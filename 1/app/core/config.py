"""
تنظیمات ثابت پروژه
مسیرها، پیش‌فرض‌ها و مقادیر پایه
"""
from pathlib import Path

# ---------- مسیرها ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
DB_PATH = DATA_DIR / "pharmacy_attendance.db"

# اطمینان از وجود پوشه data
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------- پیش‌فرض‌ها ----------
DEFAULT_ADMIN_PASSWORD = "1234"
MAX_EMPLOYEES = 10
ADMIN_IDLE_TIMEOUT_SECONDS = 5 * 60   # ۵ دقیقه

# ---------- API های زمان ----------
TIME_API_URLS = [
    "https://worldtimeapi.org/api/timezone/Asia/Tehran",
    "https://timeapi.io/api/Time/current/zone?timeZone=Asia/Tehran",
]

# ---------- اطلاعات برنامه ----------
APP_NAME = "سیستم ثبت رفت و آمد پرسنل داروخانه"
APP_VERSION = "1.0.0"
ORG_NAME = "Pharmacy"

# ---------- تنظیمات گزارش ----------
RECORDS_PAGE_LIMIT = 500   # تعداد رکوردهای نمایشی در صفحه مدیریت تردد

# ---------- فونت PDF ----------
PDF_FONT_NAME = "Vazirmatn"
PDF_FONT_PATH = FONTS_DIR / "Vazirmatn-Regular.ttf"
"""
تنظیمات ثابت پروژه
مسیرها، پیش‌فرض‌ها و مقادیر پایه + پالت رنگ
"""
from pathlib import Path

# ---------- مسیرها ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
DB_PATH = DATA_DIR / "pharmacy_attendance.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------- پیش‌فرض‌ها ----------
DEFAULT_ADMIN_PASSWORD = "1234"
MAX_EMPLOYEES = 10
ADMIN_IDLE_TIMEOUT_SECONDS = 5 * 60

# ---------- API های زمان ----------
TIME_API_URLS = [
    "https://worldtimeapi.org/api/timezone/Asia/Tehran",
    "https://timeapi.io/api/Time/current/zone?timeZone=Asia/Tehran",
]

# ---------- اطلاعات برنامه ----------
APP_NAME = "سیستم ثبت رفت و آمد پرسنل داروخانه"
APP_VERSION = "1.0.0"
ORG_NAME = "Pharmacy"

# ---------- تنظیمات گزارش ----------
RECORDS_PAGE_LIMIT = 500

# ---------- فونت PDF ----------
PDF_FONT_NAME = "Vazirmatn"
PDF_FONT_PATH = FONTS_DIR / "Vazirmatn-Regular.ttf"

# ---------- تایپوگرافی ----------
# فونت‌های جایگزین به ترتیب اولویت
FONT_FAMILY_STACK = '"Vazirmatn", "IRANSans", "Segoe UI", "Tahoma", sans-serif'

# اندازه‌های فونت
FONT_SIZE_BASE = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_TITLE = 20
FONT_SIZE_H1 = 17
FONT_SIZE_BUTTON = 13
FONT_SIZE_CLOCK = 14

# ---------- Radius ----------
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 16
RADIUS_XL = 20