[app]

title = AMIR6
package.name = amir6
package.domain = org.amir6

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.3

requirements = python3,kivy==2.2.1,openssl,plyer

orientation = portrait

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

android.accept_sdk_license = True

fullscreen = 0

[buildozer]

log_level = 2
