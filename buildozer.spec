[app]

title = Amir6
package.name = amir6
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
version = 0.1

# هم python3 و هم hostpython3 رو به ۳.۱۱ پین کردیم
requirements = python3==3.11,hostpython3==3.11,kivy==2.3.0,openssl,certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25c
android.ndk_api = 21
android.archs = arm64-v8a

# از master استفاده کن
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
