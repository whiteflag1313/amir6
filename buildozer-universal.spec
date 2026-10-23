[app]
title = AMIR6
package.name = amir6_universal
package.domain = org.amir6
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.3
requirements = python3,kivy==2.3.0,openssl,certifi,cython==0.29.36
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# این دو خط مسیر دقیق اندروید را به بیلدوزر قفل می‌کند تا گمراه نشود
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk/25.2.9519653

fullscreen = 0
android.presplash_color = #0d0d0d

[buildozer]
log_level = 2
