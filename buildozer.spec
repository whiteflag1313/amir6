[app]

# عنوان برنامه
title = Amir6

# نام پکیج
package.name = amir6

# دامنه پکیج
package.domain = org.test

# مسیر سورس
source.dir = .

# پسوند فایل‌هایی که باید داخل APK باشن
source.include_exts = py,png,jpg,kv,atlas,json,xml

# نسخه برنامه
version = 0.1

# نیازمندی‌ها
requirements = python3==3.11,kivy==2.3.0,openssl,certifi

# جهت صفحه
orientation = portrait

# تمام‌صفحه نباشد
fullscreen = 0

# مجوزها
android.permissions = INTERNET

# تنظیمات اندروید
android.api = 33
android.minapi = 21
android.ndk = 25c
android.ndk_api = 21
android.archs = arm64-v8a

# شاخه python-for-android (پایدارتر)
p4a.branch = master

[buildozer]

# سطح لاگ
log_level = 2

# هشدار root
warn_on_root = 1
