package com.heykettle.android

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * The one path every signal takes out of the phone: cap check, one attempt,
 * then the queue on failure, revoke on 403. Receivers call [send]; the worker
 * calls [flush]. Nothing else talks to the network.
 */
class Sender(
    private val context: Context,
    private val tokens: TokenStore = TokenStore(context),
    private val state: AppState = AppState(context),
    private val pinger: Pinger = HttpPinger(BuildConfig.VERSION_NAME),
    private val clock: () -> Long = System::currentTimeMillis,
) {
    /** Off the calling thread: receivers run on main. */
    fun sendAsync(signal: String) {
        executor.execute { send(signal) }
    }

    @Synchronized
    fun send(signal: String) {
        val token = tokens.token ?: return
        val now = clock()
        if (signal == Signals.DEVICE_ALIVE) {
            if (state.deviceAliveSentToday(now)) return
        } else if (!RateCap.allows(signal, state.lastSent(signal), now)) {
            return
        }
        // Cap first, so a failed attempt does not fire again on every screen-on.
        if (signal == Signals.DEVICE_ALIVE) state.markDeviceAlive(now) else state.markSent(signal, now)

        when (pinger.ping(tokens.apiBase, token, signal)) {
            PingResult.Accepted -> onAccepted(signal)
            is PingResult.Rejected -> Unit // 400: not provisioned for this key. Ignored (§3).
            PingResult.Revoked -> revoke()
            PingResult.Failed -> {
                state.queue = state.queue + Pending(signal, now)
                scheduleFlush()
            }
        }
    }

    /** Worker entry: retry everything still inside the window. */
    @Synchronized
    fun flush() {
        val token = tokens.token ?: return
        val pending = state.queue
        if (pending.isEmpty()) return
        val result = RetryQueue.flush(pending, clock()) { signal -> pinger.ping(tokens.apiBase, token, signal) }
        if (result.revoked) {
            revoke()
            return
        }
        state.queue = result.remaining
        result.accepted.forEach { onAccepted(it.signal) }
        if (result.remaining.isNotEmpty()) scheduleFlush()
    }

    private fun onAccepted(signal: String) {
        if (signal == Signals.UNLOCK && state.phase == Phase.VERIFY) {
            // Verification by prediction (§5.4 item 4): the app's own unlock
            // ping was accepted, so the token, the permission and the wiring
            // are all right at once.
            state.heardPending = true
            state.phase = Phase.ON
        }
    }

    /** §4.5: a 403 means revoked. Stop, clear, show REVOKED, never retry. */
    fun revoke() {
        KettleService.stop(context)
        HeartbeatWorker.cancel(context)
        tokens.clear()
        state.resetSignals()
        state.phase = Phase.REVOKED
    }

    private fun scheduleFlush() {
        val request = OneTimeWorkRequestBuilder<HeartbeatWorker>()
            .setInputData(workDataOf(HeartbeatWorker.INPUT_FLUSH_ONLY to true))
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 1, TimeUnit.MINUTES)
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(FLUSH_WORK, ExistingWorkPolicy.KEEP, request)
    }

    companion object {
        const val FLUSH_WORK = "kettle-flush"
        private val executor = Executors.newSingleThreadExecutor()
    }
}
