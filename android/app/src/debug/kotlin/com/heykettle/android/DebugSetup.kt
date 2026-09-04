package com.heykettle.android

import android.app.Activity
import android.text.InputType
import android.view.View
import android.widget.EditText
import android.widget.LinearLayout
import androidx.appcompat.app.AlertDialog

/**
 * DEBUG BUILDS ONLY. The claim route (spec 014 §5.3) does not exist yet, so
 * the founder hands the token to the phone: long-press the title in
 * BEFORE_SETUP, type the api base and the token. Nothing here is parent-facing
 * and nothing here is in strings.xml; the release source set replaces this
 * file with a no-op, so a release APK does not contain it.
 */
object DebugSetup {
    fun install(activity: Activity, title: View, onToken: (apiBase: String, token: String) -> Unit) {
        title.setOnLongClickListener {
            if (AppState(activity).phase != Phase.BEFORE_SETUP) return@setOnLongClickListener false
            val apiBase = EditText(activity).apply {
                hint = "api base"
                setText(TokenStore.DEFAULT_API_BASE)
                inputType = InputType.TYPE_TEXT_VARIATION_URI
            }
            val token = EditText(activity).apply {
                hint = "device token"
                inputType = InputType.TYPE_TEXT_VARIATION_PASSWORD or InputType.TYPE_CLASS_TEXT
            }
            val box = LinearLayout(activity).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(48, 24, 48, 0)
                addView(apiBase)
                addView(token)
            }
            AlertDialog.Builder(activity)
                .setTitle("Debug: enter token")
                .setView(box)
                .setPositiveButton("Connect") { _, _ ->
                    val t = token.text.toString().trim()
                    val b = apiBase.text.toString().trim()
                    if (t.isNotEmpty() && b.startsWith("https://")) onToken(b, t)
                }
                .setNegativeButton("Cancel", null)
                .show()
            true
        }
    }
}
