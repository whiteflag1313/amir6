[app]
title = AMIR6
package.name = amir6
package.domain = org.amir6
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,openssl,certifi
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25.2.9519653
android.archs = arm64-v8a
android.allow_backup = True
fullscreen = 0
android.presplash_color = #0d0d0d

# معرفی دقیق مسیرها برای جلوگیری از جستجوی اشتباه توسط بیلدوزر
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.skip_update = True

[buildozer]
log_level = 2
