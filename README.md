<div align="center">

# کوئری‌پورت (QueryPort)
### ابزار فوق‌سریع، سبک و مستقل استخراج و بارگذاری داده‌های پایگاه داده اوراکل (Oracle Database)
### Dual-Engine: High-Performance Oracle Exporter & CSV Importer

[![GitHub Stars](https://img.shields.io/github/stars/hamid-morsali-786/QueryPort?style=for-the-badge&color=e8590c)](https://github.com/hamid-morsali-786/QueryPort/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/hamid-morsali-786/QueryPort?style=for-the-badge&color=f59e0b)](https://github.com/hamid-morsali-786/QueryPort/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-brightgreen?style=for-the-badge&logo=python)](https://python.org)
[![Oracle Thin Driver](https://img.shields.io/badge/Oracle-Thin%20Mode-red?style=for-the-badge&logo=oracle)](https://oracle.github.io/python-oracledb/)
[![Standalone Executable](https://img.shields.io/badge/Portable-Standalone%20EXE-blueviolet?style=for-the-badge&logo=windows)](https://github.com/hamid-morsali-786/QueryPort/releases)
[![CI Build](https://img.shields.io/badge/CI-Passing-success?style=for-the-badge&logo=githubactions)](https://github.com/hamid-morsali-786/QueryPort/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

<p align="center">
  <b>توسعه و نگهداری توسط:</b> <a href="https://github.com/hamid-morsali-786">hamid-morsali-786</a>
</p>

**فارسی** | [English](README.en.md)

</div>

---

<div dir="rtl">

## 📑 فهرست مطالب (Table of Contents)

- [معرفی و چرا QueryPort؟](#معرفی-و-چرا-queryport)
- [ویژگی‌های کلیدی](#ویژگیهای-کلیدی-key-features)
- [جدول مقایسه قابلیت‌ها](#جدول-مقایسه-قابلیتها)
- [معماری سیستم (Architecture)](#معماری-سیستم-architecture)
- [راهنمای تصویری ترمینال و خط فرمان (Visual Terminal Guide)](docs/terminal_guide.md)
- [نصب و راه‌اندازی](#نصب-و-راهاندازی-installation)
- [شروع سریع و جریان‌های کاری خط فرمان (CLI)](#شروع-سریع-و-جریانهای-کاری-خط-فرمان-cli)
- [فایل اجرایی مستقل و کنسول تعاملی یکپارچه (Unified Interactive Console)](#فایل-اجرایی-مستقل-و-کنسول-تعاملی-یکپارچه-unified-interactive-console)
- [موتور استخراج داده‌ها (Export Engine)](#موتور-استخراج-دادهها-export-engine)
- [موتور هوشمند بارگذاری و ورود داده‌ها (CSV Importer Subsystem)](#موتور-هوشمند-بارگذاری-و-ورود-دادهها-csv-importer-subsystem)
- [موتور موازی‌سازی سازمانی و اتصال هوشمند به کلاستر RAC (Enterprise Concurrency & RAC Affinity)](#موتور-موازیسازی-سازمانی-و-اتصال-هوشمند-به-کلاستر-rac-enterprise-concurrency--rac-affinity)
- [راهنمای جامع تنظیمات (config.json)](#راهنمای-جامع-تنظیمات-configjson)
- [جدول جامع تمام پارامترهای خط فرمان (CLI Reference)](#جدول-جامع-تمام-پارامترهای-خط-فرمان-cli-reference)
- [دستورات آماده کپی و اجرا (Ready-to-Run Cheat Sheet)](#دستورات-آماده-کپی-و-اجرا-ready-to-run-cheat-sheet)
- [موتور هوشمند تفکیک و پردازش کوئری‌ها (Smart SQL Parser)](#موتور-هوشمند-تفکیک-و-پردازش-کوئریها-smart-sql-parser)
- [فرمت‌های خروجی و پشتیبانی از داده‌های فارسی (UTF-8-SIG & SQL Inserts)](#فرمتهای-خروجی-و-پشتیبانی-از-دادههای-فارسی-utf-8-sig--sql-inserts)
- [بسته آماده استقرار در محیط عملیاتی (Production Deployment)](#بسته-آماده-استقرار-در-محیط-عملیاتی-production-deployment)
- [آزمون‌ها و تضمین کیفیت (Testing & QA)](#آزمونها-و-تضمین-کیفیت-testing--qa)
- [تاریخچه ستاره‌ها (Star History)](#تاریخچه-ستارهها-star-history)
- [مشارکت و حق امتیاز](#مشارکت-و-حق-امتیاز)

---

## 🎯 معرفی و چرا QueryPort؟

در پروژه‌های سازمانی، مهاجرت داده‌ها، سیستم‌های یکپارچه‌سازی و فرآیندهای انبارش داده، دو نیاز اساسی و تکرارشونده وجود دارد:
1. **استخراج مداوم و سریع داده‌ها (Export):** تبدیل خروجی صدها کوئری پیچیده از دیتابیس اوراکل به فایل‌های استاندارد CSV یا اسکریپت‌های INSERT سازگار.
2. **ورود و بارگذاری حجیم داده‌ها (Import):** خواندن فایل‌های CSV تو در تو و بارگذاری با سرعت بسیار بالا در جداول متناظر پایگاه داده اوراکل با اعتبارسنجی ساختار، تراکنش‌های دسته‌ای و ثبت دقیق خطاهای احتمالی.

ابزارهای سنتی و متفرقه با چالش‌هایی همچون نیاز به نصب پردردسر Oracle Client/Instant Client، سرریز حافظه در حجم‌های بالا (OOM Crash)، به‌هم‌ریختگی حروف فارسی در اکسل و فقدان اعتبارسنجی پیشگیرانه مواجه هستند.

**QueryPort** یک راه‌حل جامع، سبک، دوطرفه (Export & Import) و کاملاً پرتابل است که بدون نیاز به هیچ‌گونه نصب یا پیش‌نیاز روی سرور، با درایور مستقیم **Thin Mode** اوراکل کار می‌کند.

---

## ⚡ ویژگی‌های کلیدی (Key Features)

### 🔹 قابلیت‌های مشترک و هسته مرکزی:
* 🚀 **اتصال مستقیم Thin Mode (بدون کلاینت اوراکل):** اتصال ۱۰۰٪ شبکه‌ای بدون نیاز به Oracle Instant Client، DLLهای اوراکل یا فایل `tnsnames.ora`.
* 💾 **استریمینگ بهینه با حافظه ثابت $O(1)$:** خواندن و نوشتن بلوکی رکوردها جهت جلوگیری از اشغال رم حتی در جداول چندمیلیون سطری.
* 🖥️ **کنسول تعاملی یکپارچه دو حالته:** منوی شروع هوشمند با پشتیبانی از دابل‌کلیک در ویندوز جهت انتخاب ساده بین حالت استخراج (Export) و ورود داده (Import).
* 📦 **فایل باینری مستقل و پرتابل (`QueryPort.exe`):** بدون نیاز به نصب پایتون یا هیچ وابستگی در سرور مقصد.
* 🛡️ **پشتیبانی از اسکیمای مجزا (`schema`):** امکان تغییر اسکیمای جاری سشن (`CURRENT_SCHEMA`) مستقل از نام کاربری اتصال.

### 📤 امکانات موتور استخراج داده (Export Engine):
* 📂 **سازمان‌دهی خودکار پوشه‌ها:** شناسایی نام جدول، تفکیک هر فایل اسکریپت در یک پوشه اختصاصی، و شماره‌گذاری ترتیبی خروجی‌ها.
* 🇮🇷 **سازگاری کامل با اکسل و متون فارسی:** ذخیره‌سازی فایل‌های CSV با انکودینگ استاندارد `UTF-8-SIG` (دارای BOM) برای نمایش بی‌نقص داده‌های فارسی و یونیکد در اکسل.
* 📝 **تولید اسکریپت‌های استاندارد INSERT اوراکل:** با خنثی‌سازی تک‌کوت‌ها (`''`)، درج `SET DEFINE OFF;` جهت جلوگیری از تداخل `&`، تبدیل تاریخ‌ها به توابع `TO_DATE` و `TO_TIMESTAMP` با دقت میکروثانیه، و دستور `COMMIT;`.
* 🔍 **شبیه‌سازی و شمارش رکوردها بدون ایجاد فایل (Dry-Run):** سوییچ `--dry-run` و `--confirm` برای شمارش سریع تعداد سطرهای هر کوئری در دیتابیس قبل از ایجاد فایل خروجی.

### 📥 امکانات موتور بارگذاری و ورود داده (Import Engine):
* 🚀 **موتور موازی‌سازی هیبرید سازمانی (Hybrid Concurrency Engine):**
  * **موازی‌سازی چند فایلی (Table-Level Parallelism):** پردازش همزمان چندین جدول/فایل CSV با تخصیص Worker Threadهای مجزا.
  * **خرد کردن تک‌فایل‌های غول‌پیکر (Intra-Table Chunking):** قطعه‌بندی استریم فایل‌های حجیم چندمیلیونی به تکه‌های ۲۵,۰۰۰ تا ۵۰,۰۰۰ سطری با مصرف رم ثابت $O(1)$.
  * **مسیریابی سرویس‌های اوراکل RAC (Workload & Node Affinity):** توزیع هوشمند Workerها روی سرویس‌های مختلف نودهای Oracle RAC جهت ممانعت از ترافیک Cache Fusion و پدیده Block Pinging.
  * **طراحی Progressive Disclosure:** رفتار پیش‌فرض برنامه ۱۰۰٪ تک‌تردی و ساده برای کاربران عادی باقی مانده و پیچیدگی جدیدی تحمیل نمی‌شود.
* 🔎 **اعتبارسنجی پیشگیرانه از متادیتای دیتابیس (Pre-validation Engine):**
  * کنترل قطعی وجود جدول مقصد در دیتابیس اوراکل (`ALL_TABLES`).
  * تطبیق ۱۰۰٪ نام تمام ستون‌های موجود در هدر فایل CSV با ستون‌های تعریف‌شده در جدول اوراکل (`ALL_TAB_COLS`).
  * کشف و گزارش ستون‌های با قید `NOT NULL` در جدول که در فایل CSV غایب هستند و مقدار پیش‌فرض (`DATA_DEFAULT`) ندارند؛ با توقف فوری و لغو ایمن عملیات قبل از هرگونه تغییر در دیتابیس.
* ⚡ **ورود دسته‌ای پرسرعت (Bulk Parameterized Ingestion):** استفاده از `cursor.executemany` با بایند متغیرها برای حداکثر سرعت در لایه شبکه و اوراکل.
* 🔄 **انعطاف در سیاست‌های کامیت (Commit Strategies):**
  * `batch`: کامیت بلوکی بر اساس اندازه مشخص‌شده (مثلاً هر ۵۰۰۰ سطر یکبار).
  * `row`: کامیت تک‌تک رکوردها به ازای هر سطر جهت بالاترین قابلیت اطمینان.
  * `all`: کامیت یکجای تراکنش پس از پایان کامل پردازش هر جدول.
* 🧹 **مدیریت داده‌های موجود در جداول (Existing Data Handling):**
  * `append`: الحاق به داده‌های موجود جدول.
  * `truncate`: پاکسازی کامل و فوق‌سریع جدول قبل از بارگذاری داده‌های جدید (`TRUNCATE TABLE`).
  * `skip`: نادیده گرفتن جداول دارای سطر قبلی و عبور به جدول بعدی.
* 📝 **استراتژی‌های مواجهه با خطا و لاگ رکوردهای مردود:**
  * `abort`: توقف بلادرنگ فرآیند و رول‌بک تراکنش جاری.
  * `skip_and_log`: ثبت اتوماتیک شماره سطر، علت خطا و مقادیر در پوشه `import_errors/<TABLE>_rejected.csv` و ادامه پردازش سایر سطرها.
* 📊 **گزارش آماری دقیق:** نمایش تفکیکی و تجمیعی تعداد سطرهای خوانده‌شده، وارد شده و با خطا مواجه‌شده، مدت زمان و نرخ درج بر ثانیه (rows/sec).

---

## 📊 جدول مقایسه قابلیت‌ها

| ویژگی / قابلیت | **QueryPort** | Oracle SQL Developer | اسکریپت‌های دستی پایتون | DBeaver |
| :--- | :---: | :---: | :---: | :---: |
| **عدم نیاز به نصب ابزار / پرتابل** | ✅ بله (تک‌فایل EXE) | ❌ خیر (نیاز به JDK و نصب) | ❌ خیر (نیاز به محیط پایتون) | ❌ خیر (نیاز به Java) |
| **عدم نیاز به Oracle Instant Client** | ✅ بله (Thin Mode) | ⚠️ در اکثر نسخه‌ها نیازمند است | ⚠️ وابسته به درایور cx_Oracle | ⚠️ نیازمند دانلود درایور JDBC |
| **استریمینگ با مصرف کم رم** | ✅ استریمینگ دسته‌ای | ❌ معمولاً کش در رم | ❌ غالباً `fetchall()` | ⚠️ با تنظیم دستی Fetch Size |
| **سازگاری خودکار فارسی در Excel** | ✅ پیش‌فرض (UTF-8-SIG) | ❌ دستی (نیاز به تنظیم کدپیج) | ⚠️ نیازمند تنظیم دستی کدگذاری | ❌ دستی |
| **پیش‌نمایش تعداد سطرها قبل از اجرا** | ✅ `--dry-run` و `--confirm` | ❌ خیر | ❌ خیر | ❌ خیر |
| **خروجی تمیز SQL INSERT با اسکیپ کامل** | ✅ استاندارد با `SET DEFINE OFF` | ⚠️ فرمت دستی اکسپورت | ❌ نیاز به کدنویسی طولانی | ⚠️ نیاز به تنظیم Wizard |
| **پشتیبانی از پوشه‌بندی و بچ فایل‌ها** | ✅ خودکار بر اساس نام فایل | ❌ خروجی دستی تک‌تک | ❌ نیاز به پیاده‌سازی دستی | ❌ خروجی دستی |
| **موازی‌سازی چندتردی و تفکیک بار نودهای RAC** | ✅ پیشرفته (Table + Chunk + RAC) | ❌ خیر (تک‌سشن) | ⚠️ نیازمند کدنویسی همروندی | ❌ خیر |

---

## 🏗️ معماری سیستم (Architecture)

```mermaid
flowchart TD
    subgraph منابع و تنظیمات ورودی
        SQLIn["اسکریپت‌های ورودی (.sql)"]
        CSVIn["فایل‌های CSV دیتاست (.csv)"]
        Config["تنظیمات یکپارچه<br/>config.json (شامل Concurrency & RAC)"]
    end

    subgraph هسته پردازش دوگانه QueryPort
        CLI["هماهنگ‌کننده خط فرمان و کنسول تعاملی<br/>(Unified CLI & Interactive Console)"]
        
        subgraph موتور استخراج داده - Export Engine
            Parser["موتور تجزیه و پاکسازی کوئری‌ها<br/>(Comments, SQL*Plus, Table Extractor)"]
            StreamExp["استریمینگ دسته‌ای با حافظه O(1)<br/>(cursor.fetchmany)"]
            CSVGen["تولیدکننده CSV استاندارد<br/>(UTF-8-SIG BOM)"]
            SQLGen["تولید اسکریپت استاندارد INSERT<br/>(Escape Quotes, Timestamps, Commits)"]
        end

        subgraph موتور ورود داده و همزمانی - Import & Concurrency Engine
            Validator["اعتبارسنجی دیکشنری داده اوراکل<br/>(ALL_TABLES & ALL_TAB_COLS)"]
            Router{"مسیریاب همزمانی<br/>(Concurrency Router)"}
            MultiFile["موازی‌سازی چند فایلی<br/>(Table-Level Parallelism)"]
            Chunking["خرد کردن تک‌فایل بزرگ<br/>(Intra-Table Chunking)"]
            ThreadPool["استخر تردها<br/>(ThreadPoolExecutor)"]
            ErrLog["لاگر ضدتداخل خطا<br/>(ThreadSafeErrorLogger)"]
        end
    end

    subgraph کلاستر پایگاه داده اوراکل
        RAC["Oracle Database 19c RAC<br/>Thin Mode Network Protocol"]
        Node1[("Node 1 / Service 1")]
        Node2[("Node 2 / Service 2")]
        NodeN[("Node N / Service N")]
    end

    Config --> CLI
    SQLIn --> Parser
    CSVIn --> Validator

    CLI --> Parser
    CLI --> Validator

    Parser --> StreamExp
    StreamExp <-->|"واکشی دسته‌ای داده‌ها"| RAC
    StreamExp --> CSVGen
    StreamExp --> SQLGen

    Validator <-->|"استعلام متادیتای ساختار و NOT NULL"| RAC
    Validator --> Router
    Router -->|"چندین فایل"| MultiFile --> ThreadPool
    Router -->|"تک‌فایل حجیم"| Chunking --> ThreadPool
    ThreadPool <-->|"Worker 1 -> RAC Service 1"| Node1
    ThreadPool <-->|"Worker 2 -> RAC Service 2"| Node2
    ThreadPool <-->|"Worker N -> RAC Service N"| NodeN
    ThreadPool -.->|"در صورت خطای سطر با قفل اتمیک"| ErrLog
```

---

## 📦 نصب و راه‌اندازی (Installation)

### ۱. استفاده از فایل اجرایی آماده (پیشنهادی برای پروداکشن)
بدون نیاز به پایتون یا درایور اوراکل، باینری مستقل `QueryPort.exe` را در کنار فایل پیکربندی یکپارچه `config.json` قرار دهید (که هر دو عملیات Export و Import را مدیریت می‌کند).

### ۲. اجرا از روی سورس‌کد پایتون (محیط توسعه)
در صورتی که می‌خواهید پروژه را در محیط پایتون اجرا و توسعه دهید:

```bash
# ۱. کلون کردن مخزن
git clone https://github.com/hamid-morsali-786/QueryPort.git
cd QueryPort

# ۲. ایجاد و فعال‌سازی محیط مجازی
python -m venv .venv

# در ویندوز:
.\.venv\Scripts\activate
# در لینوکس / مک:
source .venv/bin/activate

# ۳. نصب وابستگی‌ها
pip install -r requirements.txt
```

---

## 🚀 شروع سریع و جریان‌های کاری خط فرمان (CLI)

### اجرای تعاملی هوشمند (دابل‌کلیک یا بدون آرگومان):
```bash
QueryPort.exe
# یا با پایتون:
python export_sql.py
```

### عملیات استخراج (Export):
```bash
# استخراج سریع با تنظیمات پیش‌فرض config.json:
QueryPort.exe --mode export

# پیش‌نمایش تعداد رکوردهای فایل خاص بدون استخراج:
QueryPort.exe --path test_sql/01_CUSTOMERS_AND_ACCOUNTS.sql --dry-run

# استخراج پوشه به هر دو قالب CSV و اسکریپت استاندارد INSERT:
QueryPort.exe --path sql_queries --format both --batch-size 10000
```

![QueryPort Parallel Export](docs/assets/terminal_export.svg)

### عملیات بارگذاری و ایمپورت (Import):
```bash
# پیش‌نمایش و اعتبارسنجی ساختار بدون درج داده (Dry-Run):
QueryPort.exe import --dry-run
# یا معادل آن:
QueryPort.exe --mode import --dry-run

# بارگذاری کلیه فایل‌های CSV با کامیت‌های دسته‌ای ۵۰۰۰ تایی:
QueryPort.exe import --path imports --commit-mode batch --batch-size 5000

# پاکسازی جداول پیش از بارگذاری و ثبت رکوردهای دارای خطا در لاگ:
QueryPort.exe import --path imports --existing-data truncate --on-error skip_and_log
```

---

## 🖱️ فایل اجرایی مستقل و کنسول تعاملی یکپارچه (Unified Interactive Console)

هنگامی که روی فایل `QueryPort.exe` دو بار کلیک می‌کنید، کنسول تعاملی هوشمند باز شده و از بسته شدن ناگهانی صفحه جلوگیری می‌کند:

![QueryPort Interactive Console](docs/assets/terminal_interactive.svg)

```text
==================================================
           QueryPort Unified Console              
==================================================
Select Operation:
  [1 / E] : Export Database queries to CSV / SQL Insert (config.json)
  [2 / I] : Import CSV datasets into Database tables  (config.json)
  [exit / q] : Exit program

Enter choice [1/2] (Default: 1): 
```

* **گزینه `1` یا `E` (Export):** فرآیند استخراج با تنظیمات بخش `export` در `config.json` را اجرا می‌کند یا با انتخاب `n` پرامپت سفارشی `QueryPort (export)>` را در اختیارتان می‌گذارد.
* **گزینه `2` یا `I` (Import):** فرآیند بارگذاری با تنظیمات بخش `import` در `config.json` را آغاز کرده و یا پرامپت سفارشی `QueryPort (import)>` را برای آرگومان‌های دلخواه باز می‌نماید.

---

## 📥 موتور هوشمند بارگذاری و ورود داده‌ها (CSV Importer Subsystem)

موتور ورود داده `import_sql` به طور اختصاصی جهت ایمپورت امن، سریع و دقیق انبوه فایل‌های CSV تولیدشده به جداول اوراکل طراحی شده است.

### ۱. کشف خودکار فایل‌ها و تطبیق نام جداول
فایل‌ها می‌توانند در پوشه اصلی یا زیرپوشه‌های تودرتو قرار داشته باشند. موتور به طور خودکار پیشوندهای ترتیبی (نظیر `02_BANKPARAMETERS.csv`) را تفکیک کرده و نام خالص جدول (`BANKPARAMETERS`) را جهت تطبیق استخراج می‌کند.

### ۲. اعتبارسنجی متادیتای دیتابیس اوراکل (Data Dictionary Validation)
پیش از اجرای حتی یک دستور `INSERT` یا دستکاری جداول:
1. وجود جدول در اسکیمای هدف اوراکل بررسی می‌شود.
2. تطابق تمامی ستون‌های هدر فایل CSV با ستون‌های تعریف‌شده در جدول اوراکل ارزیابی می‌گردد.
3. در صورت وجود ستونی با قید `NOT NULL` در جدول که در فایل CSV وجود ندارد و فاقد مقدار `DATA_DEFAULT` باشد، سامانه خطای جامع صادر کرده و بلافاصله متوقف می‌شود.

با اجرای سوییچ `--dry-run`، پیش‌نمایش جدول تطابق ستون‌ها و صحت اعتبارسنجی بدون کوچکترین ریسک نمایش داده می‌شود:

![QueryPort Schema Pre-Validation](docs/assets/terminal_import_dryrun.svg)

### ۳. استراتژی‌های تراکنش و کامیت (Commit Strategies)
* **`batch` (پیش‌فرض):** به ازای هر $N$ سطر (مثلاً ۵,۰۰۰ رکورد)، دستور `commit` صادر می‌شود. ایده‌آل برای بهینه‌سازی منابع UNDO tablespace و جلوگیری از قفل‌های سنگین.
* **`row`:** کامیت پس از هر رکورد منفرد (بسیار دقیق با اطمینان حداکثری).
* **`all`:** یک کامیت منفرد در انتهای هر فایل/جدول.

### ۴. مدیریت رکوردهای رد شده و مواجهه با خطا
در صورت فعال بودن `--on-error skip_and_log`:
* خطاهای داده‌ای (نظیر مقادیر نامعتبر کلید خارجی یا طول فیلد) مانع از توقف کل عملیات نمی‌شوند.
* رکوردهای رد شده همراه با شماره ردیف و پیام دقیق خطای اوراکل در مسیر `import_errors/<TABLE>_rejected.csv` ثبت می‌گردند.

---

## ⚡ موتور موازی‌سازی سازمانی و هماهنگی با کلاستر RAC (Enterprise Concurrency & RAC Affinity)

در محیط‌های دیتابیسی بزرگ و سازمانی که با حجم‌های ده‌ها میلیون سطری یا کلاسترهای چندنودی **Oracle Real Application Clusters (RAC)** سر و کار دارند، بارگذاری داده‌ها با چالش‌های گلوگاه شبکه و رقابت کلاستر مواجه می‌شود. **QueryPort** یک معماری موازی‌سازی هوشمند دو سطحی (Hybrid Concurrency) را پیاده‌سازی کرده است:

### ۱. معماری همزمانی هیبرید (Hybrid Concurrency Architecture)
* **موازی‌سازی چند فایلی (Table-Level Parallelism):** هنگامی که چندین فایل CSV در پوشه ورودی وجود دارد و پرچم `--workers N` مشخص شده است، هر فایل/جدول به یک Worker Thread مجزا تخصیص داده می‌شود. از آنجا که جداول از یکدیگر مستقل هستند، هیچ‌گونه رقابت بلاکی در سطح پایگاه داده شکل نمی‌گیرد.
* **خرد کردن تک‌فایل بزرگ (Intra-Table Chunking):** در صورتی که کاربر یک تک‌فایل عظیم (مثلاً ۲۰ میلیون سطری) را برای یک جدول بارگذاری کند، موتور به طور خودکار فایل را در قطعات با اندازه قابل تنظیم (پیش‌فرض ۲۵,۰۰۰ سطر با `--chunk-size`) خرد کرده و بدون لود کل فایل در حافظه ($O(1)$ RAM)، قطعات را به صورت موازی بین تردها توزیع می‌کند.

### ۲. مسیریابی سرویس‌ها و تفکیک بار روی نودهای RAC (Workload & Node Affinity)
در کلاستر RAC، اگر چندین سشن بدون تفکیک نود روی یک جدول ایندکس‌دار مشترک بنویسند، پدیده **Block Pinging** و رویدادهای انتظاری سنگین شبکه کلاستر (نظیر `gc current block busy` و `gc buffer busy acquire`) رخ می‌دهد.
* **راهکار QueryPort:** با استفاده از پارامتر `--rac-services` یا کلید `rac_services` در کانفیگ، می‌توان لیستی از نام سرویس‌های متصل به نودهای مختلف RAC را تعیین کرد:
  ```bash
  QueryPort.exe import --path imports --workers 4 --rac-services APP_NODE1_SRV,APP_NODE2_SRV,APP_NODE3_SRV,APP_NODE4_SRV
  ```
* موتور به صورت گردشی (Round-Robin)، هر Worker Thread را مستقیماً به سرویس اختصاصی آن نود متصل می‌کند تا ترافیک شبکه کلاستر و تداخل اینترکانکت به حداقل ممکن برسد.

![QueryPort RAC Concurrency](docs/assets/terminal_concurrency_rac.svg)

### ۳. امنیت تراکنش و لاگر خطای ضدتداخل (Thread-Safe Error Logger)
* اعتبارسنجی دیکشنری داده اوراکل (`validate_import_plan`) و عملیات `TRUNCATE TABLE` قبل از استارت هرگونه ترد به صورت Single-Threaded اجرا می‌شوند تا از Race Condition پیشگیری شود.
* در صورت بروز خطا در هر یک از سطرها، کلاس [`ThreadSafeErrorLogger`](file:///e:/project/QueryPort/import_sql.py#L335) با استفاده از قفل اتمیک `threading.Lock` اطلاعات رکوردهای رد شده را به صورت خط‌به‌خط و بدون تداخل در فایل `import_errors/<TABLE>_rejected.csv` می‌نویسد.

---

## ⚙️ راهنمای جامع تنظیمات (config.json)

تمام تنظیمات برنامه اعم از اتصال به پایگاه داده اوراکل، گزینه‌های استخراج (Export) و پارامترهای بارگذاری (Import) در یک فایل یکپارچه `config.json` تجمیع شده‌اند:

```json
{
  "database": {
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "TARGET_SCHEMA"
  },
  "concurrency": {
    "workers": 1,
    "chunk_size": 25000,
    "rac_services": []
  },
  "export": {
    "input_path": "sql_queries",
    "output_dir": "exports",
    "format": "both",
    "batch_size": 1000
  },
  "import": {
    "input_path": "imports",
    "commit_mode": "batch",
    "batch_size": 5000,
    "existing_data_action": "append",
    "on_error": "abort",
    "bad_rows_dir": "import_errors"
  }
}
```

> [!NOTE]
> جهت حفظ سازگاری با نسخه‌های گذشته (Backward Compatibility)، نام‌های قدیمی کلیدها شامل `"defaults"` برای استخراج و `"import_settings"` برای ورود داده، و همچنین فایل‌های مجزای قدیمی همچنان بدون مشکل پشتیبانی و خوانده می‌شوند.

### جدول مشخصات تنظیمات ورود داده (`import`):
| کلید | نوع | مقدار پیش‌فرض | مقادیر معتبر | توضیحات |
| :--- | :---: | :---: | :---: | :--- |
| `input_path` | رشته | `imports` | مسیر فایل یا پوشه | دایرکتوری شامل فایل‌های CSV یا آدرس یک فایل CSV |
| `commit_mode` | رشته | `batch` | `batch`, `row`, `all` | استراتژی کامیت تراکنش‌ها |
| `batch_size` | عدد | `5000` | عدد صحیح مثبت | اندازه دسته‌ها برای کامیت در حالت `batch` |
| `existing_data_action` | رشته | `append` | `append`, `truncate`, `skip` | رفتار با داده‌های فعلی جدول قبل از ورود |
| `on_error` | رشته | `abort` | `abort`, `skip_and_log` | استراتژی مواجهه با خطای سطرها |
| `bad_rows_dir` | رشته | `import_errors` | مسیر پوشه | پوشه مقصد برای ذخیره فایل‌های CSV رکوردهای خطا دار |

---

## 📋 جدول جامع تمام پارامترهای خط فرمان (CLI Reference)

### ۱. دستورات و پارامترهای موتور استخراج (Export CLI Options)
اجرا با: `QueryPort.exe [options]` یا `QueryPort.exe export [options]` یا `QueryPort.exe --mode export [options]`

| پارامتر بلند | پارامتر کوتاه | مقادیر پذیرفته‌شده | پیش‌فرض | توضیحات عملکردی |
| :--- | :---: | :---: | :---: | :--- |
| `--path` | `-p` | مسیر فایل یا فولدر | طبق کانفیگ | آدرس فایل مشخص `.sql` یا پوشه شامل چندین فایل SQL |
| `--schema` | `-s` | نام اسکیما | طبق کانفیگ | تغییر اسکیمای جاری سشن اوراکل (`CURRENT_SCHEMA`) مستقل از یوزر لاگین |
| `--format` | `-f` | `both`, `csv`, `insert` | `both` | قالب فایل‌های خروجی |
| `--dry-run` | `-d` | پرچم بدون مقدار | - | **پیش‌نمایش تعداد رکوردها:** فقط شمارش سطرها در دیتابیس بدون ساخت فایل |
| `--confirm` | - | پرچم بدون مقدار | - | **پیش‌نمایش با تایید کاربر:** نمایش تعداد رکوردها و سپس دریافت تایید برای ادامه |
| `--config` | `-c` | مسیر فایل JSON | `config.json` | آدرس فایل کانفیگ سفارشی |
| `--output` | `-o` | مسیر پوشه | `exports` | تغییر دایرکتوری ذخیره فایل‌های خروجی |
| `--batch-size` | `-b` | عدد صحیح | `1000` | تعداد سطرهای واکشی در هر پارت استریم |
| `--help` | `-h` | پرچم بدون مقدار | - | نمایش راهنمای رسمی دستورات استخراج |

### ۲. دستورات و پارامترهای موتور بارگذاری (Import CLI Options)
اجرا با: `QueryPort.exe import [options]` یا `QueryPort.exe --mode import [options]` یا `python import_sql.py [options]`

| پارامتر بلند | پارامتر کوتاه | مقادیر پذیرفته‌شده | پیش‌فرض | توضیحات عملکردی |
| :--- | :---: | :---: | :---: | :--- |
| `--path` | `-p` | مسیر فایل یا پوشه | `imports` | مسیر فایل CSV یا پوشه حاوی فایل‌های CSV جهت ورود |
| `--config` | `-c` | مسیر فایل JSON | `config.json` | آدرس فایل تنظیمات (با پشتیبانی از کانفیگ تفکیکی) |
| `--schema` | `-s` | نام اسکیما | طبق کانفیگ | اسکیمای هدف دیتابیس اوراکل جهت اعتبارسنجی و درج |
| `--commit-mode` | - | `batch`, `row`, `all` | `batch` | استراتژی ثبت تراکنش‌ها (دسته‌ای، سطری یا پایانی) |
| `--batch-size` | `-b` | عدد صحیح مثبت | `5000` | تعداد سطرهای هر بسته جهت درج دسته‌ای و کامیت |
| `--existing-data` | - | `append`, `truncate`, `skip` | `append` | سیاست رفتار با داده‌های قبلی جدول |
| `--on-error` | - | `abort`, `skip_and_log` | `abort` | استراتژی مواجهه با خطای درج رکورد |
| `--bad-rows-dir` | - | مسیر دایرکتوری | `import_errors` | مسیر ثبت فایل‌های CSV رکوردهای خطادار مردود |
| `--dry-run` | `-d` | پرچم بدون مقدار | - | **اعتبارسنجی ساختار بدون درج داده:** بررسی جداول، ستون‌ها و Not Null |
| `--workers` | `-w` | عدد صحیح مثبت | `1` | **تعداد ترد‌های موازی:** برای موازی‌سازی فایل‌ها یا خرد کردن تک‌فایل |
| `--chunk-size` | - | عدد صحیح مثبت | `25000` | تعداد سطرهای هر قطعه در خرد کردن تک‌فایل بزرگ |
| `--rac-services` | - | لیست جداشده با کاما | - | لیست سرویس‌های Oracle RAC جهت مسیریابی و تفکیک بار نودها |
| `--help` | `-h` | پرچم بدون مقدار | - | نمایش راهنمای رسمی دستورات ایمپورت |

---

## 💡 دستورات آماده کپی و اجرا (Ready-to-Run Cheat Sheet)

```bash
# =============================================================
# ۱. استخراج داده‌ها (Export Operations)
# =============================================================

# بررسی سریع تعداد رکوردهای فایل خاص بدون استخراج:
QueryPort.exe --path test_sql/01_CUSTOMERS_AND_ACCOUNTS.sql --dry-run

# بررسی تمام فایل‌های یک پوشه:
QueryPort.exe --path sql_queries --dry-run

# استخراج کامل (هم CSV و هم SQL INSERT):
QueryPort.exe --path sql_queries --format both

# استخراج فقط فایل‌های اکسل/CSV با پشتیبانی متن فارسی:
QueryPort.exe --path sql_queries --format csv

# استخراج با تغییر اسکیمای هدف و پوشه خروجی:
QueryPort.exe --path test_sql --schema TARGET_SCHEMA --output D:\Backups\Today

# =============================================================
# ۲. بارگذاری داده‌ها (Import Operations)
# =============================================================

# اعتبارسنجی متادیتا و بررسی سلامت بدون تغییر دیتابیس (Dry-Run):
QueryPort.exe import --dry-run

# بارگذاری یک فایل CSV مشخص:
QueryPort.exe import --path imports/02_BANKPARAMETERS.csv

# بارگذاری کلیه فایل‌های یک پوشه با کامیت ۵۰۰۰ تایی و پاکسازی جداول قبلی:
QueryPort.exe import --path imports --existing-data truncate --batch-size 5000

# بارگذاری مطمئن با کامیت سطر به سطر و ذخیره رکوردهای رد شده در لاگ:
QueryPort.exe import --commit-mode row --on-error skip_and_log

# بارگذاری فوق‌سریع موازی با ۴ ترد روی چندین فایل:
QueryPort.exe import --path imports --workers 4

# بارگذاری تک‌فایل بزرگ ۲۰ میلیون سطری با خرد کردن ۵۰ هزارتایی و توزیع روی سرویس‌های نودهای RAC:
QueryPort.exe import --path imports/large_table.csv --workers 4 --chunk-size 50000 --rac-services RAC_SRV1,RAC_SRV2

# اجرای بارگذاری روی اسکیمای مجزا:
QueryPort.exe import --schema CRM_SCHEMA --config config.json
```

---

## 🧠 موتور هوشمند تفکیک و پردازش کوئری‌ها (Smart SQL Parser)

اسکریپت‌های استخراج دیتابیس اغلب حاوی دستورات گزارش‌گیری و کامنت‌های ابزارهایی مانند SQL*Plus هستند. **QueryPort** به صورت خودکار موارد زیر را پیش از اجرا فیلتر و استانداردسازی می‌کند:

1. **حذف دستورات محیطی SQL\*Plus:** فیلتر خودکار دستورات `PROMPT`, `SET`, `SPOOL`, `CLEAR`, `SHOW` و ...
2. **پاکسازی کامنت‌ها:** حذف کامنت‌های تک‌خطی (`--`) و کامنت‌های چندخطی (`/* ... */`) حتی اگر داخل بلاک‌های پیچیده باشند.
3. **تفکیک عبارات با سمیکالن (`;`):** شکستن دستورات به صورت چند کوئری مستقل و اجرای ترتیبی هر یک با مکانیسم مدیریت خطا.
4. **استخراج هوشمند نام جدول:** شناسایی نام جدول حتی در صورت وجود پیشوند اسکیما مانند `MY_SCHEMA.CUSTOMER_ACCOUNTS` و نام‌گذاری خروجی با نام تمیز جدول (`CUSTOMER_ACCOUNTS`).

---

## 🔤 فرمت‌های خروجی و پشتیبانی از داده‌های فارسی

### ۱. فایل‌های CSV (Excel-Compatible)
* **انکودینگ استاندارد:** `utf-8-sig` (تزریق بایت‌های BOM در ابتدای فایل).
* باز شدن بدون هیچ‌گونه بهم‌ریختگی حروف فارسی و فونت در مایکروسافت اکسل بدون نیاز به Data Import Wizard.
* کوتینگ استاندارد فیلدهای حاوی ویرگول، انتر (Newline) و کاراکترهای خاص طبق استاندارد RFC 4180.

### ۲. اسکریپت‌های SQL INSERT (اوراکل سازگار)
* قرار دادن دستور `SET DEFINE OFF;` در خط اول فایل جهت ممانعت از توقف اجرای اسکریپت در زمان برخورد با کاراکترهای `&`.
* تبدیل امن تک‌کوت‌های داخل متن به `''`.
* تبدیل دقیق تاریخ و زمان به توابع استانداردی اوراکل:
  ```sql
  TO_DATE('2026-10-21 14:30:00', 'YYYY-MM-DD HH24:MI:SS')
  TO_TIMESTAMP('2026-10-21 14:30:00.123456', 'YYYY-MM-DD HH24:MI:SS.FF6')
  ```
* مدیریت مقادیر تهی (`NULL`) بدون ایجاد کوتیشن اضافه.
* درج اتوماتیک دستور `COMMIT;` در پایان عملیات.

---

## 🏢 بسته آماده استقرار در محیط عملیاتی (Production Deployment)

پوشه `QueryPort_Production/` شامل پکیج ایزوله و کامل جهت انتقال به سرورها و محیط‌های عملیاتی است:

```text
Release/
│
├── QueryPort.exe                  # فایل باینری پرتابل و بدون وابستگی
├── config.json                    # فایل تنظیمات یکپارچه اتصال، استخراج و بارگذاری
├── config.example.json            # نمونه کامل تنظیمات
├── README.txt                     # راهنمای سریع متنی برای سرورها بدون مرورگر
├── README.md                      # راهنمای کامل فارسی
└── test_sql/                      # نمونه اسکریپت‌های SQL آزمایشی
```

برای استفاده در سرور، کافیست باینری `QueryPort.exe` و فایل `config.json` را در یک مسیر قرار داده، اطلاعات دیتابیس را تکمیل و برنامه را اجرا نمایید.

---

## 🧪 آزمون‌ها و تضمین کیفیت (Testing & QA)

پروژه دارای مجموعه ۴۶ آزمون واحد (Unit Tests) جامع بر پایه ماژول استاندارد `unittest` پایتون (بدون نیاز به کتابخانه‌های شخص ثالث مانند pytest) است که بدون نیاز به دیتابیس لایو تمام جنبه‌های برنامه را ارزیابی می‌کند:

```bash
# اجرای کلیه تست‌ها با کتابخانه استاندارد پایتون:
python -m unittest discover -v
```

### پوشش آزمون‌ها:
* ✅ **آزمون‌های استخراج (`test_export_sql.py` - ۲۱ تست):**
  * خواندن و اعتبارسنجی فایل تنظیمات یکپارچه و مدیریت خطاهای ساختاری.
  * پردازش و پالایش دستورات SQL*Plus (`PROMPT`, `SET`, `SPOOL`).
  * پاکسازی کامنت‌های تک‌خطی و چندخطی.
  * استخراج نام تمیز جدول با و بدون پیشوند اسکیما.
  * تولید خروجی CSV با BOM و انکودینگ UTF-8-SIG.
  * خنثی‌سازی و اسکیپ کاراکترهای خاص در دستورات INSERT.
  * استریمینگ کم‌مصرف حافظه با `fetchmany`.
  * منوی تعاملی و پرامپت کنسول یکپارچه.
* ✅ **آزمون‌های ورود داده (`test_import_sql.py` - ۲۵ تست):**
  * بارگذاری و اعتبارسنجی تنظیمات یکپارچه ایمپورت و پارامترهای Concurrency/RAC.
  * کشف تو در تو فایل‌های CSV و استخراج نام خالص جدول.
  * تبدیل داده‌های سلول، تبدیل رشته‌های خالی به `None` و پارس سریع تاریخ‌ها با `fromisoformat`.
  * استریمینگ حافظه با ژنراتور دسته‌ای در مقیاس $O(1)$ و ژنراتور قطعه‌بندی `stream_csv_chunks`.
  * لاگر ضد تداخل و ایمن در برابر چندتردی (`ThreadSafeErrorLogger`).
  * ارزیابی انطباق جداول، ستون‌ها و قیود NOT NULL فاقد مقدار پیش‌فرض.
  * آزمون استراتژی‌های کامیت (`batch`, `row`, `all`).
  * آزمون عملیات `truncate` و سیاست برخورد با داده‌های قبلی.
  * تفکیک و ثبت رکوردهای نامعتبر در فایل‌های لاگ خطا (`skip_and_log`).
  * موازی‌سازی چند فایلی و خرد کردن تک‌فایل بزرگ با پشتیبانی از RAC Services.

---

## ⭐ تاریخچه ستاره‌ها (Star History)

[![Star History Chart](https://api.star-history.com/svg?repos=hamid-morsali-786/QueryPort&type=Date)](https://star-history.com/#hamid-morsali-786/QueryPort&Date)

---

## 🤝 مشارکت و حق امتیاز

مشارکت شما در ارتقا و بهبود کارایی این ابزار ارزشمند است. لطفاً پیش از ارسال Pull Request موارد زیر را بررسی فرمایید:
* [راهنمای مشارکت (CONTRIBUTING.md)](CONTRIBUTING.md)
* [منشور اخلاقی (CODE_OF_CONDUCT.md)](CODE_OF_CONDUCT.md)
* [خط‌مشی امنیتی (SECURITY.md)](SECURITY.md)

### توسعه‌دهنده
طراحی و توسعه‌یافته با ❤️ توسط **[حمید مرسلی (Hamid Morsali)](https://github.com/hamid-morsali-786)**.

### لایسنس
این پروژه تحت مجوز متن‌باز **[MIT License](LICENSE)** منتشر شده است.

</div>
