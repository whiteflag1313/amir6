[app]
title = AMIR6 (ARM7)
package.name = amir6_arm7
package.domain = org.amir6
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.4
requirements = python3,kivy==2.3.0,openssl,certifi
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = armeabi-v7a
android.allow_backup = True
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
fullscreen = 0

[buildozer]
log_level = 2
