
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

android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.build_tools_version = 33.0.2

android.accept_sdk_license = True
android.skip_update = True

fullscreen = 0

[buildozer]

log_level = 2
