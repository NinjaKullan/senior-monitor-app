import java.io.File

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Spec 014 §4.4: the User-Agent is kettle-android/{version}. One place.
val kettleVersionName = "0.1.0"

android {
    namespace = "com.heykettle.android"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.heykettle.android"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = kettleVersionName
    }

    buildTypes {
        debug {
            // Debug-only token entry (spec 014 §6 preamble): the claim route does
            // not exist yet, so the founder types the token in by hand. That code
            // lives in src/debug only; release compiles the empty counterpart in
            // src/release/.../DebugSetup.kt instead.
            applicationIdSuffix = ".debug"
        }
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    sourceSets {
        getByName("main").kotlin.srcDirs("src/main/kotlin")
        getByName("debug").kotlin.srcDirs("src/debug/kotlin")
        getByName("release").kotlin.srcDirs("src/release/kotlin")
        getByName("test").kotlin.srcDirs("src/test/kotlin")
    }

    buildFeatures { buildConfig = true }

    testOptions {
        unitTests.all { it.systemProperty("kettle.projectDir", projectDir.absolutePath) }
    }
}

// Spec 014 §4: AndroidX and WorkManager only. Nothing else may be added
// without a DECISIONS entry.
dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.work:work-runtime-ktx:2.10.1")
    // Token at rest (spec 014 §4.5): EncryptedSharedPreferences.
    implementation("androidx.security:security-crypto:1.1.0")

    testImplementation("junit:junit:4.13.2")
}

// ---------------------------------------------------------------------------
// Manifest audit (spec 014 §8.6). The unit test in src/test audits the source
// manifest and strings; this task audits the *merged* manifest, which is what
// the phone actually sees after every library has contributed its slice. It
// is wired into `check`, so `./gradlew check` fails if any library ever
// smuggles in a location permission or PACKAGE_USAGE_STATS.
// ---------------------------------------------------------------------------
val forbiddenManifestTokens = listOf(
    "PACKAGE_USAGE_STATS",
    "ACCESS_FINE_LOCATION",
    "ACCESS_COARSE_LOCATION",
    "ACCESS_BACKGROUND_LOCATION",
    "ACCESS_MEDIA_LOCATION",
    "FOREGROUND_SERVICE_LOCATION",
    "foregroundServiceType=\"location\"",
)

androidComponents {
    onVariants { variant ->
        val name = variant.name.replaceFirstChar { it.uppercase() }
        val audit = tasks.register("audit${name}Manifest") {
            group = "verification"
            description = "Fails if the merged $name manifest carries a location permission or PACKAGE_USAGE_STATS."
            dependsOn("process${name}Manifest")
            doLast {
                val intermediates = layout.buildDirectory.get().asFile.resolve("intermediates")
                val merged = fileTree(intermediates) {
                    include("**/merged_manifest*/${variant.name}/**/AndroidManifest.xml")
                }.files.firstOrNull()
                    ?: throw GradleException("merged manifest for ${variant.name} not found under $intermediates")
                val text = merged.readText()
                val hits = forbiddenManifestTokens.filter { text.contains(it) }
                if (hits.isNotEmpty()) {
                    throw GradleException("Merged ${variant.name} manifest violates spec 014 §8.6: $hits (${merged.path})")
                }
                if (Regex("""android:name="[^"]*\.permission\.[^"]*LOCATION[^"]*"""").containsMatchIn(text)) {
                    throw GradleException("Merged ${variant.name} manifest requests a location permission (spec 014 §8.6)")
                }
                logger.lifecycle("Manifest audit passed for ${variant.name}: ${merged.path}")
            }
        }
        tasks.named("check") { dependsOn(audit) }
    }
}
