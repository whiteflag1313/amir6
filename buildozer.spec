[app]

title = Amir6
package.name = amir6
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
version = 0.1

# android module needed for android.permissions on API < 29
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,openssl,certifi,pyjnius,android

orientation = portrait
fullscreen = 0

# WRITE/READ only needed for Android 9 and below
# Android 10+ uses MediaStore — no storage permission required
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.requestLegacyExternalStorage = True

android.api     = 33
android.minapi  = 21
android.ndk     = 25c
android.ndk_api = 21

# Overridden by CI matrix per job
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
