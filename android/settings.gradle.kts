// Spec 014 §4: Kotlin, AndroidX and WorkManager only. No other repositories,
// no other plugins, so a dependency cannot arrive by accident.
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "kettle-android"
include(":app")
