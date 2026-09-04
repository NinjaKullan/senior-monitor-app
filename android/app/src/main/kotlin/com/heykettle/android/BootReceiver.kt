package com.heykettle.android

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** §4.2: after a reboot (or an update) put the service and the worker back. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED, Intent.ACTION_MY_PACKAGE_REPLACED -> {
                val state = AppState(context)
                if (state.phase == Phase.VERIFY || state.phase == Phase.ON) {
                    HeartbeatWorker.schedule(context)
                    KettleService.start(context)
                }
            }
        }
    }
}
