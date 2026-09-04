package com.heykettle.android

import android.app.Activity
import android.view.View

/** Release: no token entry exists. The debug source set carries the real one. */
object DebugSetup {
    @Suppress("UNUSED_PARAMETER")
    fun install(activity: Activity, title: View, onToken: (apiBase: String, token: String) -> Unit) = Unit
}
