package com.heykettle.android

import android.app.KeyguardManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat

/**
 * The live process (§4.1). Since Android 8 the charger and unlock broadcasts
 * only reach a receiver registered at runtime, so something has to stay
 * alive to hold one. This is it. Its notification is the price: one line,
 * silent, MIN importance, no buttons.
 */
class KettleService : Service() {

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val sender = Sender(context)
            when (intent.action) {
                Intent.ACTION_USER_PRESENT -> sender.sendAsync(Signals.UNLOCK)
                Intent.ACTION_SCREEN_ON -> {
                    // §3: a phone with no lock screen never fires USER_PRESENT.
                    // If the keyguard is not up when the screen comes on, the
                    // screen coming on is the unlock.
                    val km = context.getSystemService(KeyguardManager::class.java)
                    if (km != null && !km.isKeyguardLocked) sender.sendAsync(Signals.UNLOCK)
                }
                Intent.ACTION_POWER_CONNECTED, Intent.ACTION_POWER_DISCONNECTED ->
                    sender.sendAsync(Signals.CHARGER)
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        ensureChannel(this)
        val type = if (Build.VERSION.SDK_INT >= 34) ServiceInfo.FOREGROUND_SERVICE_TYPE_HEALTH else 0
        ServiceCompat.startForeground(this, NOTIFICATION_ID, notification(this), type)
        registerReceiver(
            receiver,
            IntentFilter().apply {
                addAction(Intent.ACTION_USER_PRESENT)
                addAction(Intent.ACTION_SCREEN_ON)
                addAction(Intent.ACTION_POWER_CONNECTED)
                addAction(Intent.ACTION_POWER_DISCONNECTED)
            },
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onDestroy() {
        runCatching { unregisterReceiver(receiver) }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        const val CHANNEL_ID = "kettle"
        const val NOTIFICATION_ID = 1

        /** Start if there is a token. Safe to call from anywhere; swallows the OEM's refusals. */
        fun start(context: Context): Boolean {
            if (!TokenStore(context).hasToken) return false
            return runCatching {
                ContextCompat.startForegroundService(context, Intent(context, KettleService::class.java))
                true
            }.getOrDefault(false)
        }

        fun stop(context: Context) {
            runCatching { context.stopService(Intent(context, KettleService::class.java)) }
        }

        fun ensureChannel(context: Context) {
            val nm = context.getSystemService(NotificationManager::class.java) ?: return
            if (nm.getNotificationChannel(CHANNEL_ID) != null) return
            val channel = NotificationChannel(CHANNEL_ID, context.getString(R.string.app_name), NotificationManager.IMPORTANCE_MIN).apply {
                setSound(null, null)
                enableVibration(false)
                enableLights(false)
                setShowBadge(false)
            }
            nm.createNotificationChannel(channel)
        }

        fun notification(context: Context): Notification =
            NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(context.getString(R.string.notification))
                .setOngoing(true)
                .setSilent(true)
                .setShowWhen(false)
                .setPriority(NotificationCompat.PRIORITY_MIN)
                .setCategory(NotificationCompat.CATEGORY_SERVICE)
                .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
                .build()
    }
}
