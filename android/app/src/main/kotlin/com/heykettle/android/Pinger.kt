package com.heykettle.android

import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/** What the server said to one ping. */
sealed class PingResult {
    /** 2xx: recorded. */
    object Accepted : PingResult()

    /** 403: the token is revoked (§4.5). Stop everything, clear the token. */
    object Revoked : PingResult()

    /** Any other 4xx, notably 400 for a key the parent is not provisioned for. Ignored, never retried. */
    data class Rejected(val code: Int) : PingResult()

    /** No answer, or a 5xx. Worth retrying inside the 60-minute window. */
    object Failed : PingResult()
}

fun interface Pinger {
    fun ping(apiBase: String, token: String, signal: String): PingResult
}

/**
 * One HTTPS GET, no body, one header (§4.4). The platform's own
 * HttpURLConnection; no third-party network library.
 */
class HttpPinger(private val versionName: String) : Pinger {
    override fun ping(apiBase: String, token: String, signal: String): PingResult {
        val url = URL("${apiBase.trimEnd('/')}/p/$token/$signal")
        var conn: HttpURLConnection? = null
        return try {
            conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 10_000
                readTimeout = 10_000
                instanceFollowRedirects = false
                useCaches = false
                setRequestProperty("User-Agent", "kettle-android/$versionName")
            }
            classify(conn.responseCode)
        } catch (e: IOException) {
            PingResult.Failed
        } finally {
            conn?.disconnect()
        }
    }

    companion object {
        fun classify(code: Int): PingResult = when {
            code in 200..299 -> PingResult.Accepted
            code == 403 -> PingResult.Revoked
            code in 400..499 -> PingResult.Rejected(code)
            else -> PingResult.Failed
        }
    }
}
