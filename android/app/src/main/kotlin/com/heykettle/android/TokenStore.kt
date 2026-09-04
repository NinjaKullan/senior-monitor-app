package com.heykettle.android

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * The device token at rest (§4.5): EncryptedSharedPreferences, never
 * displayed, never logged, never exported (backup is off in the manifest).
 */
class TokenStore(context: Context) {
    private val prefs: SharedPreferences = run {
        val key = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "kettle_secure",
            key,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    val token: String? get() = prefs.getString(KEY_TOKEN, null)
    val apiBase: String get() = prefs.getString(KEY_API_BASE, null) ?: DEFAULT_API_BASE
    val hasToken: Boolean get() = !token.isNullOrBlank()

    fun set(apiBase: String, token: String) {
        prefs.edit().putString(KEY_API_BASE, apiBase.trim().trimEnd('/')).putString(KEY_TOKEN, token.trim()).apply()
    }

    fun clear() {
        prefs.edit().remove(KEY_TOKEN).apply()
    }

    companion object {
        const val DEFAULT_API_BASE = "https://kettle-api.fly.dev"
        private const val KEY_TOKEN = "token"
        private const val KEY_API_BASE = "api_base"
    }
}
