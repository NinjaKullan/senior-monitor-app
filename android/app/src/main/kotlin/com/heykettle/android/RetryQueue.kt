package com.heykettle.android

/**
 * The retry queue (§4.4): a ping that could not be delivered is kept, with the
 * time it was born, and tried again on each worker run. A ping older than
 * [Signals.DROP_AFTER_MS] is dropped before any attempt: the server records
 * arrival time, and a morning unlock delivered at dinner would lie about the
 * morning. Pure Kotlin so it is unit-tested without a device.
 */
data class Pending(val signal: String, val bornMs: Long)

object RetryQueue {
    private const val SEP_ENTRY = ";"
    private const val SEP_FIELD = "|"

    fun encode(items: List<Pending>): String =
        items.joinToString(SEP_ENTRY) { "${it.signal}$SEP_FIELD${it.bornMs}" }

    fun decode(raw: String?): List<Pending> {
        if (raw.isNullOrBlank()) return emptyList()
        return raw.split(SEP_ENTRY).mapNotNull { entry ->
            val parts = entry.split(SEP_FIELD)
            val born = parts.getOrNull(1)?.toLongOrNull() ?: return@mapNotNull null
            if (parts[0].isBlank()) null else Pending(parts[0], born)
        }
    }

    /** Everything still young enough to be worth sending. */
    fun prune(items: List<Pending>, nowMs: Long): List<Pending> =
        items.filter { nowMs - it.bornMs < Signals.DROP_AFTER_MS }

    /** The outcome of one flush pass. */
    data class Flush(
        val remaining: List<Pending>,
        val accepted: List<Pending>,
        val revoked: Boolean,
    )

    /**
     * Try each pending ping once, oldest first. Accepted and rejected pings
     * leave the queue; failed ones stay (still subject to the age rule next
     * time); a 403 ends the pass and tells the caller to revoke.
     */
    fun flush(items: List<Pending>, nowMs: Long, attempt: (String) -> PingResult): Flush {
        val live = prune(items, nowMs).sortedBy { it.bornMs }
        val remaining = mutableListOf<Pending>()
        val accepted = mutableListOf<Pending>()
        for (item in live) {
            when (attempt(item.signal)) {
                PingResult.Accepted -> accepted += item
                is PingResult.Rejected -> Unit
                PingResult.Failed -> remaining += item
                PingResult.Revoked -> return Flush(emptyList(), accepted, revoked = true)
            }
        }
        return Flush(remaining, accepted, revoked = false)
    }
}
