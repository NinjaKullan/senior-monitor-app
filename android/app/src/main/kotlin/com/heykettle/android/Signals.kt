package com.heykettle.android

/**
 * The Android vocabulary (spec 014 §3) and its app-side caps.
 *
 * Only the key and the fact of the event ever leave the phone: a ping is
 * `GET {api_base}/p/{token}/{signal}` with no body (§4.4). Never a count.
 */
object Signals {
    /**
     * Spec 014 §3 names this key `unlock`. The server vocabulary does not have
     * it yet (spec 014 §9.1, the PM session's lane), so during the soak the
     * app sends `routine`, which is already alarm-grade and provisioned for the
     * rehearsal parent. Flip this one constant to "unlock" when §6 item 1 lands.
     */
    const val UNLOCK = "routine"
    const val CHARGER = "charger"
    const val MOTION = "motion"
    const val DEVICE_ALIVE = "device_alive"

    /** App-side caps from the §3 table, in milliseconds. */
    const val UNLOCK_CAP_MS = 30L * 60_000
    const val CHARGER_CAP_MS = 60_000L
    const val MOTION_CAP_MS = 60L * 60_000

    /** §4.4: a ping older than this is dropped, never replayed. */
    const val DROP_AFTER_MS = 60L * 60_000

    fun capFor(signal: String): Long = when (signal) {
        UNLOCK -> UNLOCK_CAP_MS
        CHARGER -> CHARGER_CAP_MS
        MOTION -> MOTION_CAP_MS
        else -> 0L // device_alive is capped by calendar day, not a window.
    }
}
