package com.heykettle.android

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import androidx.core.content.ContextCompat
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * The belt (§4.2): every 15 minutes, restart the service if the OEM killed it,
 * read the step counter once, send `device_alive` once a day, flush the queue.
 * The same class runs as a one-off flush when a ping fails (input flag).
 */
class HeartbeatWorker(context: Context, params: WorkerParameters) : Worker(context, params) {

    override fun doWork(): Result {
        val ctx = applicationContext
        val tokens = TokenStore(ctx)
        val state = AppState(ctx)
        if (!tokens.hasToken || state.phase == Phase.REVOKED || state.phase == Phase.OFF) return Result.success()

        val sender = Sender(ctx)
        val flushOnly = inputData.getBoolean(INPUT_FLUSH_ONLY, false)
        if (!flushOnly) {
            KettleService.start(ctx)
            if (stepsMovedSinceLastRead(ctx, state)) sender.send(Signals.MOTION)
            sender.send(Signals.DEVICE_ALIVE)
        }
        sender.flush()
        return Result.success()
    }

    /**
     * One reading of TYPE_STEP_COUNTER, no continuous listener. The number is
     * compared to the last one and thrown away; only "did it grow" survives.
     */
    private fun stepsMovedSinceLastRead(ctx: Context, state: AppState): Boolean {
        if (Build.VERSION.SDK_INT >= 29 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACTIVITY_RECOGNITION) != PackageManager.PERMISSION_GRANTED
        ) return false
        val sm = ctx.getSystemService(SensorManager::class.java) ?: return false
        val sensor = sm.getDefaultSensor(Sensor.TYPE_STEP_COUNTER) ?: return false

        val latch = CountDownLatch(1)
        var reading = -1f
        val listener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                if (reading < 0f) {
                    reading = event.values.firstOrNull() ?: -1f
                    latch.countDown()
                }
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
        }
        val handler = Handler(Looper.getMainLooper())
        sm.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_NORMAL, handler)
        try {
            latch.await(SENSOR_WAIT_S, TimeUnit.SECONDS)
        } finally {
            sm.unregisterListener(listener)
        }
        if (reading < 0f) return false

        val last = state.lastSteps
        state.lastSteps = reading
        // The counter resets on reboot; a smaller number is a new baseline, not movement.
        return last >= 0f && reading > last
    }

    companion object {
        const val INPUT_FLUSH_ONLY = "flush_only"
        const val PERIODIC_WORK = "kettle-heartbeat"
        private const val SENSOR_WAIT_S = 5L

        fun schedule(context: Context) {
            val request = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES).build()
            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(PERIODIC_WORK, ExistingPeriodicWorkPolicy.KEEP, request)
        }

        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(PERIODIC_WORK)
            WorkManager.getInstance(context).cancelUniqueWork(Sender.FLUSH_WORK)
        }
    }
}
