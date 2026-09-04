package com.heykettle.android

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RetryQueueTest {
    private val minute = 60_000L

    @Test
    fun `a ping older than 60 minutes is dropped before any attempt`() {
        val items = listOf(Pending("routine", 0L), Pending("charger", 30 * minute))
        val tried = mutableListOf<String>()
        val result = RetryQueue.flush(items, 61 * minute) { tried += it; PingResult.Accepted }
        assertEquals(listOf("charger"), tried)
        assertEquals(emptyList<Pending>(), result.remaining)
    }

    @Test
    fun `at exactly 60 minutes the ping is dropped - late is late`() {
        val result = RetryQueue.flush(listOf(Pending("routine", 0L)), 60 * minute) { PingResult.Accepted }
        assertEquals(emptyList<Pending>(), result.accepted)
    }

    @Test
    fun `failed pings stay, accepted and rejected leave`() {
        val items = listOf(Pending("routine", 0L), Pending("motion", 1L), Pending("charger", 2L))
        val result = RetryQueue.flush(items, 5 * minute) {
            when (it) {
                "routine" -> PingResult.Failed
                "motion" -> PingResult.Rejected(400)
                else -> PingResult.Accepted
            }
        }
        assertEquals(listOf(Pending("routine", 0L)), result.remaining)
        assertEquals(listOf(Pending("charger", 2L)), result.accepted)
        assertFalse(result.revoked)
    }

    @Test
    fun `a 403 empties the queue and reports revoked`() {
        val items = listOf(Pending("routine", 0L), Pending("charger", 1L))
        var attempts = 0
        val result = RetryQueue.flush(items, minute) { attempts++; PingResult.Revoked }
        assertTrue(result.revoked)
        assertEquals(emptyList<Pending>(), result.remaining)
        assertEquals(1, attempts)
    }

    @Test
    fun `encode and decode round-trip`() {
        val items = listOf(Pending("routine", 123L), Pending("device_alive", 456L))
        assertEquals(items, RetryQueue.decode(RetryQueue.encode(items)))
        assertEquals(emptyList<Pending>(), RetryQueue.decode(null))
        assertEquals(emptyList<Pending>(), RetryQueue.decode(""))
    }

    @Test
    fun `http codes classify as the spec says`() {
        assertEquals(PingResult.Accepted, HttpPinger.classify(200))
        assertEquals(PingResult.Revoked, HttpPinger.classify(403))
        assertEquals(PingResult.Rejected(400), HttpPinger.classify(400))
        assertEquals(PingResult.Failed, HttpPinger.classify(502))
        assertEquals(PingResult.Failed, HttpPinger.classify(-1))
    }
}
