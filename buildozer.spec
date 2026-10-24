[app]

title = Amir6
package.name = amir6
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
version = 0.1

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,openssl,certifi,pyjnius,android

orientation = portrait
fullscreen = 0

# Permissions — MANAGE_EXTERNAL_STORAGE is the key for Android 11+
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# Keep legacy mode for Android 10; 11+ uses MANAGE_EXTERNAL_STORAGE
android.requestLegacyExternalStorage = True

android.api    = 33
android.minapi = 21
android.ndk    = 25c
android.ndk_api = 21

# Default arch — overridden by CI matrix
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
