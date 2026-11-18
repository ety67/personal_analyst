plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android { namespace = "ru.advisor.maxai"; compileSdk = 35
 defaultConfig { applicationId = "ru.advisor.maxai"; minSdk = 29; targetSdk = 35; versionCode = 3; versionName = "0.3-lite" }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
 kotlinOptions { jvmTarget = "17" }
}
