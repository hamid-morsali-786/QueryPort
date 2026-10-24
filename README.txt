================================================================================
                    QueryPort - Oracle SQL Utility (Export & Import)
================================================================================

یک ابزار سبک، ماژولار و بسیار سریع بر پایه پایتون با قابلیت اجرای مستقل (بدون نیاز
به پایتون یا اوراکل کلاینت) برای استخراج (Export) داده‌ها از دیتابیس اوراکل به قالب‌های
CSV (سازگار با فارسی در اکسل) و اسکریپت‌های SQL INSERT، و همچنین بارگذاری و ورود
(Import) فوق‌سریع انبوه فایل‌های CSV به جداول دیتابیس اوراکل.


--------------------------------------------------------------------------------
۱. ویژگی‌های کلیدی (Key Features)
--------------------------------------------------------------------------------
* اتصال مستقیم Thin Mode (بدون کلاینت اوراکل):
  اتصال ۱۰۰٪ شبکه‌ای بدون نیاز به Oracle Instant Client، DLLهای اوراکل یا فایل tnsnames.ora.

* استریمینگ بهینه با حافظه ثابت O(1):
  واکشی و درج بلوکی رکوردها جهت جلوگیری از اشغال رم حتی در جداول چندمیلیون سطری.

* کنسول تعاملی یکپارچه دوحالته:
  منوی شروع هوشمند با پشتیبانی از دابل‌کلیک در ویندوز جهت انتخاب ساده بین حالت استخراج (Export)
  و ورود داده (Import) بدون بسته شدن ناگهانی پنجره سیاه ترمینال.

* امکانات استخراج (Export Engine):
  - پوشه‌بندی و شماره‌گذاری خودکار به ازای هر فایل SQL و جدول.
  - خروجی CSV با انکودینگ UTF-8-SIG و بایت‌های BOM جهت نمایش بی‌نقص متون فارسی در اکسل.
  - تولید اسکریپت استاندارد INSERT با خنثی‌سازی تک‌کوت‌ها ('')، متغیرهای رزرو شده (&)،
    تبدیل دقیق تاریخ‌ها (TO_DATE و TO_TIMESTAMP با دقت میکروثانیه) و دستور COMMIT.
  - پیش‌نمایش سریع تعداد رکوردها با سوییچ --dry-run و --confirm.

* امکانات بارگذاری و ورود داده (Import Engine):
  - اعتبارسنجی پیشگیرانه از متادیتای اوراکل (ALL_TABLES و ALL_TAB_COLS): کنترل وجود جدول،
    انطباق کامل ستون‌ها، و کشف ستون‌های NOT NULL بدون مقدار پیش‌فرض قبل از لمس دیتابیس.
  - درج دسته‌ای با سرعت بالا (cursor.executemany با بایند پارامترها).
  - استراتژی‌های متنوع کامیت: batch (دسته‌ای)، row (سطری)، all (یکجا).
  - سیاست‌های برخورد با داده‌های قبلی: append (الحاق)، truncate (پاکسازی)، skip (رد کردن).
  - مدیریت خطای سطرها: abort (توقف) یا skip_and_log (ثبت رکوردهای رد شده در CSV خطا).


--------------------------------------------------------------------------------
۲. فایل‌های تنظیمات (Configuration Files)
--------------------------------------------------------------------------------
الف) فایل تنظیمات استخراج (config.json):
{
  "database": {
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "TARGET_SCHEMA"
  },
  "defaults": {
    "input_path": "test_sql",
    "output_dir": "exports",
    "format": "both",
    "batch_size": 1000
  }
}

ب) فایل تنظیمات ورود داده (import_config.json):
{
  "database": {
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "TARGET_SCHEMA"
  },
  "import_settings": {
    "input_path": "imports",
    "commit_mode": "batch",
    "batch_size": 5000,
    "existing_data_action": "append",
    "on_error": "abort",
    "bad_rows_dir": "import_errors"
  }
}


