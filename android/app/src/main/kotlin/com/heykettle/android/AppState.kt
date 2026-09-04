package com.heykettle.android

import android.content.Context
import android.content.SharedPreferences
import java.time.LocalDate
import java.time.ZoneId

/** The one screen's states (§5.4). HEARD is ON seen for the first time. */
enum class Phase { BEFORE_SETUP, CONNECTING, PERMISSIONS, VERIFY, ON, REVOKED, OFF }

/**
 * Everything the app remembers that is not the token: which state the screen
 * is in, when each signal last went out, the retry queue, the last step-counter
 * reading. Plain SharedPreferences; nothing here identifies anyone.
 */
class AppState(context: Context) {
    val prefs: SharedPreferences = context.getSharedPreferences("kettle_state", Context.MODE_PRIVATE)

    var phase: Phase
        get() = runCatching { Phase.valueOf(prefs.getString(KEY_PHASE, null) ?: "") }.getOrDefault(Phase.BEFORE_SETUP)
        set(value) = prefs.edit().putString(KEY_PHASE, value.name).apply()

    /** Set when VERIFY flips to ON; the activity shows HEARD once, then clears it. */
    var heardPending: Boolean
        get() = prefs.getBoolean(KEY_HEARD_PENDING, false)
        set(value) = prefs.edit().putBoolean(KEY_HEARD_PENDING, value).apply()

    fun lastSent(signal: String): Long = prefs.getLong("last_$signal", 0L)
    fun markSent(signal: String, nowMs: Long) = prefs.edit().putLong("last_$signal", nowMs).apply()

    /** device_alive: one per local calendar day (§3). */
    fun deviceAliveSentToday(nowMs: Long): Boolean = prefs.getString(KEY_ALIVE_DAY, null) == localDay(nowMs)
    fun markDeviceAlive(nowMs: Long) = prefs.edit().putString(KEY_ALIVE_DAY, localDay(nowMs)).apply()

    /** Last step-counter reading. Compared and discarded; never sent (§7). */
    var lastSteps: Float
        get() = prefs.getFloat(KEY_LAST_STEPS, -1f)
        set(value) = prefs.edit().putFloat(KEY_LAST_STEPS, value).apply()

    var queue: List<Pending>
        get() = RetryQueue.decode(prefs.getString(KEY_QUEUE, null))
        set(value) = prefs.edit().putString(KEY_QUEUE, RetryQueue.encode(value)).apply()

    /** Forget the send history and the queue; used by the kill switch and by revoke. */
    fun resetSignals() {
        prefs.edit()
            .remove(KEY_QUEUE).remove(KEY_ALIVE_DAY).remove(KEY_LAST_STEPS).remove(KEY_HEARD_PENDING)
            .remove("last_${Signals.UNLOCK}").remove("last_${Signals.CHARGER}").remove("last_${Signals.MOTION}")
            .apply()
    }

    companion object {
        const val KEY_PHASE = "phase"
        const val KEY_HEARD_PENDING = "heard_pending"
        private const val KEY_ALIVE_DAY = "alive_day"
        private const val KEY_LAST_STEPS = "last_steps"
        private const val KEY_QUEUE = "queue"

        fun localDay(nowMs: Long): String =
            java.time.Instant.ofEpochMilli(nowMs).atZone(ZoneId.systemDefault()).toLocalDate().let(LocalDate::toString)
    }
}
