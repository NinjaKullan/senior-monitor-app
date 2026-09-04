package com.heykettle.android

import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory

/**
 * Pins every parent-facing string to DECISIONS 257, verbatim, and pins the
 * set: no string may be added or removed without a new DECISIONS entry.
 */
class StringsTest {

    private val expected = linkedMapOf(
        "app_name" to "Kettle",
        "notification" to "Kettle is on",
        "before_setup" to "Ask your family to send you the Kettle setup link, then open it on this phone.",
        "connecting" to "Connecting this phone to Kettle.",
        "permissions" to "Your phone will ask two questions. Tap Allow on both.",
        "permissions_button" to "Continue",
        "rationale_motion" to "Kettle only notices that the phone moved today. It never knows where you are.",
        "rationale_battery" to "This lets Kettle keep working every day.",
        "oem_setting" to "One more setting so this phone does not switch Kettle off.",
        "oem_setting_button" to "Show me",
        "verify" to "Turn the screen off, then unlock the phone the way you usually do.",
        "heard" to "Kettle heard it. This phone is connected. You can close this.",
        "on" to "Kettle is on. There is nothing you need to do.",
        "off_link" to "Turn Kettle off",
        "off_confirm" to "Turn Kettle off on this phone? Your family will stop hearing that your day has started.",
        "off_confirm_yes" to "Turn off",
        "off_confirm_no" to "Keep on",
        "off" to "Kettle is off on this phone.",
        "off_button" to "Reconnect",
        "off_note" to "Ask your family for a new setup link.",
        "revoked" to "Your family has turned Kettle off on this phone.",
    )

    @Test
    fun `every string is exactly DECISIONS 257 and nothing else exists`() {
        assertEquals(expected, ProjectFiles.strings())
    }

    @Test
    fun `copy laws hold - straight apostrophes, no em dashes, no we`() {
        for ((name, value) in ProjectFiles.strings()) {
            assert(!value.contains('’') && !value.contains('‘')) { "$name: curly apostrophe" }
            assert(!value.contains('—')) { "$name: em dash" }
            assert(!Regex("\\bwe\\b", RegexOption.IGNORE_CASE).containsMatchIn(value)) { "$name: 'we'" }
        }
    }

    @Test
    fun `only one strings file exists - no translations, no extra values files with strings`() {
        val res = File(ProjectFiles.root, "src/main/res")
        val stringFiles = res.walkTopDown().filter { it.isFile && it.name == "strings.xml" }.toList()
        assertEquals(listOf(File(res, "values/strings.xml")), stringFiles)
        val otherStrings = res.walkTopDown()
            .filter { it.isFile && it.extension == "xml" && it.parentFile.name.startsWith("values") && it.name != "strings.xml" }
            .filter { it.readText().contains("<string ") }
            .toList()
        assertEquals(emptyList<File>(), otherStrings)
    }
}

/** Reads the project's own source files; the Gradle test task passes the dir in. */
object ProjectFiles {
    val root: File = File(System.getProperty("kettle.projectDir") ?: File("").absolutePath)

    fun strings(): Map<String, String> {
        val doc = DocumentBuilderFactory.newInstance().newDocumentBuilder()
            .parse(File(root, "src/main/res/values/strings.xml"))
        val nodes = doc.getElementsByTagName("string")
        val out = linkedMapOf<String, String>()
        for (i in 0 until nodes.length) {
            val node = nodes.item(i)
            out[node.attributes.getNamedItem("name").nodeValue] = node.textContent
        }
        return out
    }

    fun manifest(): String = File(root, "src/main/AndroidManifest.xml").readText()

    fun mainSources(): List<File> =
        File(root, "src/main").walkTopDown().filter { it.isFile && (it.extension == "kt" || it.extension == "xml") }.toList()
}
