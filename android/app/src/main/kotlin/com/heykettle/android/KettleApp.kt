package com.heykettle.android

import android.app.Application

class KettleApp : Application() {
    override fun onCreate() {
        super.onCreate()
        KettleService.ensureChannel(this)
        // The worker is idempotent to schedule; if the phone is connected,
        // every process start is another chance to have the belt on.
        val phase = AppState(this).phase
        if (phase == Phase.VERIFY || phase == Phase.ON) HeartbeatWorker.schedule(this)
    }
}
