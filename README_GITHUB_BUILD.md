# WiFi Tester Pro — GitHub APK Build

## مهم
هذه النسخة مخصصة لإصلاح **مشاكل التحويل والبناء فقط**.

لم يتم تغيير:
- `wifi_auto.py`
- `buildozer.spec`
- `passwords.txt`
- إعدادات التطبيق أو الواجهة أو منطق التطبيق

### التغييرات الخاصة بالبناء فقط
1. تمت إضافة `main.py` كنقطة دخول لـ Buildozer، ويستدعي `wifi_auto.py` الأصلي.
2. تمت إعادة كتابة GitHub Actions ليستخدم بيئة Ubuntu 22.04 مباشرة بدل Action غير موجودة/غير موثوقة.
3. تمت إضافة حزم البناء المطلوبة مثل `autoconf`, `automake`, `libtool`, `libltdl-dev`, `autopoint` و`gettext` لمعالجة أخطاء Autoconf/Libtool.
4. تم تثبيت Python 3.10 وBuildozer 1.5.0 وCython 0.29.34 في بيئة البناء.
5. يتم رفع أي APK موجود في `bin/*.apk` كـ Artifact باسم `WiFiTesterPro-debug-apk`.

## طريقة الاستخدام

1. ارفع محتويات هذا المجلد إلى Repository في GitHub.
2. افتح تبويب **Actions**.
3. اختر **Build Android APK**.
4. اضغط **Run workflow**.
5. انتظر انتهاء المهمة.
6. عند نجاحها افتح **Artifacts** وحمّل `WiFiTesterPro-debug-apk`.

## إذا فشل البناء
لا تغيّر ملفات التطبيق. افتح خطوة **Build APK with Buildozer** وانسخ آخر جزء من الخطأ، وأرسله كما هو. سيتم التعامل مع خطأ البناء فقط.
