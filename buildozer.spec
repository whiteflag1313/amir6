[app]
title = AMIR6
package.name = amir6
package.domain = org.amir6
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,openssl
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
fullscreen = 0
android.presplash_color = #0d0d0d

[buildozer]
log_level = 2