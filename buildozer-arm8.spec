[app]
title = AMIR6
package.name = amir6_v8
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
android.archs = arm64-v8a
android.allow_backup = True
fullscreen = 0
android.presplash_color = #0d0d0d

[buildozer]
log_level = 2
