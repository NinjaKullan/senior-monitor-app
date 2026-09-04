package com.heykettle.android

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Spec 014 §8.6, the source-side half: the manifest holds exactly the §4.3
 * permissions, never a location permission, never PACKAGE_USAGE_STATS; and
 * the word "location" appears nowhere the app ships. The Gradle task
 * auditXxxManifest is the other half, over the merged manifest.
 */
class ManifestAuditTest {

    private val allowed = setOf(
        "android.permission.INTERNET",
        "android.permission.FOREGROUND_SERVICE",
        "android.permission.FOREGROUND_SERVICE_HEALTH",
        "android.permission.RECEIVE_BOOT_COMPLETED",
        "android.permission.ACTIVITY_RECOGNITION",
        "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
        "android.permission.POST_NOTIFICATIONS",
    )

    private fun declaredPermissions(): Set<String> =
        Regex("""<uses-permission[^>]*android:name="([^"]+)"""").findAll(ProjectFiles.manifest()).map { it.groupValues[1] }.toSet()

    @Test
    fun `manifest declares exactly the spec 4_3 permissions`() {
        assertEquals(allowed, declaredPermissions())
    }

    @Test
    fun `no location permission and no usage stats`() {
        val manifest = ProjectFiles.manifest()
        assertFalse(manifest.contains("PACKAGE_USAGE_STATS"))
        assertFalse(Regex("LOCATION").containsMatchIn(manifest))
        assertFalse(manifest.contains("foregroundServiceType=\"location\""))
    }

    @Test
    fun `the word location appears nowhere in shipped sources or strings`() {
        val word = Regex("\\blocation\\b", RegexOption.IGNORE_CASE)
        val offenders = ProjectFiles.mainSources().filter { word.containsMatchIn(it.readText()) }.map { it.path }
        assertEquals(emptyList<String>(), offenders)
        for ((name, value) in ProjectFiles.strings()) assertFalse("$name says location", word.containsMatchIn(value))
    }

    @Test
    fun `foreground service is typed and not exported`() {
        val manifest = ProjectFiles.manifest()
        assertTrue(manifest.contains("android:foregroundServiceType=\"health\""))
        assertTrue(Regex("""<service[^>]*android:exported="false"""", RegexOption.DOT_MATCHES_ALL).containsMatchIn(manifest))
    }

    @Test
    fun `backup is off so the token never leaves the phone`() {
        assertTrue(ProjectFiles.manifest().contains("android:allowBackup=\"false\""))
    }
}
