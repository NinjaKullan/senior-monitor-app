package com.heykettle.android

import android.Manifest
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

/**
 * The one screen (§5.4). It renders whatever [AppState.phase] says and moves
 * the phase along on the kid's taps. The parent, if they ever open it after
 * setup, sees only ON and the small kill switch.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var state: AppState
    private lateinit var tokens: TokenStore
    private lateinit var title: TextView
    private lateinit var spinner: ProgressBar
    private lateinit var line: TextView
    private lateinit var line2: TextView
    private lateinit var button: Button
    private lateinit var button2: Button
    private lateinit var offLink: TextView

    private var batteryDialogLaunched = false

    private val prefsListener = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key == AppState.KEY_PHASE || key == AppState.KEY_HEARD_PENDING) runOnUiThread { render() }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        state = AppState(this)
        tokens = TokenStore(this)
        title = findViewById(R.id.title)
        spinner = findViewById(R.id.spinner)
        line = findViewById(R.id.line)
        line2 = findViewById(R.id.line2)
        button = findViewById(R.id.button)
        button2 = findViewById(R.id.button2)
        offLink = findViewById(R.id.off_link)

        // Debug builds only: long-press the title in BEFORE_SETUP to type the
        // token in. Release compiles the empty DebugSetup instead.
        DebugSetup.install(this, title) { apiBase, token -> onTokenEntered(apiBase, token) }
    }

    override fun onResume() {
        super.onResume()
        state.prefs.registerOnSharedPreferenceChangeListener(prefsListener)
        if (batteryDialogLaunched) {
            // Back from the battery dialog: the permission step is done however it went.
            batteryDialogLaunched = false
            enterVerify()
        }
        render()
    }

    override fun onPause() {
        state.prefs.unregisterOnSharedPreferenceChangeListener(prefsListener)
        super.onPause()
    }

    override fun onStop() {
        // HEARD is shown once; from now on the steady state reads ON.
        if (state.phase == Phase.ON && state.heardPending) state.heardPending = false
        super.onStop()
    }

    // ---- rendering -------------------------------------------------------

    private fun render() {
        spinner.visibility = View.GONE
        line2.visibility = View.GONE
        button.visibility = View.GONE
        button2.visibility = View.GONE
        offLink.visibility = View.GONE
        button.setOnClickListener(null)
        button2.setOnClickListener(null)

        when (state.phase) {
            Phase.BEFORE_SETUP -> line.setText(R.string.before_setup)
            Phase.CONNECTING -> {
                spinner.visibility = View.VISIBLE
                line.setText(R.string.connecting)
            }
            Phase.PERMISSIONS -> {
                line.setText(R.string.permissions)
                line2.text = getString(R.string.rationale_motion) + "\n\n" + getString(R.string.rationale_battery)
                line2.visibility = View.VISIBLE
                show(button, R.string.permissions_button) { requestPermissionsInSequence() }
                if (OemSettings.isKnownOem()) {
                    line2.text = line2.text.toString() + "\n\n" + getString(R.string.oem_setting)
                    show(button2, R.string.oem_setting_button) { openOemPage() }
                }
            }
            Phase.VERIFY -> line.setText(R.string.verify)
            Phase.ON -> {
                line.setText(if (state.heardPending) R.string.heard else R.string.on)
                offLink.setText(R.string.off_link)
                offLink.visibility = View.VISIBLE
                offLink.setOnClickListener { confirmOff() }
            }
            Phase.REVOKED -> line.setText(R.string.revoked)
            Phase.OFF -> {
                line.setText(R.string.off)
                line2.setText(R.string.off_note)
                line2.visibility = View.VISIBLE
                show(button, R.string.off_button) { state.phase = Phase.BEFORE_SETUP }
            }
        }
    }

    private fun show(b: Button, text: Int, onClick: () -> Unit) {
        b.setText(text)
        b.visibility = View.VISIBLE
        b.setOnClickListener { onClick() }
    }

    // ---- transitions -----------------------------------------------------

    /** Token in hand (today: typed in a debug build; later: the claim route, §5.3). */
    private fun onTokenEntered(apiBase: String, token: String) {
        tokens.set(apiBase, token)
        state.resetSignals()
        state.phase = Phase.CONNECTING
        Handler(Looper.getMainLooper()).postDelayed({ if (state.phase == Phase.CONNECTING) state.phase = Phase.PERMISSIONS }, 600)
    }

    /** §5.4 item 3: activity recognition, notifications, then the battery dialog. */
    private fun requestPermissionsInSequence() {
        val wanted = mutableListOf<String>()
        if (Build.VERSION.SDK_INT >= 29 && !granted(Manifest.permission.ACTIVITY_RECOGNITION)) wanted += Manifest.permission.ACTIVITY_RECOGNITION
        if (Build.VERSION.SDK_INT >= 33 && !granted(Manifest.permission.POST_NOTIFICATIONS)) wanted += Manifest.permission.POST_NOTIFICATIONS
        if (wanted.isEmpty()) requestBatteryExemption() else requestPermissions(wanted.toTypedArray(), REQ_PERMS)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_PERMS) requestBatteryExemption()
    }

    private fun requestBatteryExemption() {
        val pm = getSystemService(PowerManager::class.java)
        if (pm != null && pm.isIgnoringBatteryOptimizations(packageName)) {
            enterVerify()
            return
        }
        val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
        if (intent.resolveActivity(packageManager) != null) {
            batteryDialogLaunched = true
            startActivity(intent)
        } else {
            enterVerify()
        }
    }

    private fun enterVerify() {
        if (state.phase != Phase.PERMISSIONS) return
        state.phase = Phase.VERIFY
        HeartbeatWorker.schedule(this)
        KettleService.start(this)
    }

    private fun openOemPage() {
        runCatching { startActivity(OemSettings.intentFor(this)) }
            .onFailure { runCatching { startActivity(OemSettings.appSettings(this)) } }
    }

    /** §8.5: the kill switch always needs a confirm. */
    private fun confirmOff() {
        AlertDialog.Builder(this)
            .setMessage(R.string.off_confirm)
            .setPositiveButton(R.string.off_confirm_yes) { _, _ -> turnOff() }
            .setNegativeButton(R.string.off_confirm_no, null)
            .show()
    }

    private fun turnOff() {
        KettleService.stop(this)
        HeartbeatWorker.cancel(this)
        tokens.clear()
        state.resetSignals()
        state.phase = Phase.OFF
    }

    private fun granted(permission: String): Boolean =
        ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED

    companion object {
        private const val REQ_PERMS = 41
    }
}
