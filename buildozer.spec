# نسخه‌ی پایتون رو شل کن (نسخه دقیق 3.11.9 خیلی وقت‌ها مشکل‌ساز می‌شه)
requirements = python3,kivy==2.3.0,openssl,certifi

# یا اگر حتماً ۳.۱۱ می‌خوای:
# requirements = python3==3.11,kivy==2.3.0,openssl,certifi

# شاخه پایدارتر python-for-android
p4a.branch = develop
# یا اگر خواستی نسخه ثابت:
# p4a.commit = 5aa97321ebf7339edf04e707beccbf94a284f4c9

# NDK رو مشخص کن (با نسخه‌ای که روی Actions داری سازگار باشه)
android.ndk = 25c
# یا اگر نیاز به پشتیبانی ۱۶ کیلوبایتی گوگل‌پلی داری:
# android.ndk = 28c

android.api = 33
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a
