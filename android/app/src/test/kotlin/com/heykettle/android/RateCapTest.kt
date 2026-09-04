package com.heykettle.android

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RateCapTest {
    private val minute = 60_000L

    @Test
    fun `unlock is one per 30 minutes`() {
        assertTrue(RateCap.allows(Signals.UNLOCK, 0L, 0L))
        assertFalse(RateCap.allows(Signals.UNLOCK, 10 * minute, 39 * minute))
        assertTrue(RateCap.allows(Signals.UNLOCK, 10 * minute, 40 * minute))
    }

    @Test
    fun `charger is one per 60 seconds`() {
        assertFalse(RateCap.allows(Signals.CHARGER, 1000L, 50_000L))
        assertTrue(RateCap.allows(Signals.CHARGER, 1000L, 61_000L))
    }

    @Test
    fun `motion is one per 60 minutes`() {
        assertFalse(RateCap.allows(Signals.MOTION, minute, 59 * minute))
        assertTrue(RateCap.allows(Signals.MOTION, minute, 61 * minute))
    }

    @Test
    fun `device_alive is not window-capped here - it is once per local day`() {
        assertTrue(RateCap.allows(Signals.DEVICE_ALIVE, 1L, 2L))
    }

    @Test
    fun `unlock goes out as routine until the vocabulary has unlock - spec 014 s9_1`() {
        assertEquals("routine", Signals.UNLOCK)
    }
}
