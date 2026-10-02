[app]
title = WiFi Tester Pro
package.name = wifitesterpro
package.domain = org.hero

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,ttf

version = 2.1

requirements = python3,kivy==2.3.0,pyjnius,android,plyer

orientation = portrait
fullscreen = 0

android.permissions = ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_NETWORK_STATE,CHANGE_NETWORK_STATE,INTERNET,NEARBY_WIFI_DEVICES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 29
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.accept_sdk_license = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1