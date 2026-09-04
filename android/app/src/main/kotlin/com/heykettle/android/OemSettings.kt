package com.heykettle.android

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings

/**
 * Where each OEM hides the switch that kills background apps (§5.4 item 3).
 * "Show me" opens the first one that resolves on this phone; if none does,
 * the app's own settings page, which has the battery section on every OEM.
 *
 * Guidance text per OEM is deliberately absent: DECISIONS 257 fixes the
 * strings and says the per-OEM lines are written from the soak test, each one
 * DECISIONS-recorded when written. Until then the OEM_SETTING line is the
 * guidance.
 */
object OemSettings {

    private data class Entry(val manufacturer: Regex, val pkg: String, val cls: String)

    private val table = listOf(
        // Xiaomi, Redmi, POCO: MIUI / HyperOS autostart, then the battery saver's per-app page.
        Entry(Regex("xiaomi|redmi|poco", RegexOption.IGNORE_CASE), "com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
        Entry(Regex("xiaomi|redmi|poco", RegexOption.IGNORE_CASE), "com.miui.powerkeeper", "com.miui.powerkeeper.ui.HiddenAppsConfigActivity"),
        // Samsung: Device care's battery page (older and newer package names).
        Entry(Regex("samsung", RegexOption.IGNORE_CASE), "com.samsung.android.lool", "com.samsung.android.sm.battery.ui.BatteryActivity"),
        Entry(Regex("samsung", RegexOption.IGNORE_CASE), "com.samsung.android.lool", "com.samsung.android.sm.ui.battery.BatteryActivity"),
        Entry(Regex("samsung", RegexOption.IGNORE_CASE), "com.samsung.android.sm_cn", "com.samsung.android.sm.ui.battery.BatteryActivity"),
        // Oppo and Realme (ColorOS): startup manager.
        Entry(Regex("oppo|realme", RegexOption.IGNORE_CASE), "com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"),
        Entry(Regex("oppo|realme", RegexOption.IGNORE_CASE), "com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity"),
        Entry(Regex("oppo|realme", RegexOption.IGNORE_CASE), "com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity"),
        // OnePlus: chain launch (autostart) list.
        Entry(Regex("oneplus", RegexOption.IGNORE_CASE), "com.oneplus.security", "com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity"),
        // Vivo and iQOO: background startup manager.
        Entry(Regex("vivo|iqoo", RegexOption.IGNORE_CASE), "com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"),
        Entry(Regex("vivo|iqoo", RegexOption.IGNORE_CASE), "com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"),
        // Huawei and Honor: app launch management.
        Entry(Regex("huawei|honor", RegexOption.IGNORE_CASE), "com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
        Entry(Regex("huawei|honor", RegexOption.IGNORE_CASE), "com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity"),
    )

    /** True if this phone is one of the OEMs the table knows about. */
    fun isKnownOem(manufacturer: String = Build.MANUFACTURER): Boolean =
        table.any { it.manufacturer.containsMatchIn(manufacturer) }

    /** The first table intent that resolves here, or the app's own settings page. */
    fun intentFor(context: Context, manufacturer: String = Build.MANUFACTURER): Intent {
        val pm = context.packageManager
        for (entry in table) {
            if (!entry.manufacturer.containsMatchIn(manufacturer)) continue
            val intent = Intent().apply {
                component = ComponentName(entry.pkg, entry.cls)
                putExtra("package_name", context.packageName)
                putExtra("package_label", context.getString(R.string.app_name))
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            if (pm.resolveActivity(intent, 0) != null) return intent
        }
        return appSettings(context)
    }

    fun appSettings(context: Context): Intent =
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

    /** Packages the manifest must declare in <queries> for resolveActivity to see them (Android 11+). */
    val queriedPackages: List<String> get() = table.map { it.pkg }.distinct()
}
