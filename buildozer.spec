[app]

title = Amir6
package.name = amir6
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
version = 0.2

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,openssl,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25c
android.ndk_api = 21
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
