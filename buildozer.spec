[app]
title = AMIR6
package.name = amir6
package.domain = org.amir6
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.2
requirements = python3,kivy==2.2.1,openssl
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
fullscreen = 0
android.presplash_color = #0d0d0d
android.sdk_path = /usr/local/lib/android/sdk
android.build_tools_version = 33.0.2

[buildozer]
log_level = 2
warn_on_root = 1