--------------------------------------------------------------------------------
۳. منوی تعاملی کنسول (Interactive Console Launch)
--------------------------------------------------------------------------------
هنگام دابل‌کلیک روی QueryPort.exe منوی تعاملی زیر ظاهر می‌شود:

==================================================
           QueryPort Unified Console              
==================================================
Select Operation:
  [1 / E] : Export Database queries to CSV / SQL Insert (config.json)
  [2 / I] : Import CSV datasets into Database tables  (import_config.json)
  [exit / q] : Exit program

Enter choice [1/2] (Default: 1): 

* با انتخاب 1 یا فشردن Enter: عملیات استخراج بر اساس config.json اجرا می‌شود.
* با انتخاب 2: عملیات ورود داده بر اساس import_config.json آغاز می‌شود.


--------------------------------------------------------------------------------
۴. راهنمای پارامترهای خط فرمان (CLI Reference)
--------------------------------------------------------------------------------
دستور استخراج:
  QueryPort.exe [options]  یا  QueryPort.exe --mode export [options]
  --path, -p <مسیر>            آدرس فایل .sql یا پوشه فایل‌های SQL
  --schema, -s <اسکیما>        تغییر CURRENT_SCHEMA سشن اوراکل
  --format, -f <both|csv|insert>  نوع فرمت خروجی (پیش‌فرض: both)
  --dry-run, -d               پیش‌نمایش تعداد سطرها بدون ایجاد فایل
  --confirm                   پیش‌نمایش رکوردها و تقاضای تایید قبل از استخراج
  --config, -c <مسیر JSON>    مسیر فایل تنظیمات (پیش‌فرض: config.json)
  --output, -o <مسیر پوشه>    مسیر پوشه خروجی (پیش‌فرض: exports)
  --batch-size, -b <عدد>      اندازه دسته استریم (پیش‌فرض: 1000)

دستور بارگذاری:
  QueryPort.exe import [options]  یا  QueryPort.exe --mode import [options]
  --path, -p <مسیر>            مسیر پوشه یا فایل CSV جهت ورود داده
  --schema, -s <اسکیما>        اسکیمای هدف جداول اوراکل
  --commit-mode <batch|row|all> استراتژی کامیت (پیش‌فرض: batch)
  --batch-size, -b <عدد>      تعداد رکوردهای هر بسته (پیش‌فرض: 5000)
  --existing-data <append|truncate|skip> رفتار با داده‌های فعلی جدول (پیش‌فرض: append)
  --on-error <abort|skip_and_log> استراتژی خطا (پیش‌فرض: abort)
  --bad-rows-dir <مسیر>       پوشه لاگ رکوردهای رد شده (پیش‌فرض: import_errors)
  --dry-run, -d               اعتبارسنجی متادیتا و بررسی ساختار بدون درج داده
  --config, -c <مسیر JSON>    مسیر کانفیگ ایمپورت (پیش‌فرض: import_config.json)


--------------------------------------------------------------------------------
۵. دستورات آماده کپی و اجرا (Cheat Sheet)
--------------------------------------------------------------------------------
# ۱. استخراج (Export):
QueryPort.exe --path test_sql --dry-run
QueryPort.exe --path test_sql --format csv
QueryPort.exe --path sql_queries --format both --output my_exports

# ۲. ورود داده (Import):
QueryPort.exe import --dry-run
QueryPort.exe import --path imports --commit-mode batch --batch-size 5000
QueryPort.exe import --path imports --existing-data truncate --on-error skip_and_log


--------------------------------------------------------------------------------
۶. آزمون‌ها و تضمین کیفیت (Testing & QA)
--------------------------------------------------------------------------------
اجرای ۳۶ آزمون واحد (Unit Tests) بدون وابستگی به دیتابیس لایو:
  python -m unittest discover -v
  (یا pytest -v)
================================================================================
