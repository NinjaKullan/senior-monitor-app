package com.heykettle.android

/** The app-side caps from the §3 table, as a pure decision. */
object RateCap {
    /** True if a ping for [signal] may go out now given when the last one went. */
    fun allows(signal: String, lastSentMs: Long, nowMs: Long): Boolean {
        val cap = Signals.capFor(signal)
        if (cap == 0L) return true
        if (lastSentMs <= 0L) return true
        return nowMs - lastSentMs >= cap
    }
}
