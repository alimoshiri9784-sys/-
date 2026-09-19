"""
ابزارهای تاریخ شمسی
تبدیل، اعتبارسنجی و فرمت
"""
from datetime import datetime, date
from typing import Optional, Tuple

import jdatetime


# ---------- اعتبارسنجی اجزا ----------
def is_valid_year(y: int) -> bool:
    return 1300 <= y <= 1500


def is_valid_month(m: int) -> bool:
    return 1 <= m <= 12


def is_valid_day(y: int, m: int, d: int) -> bool:
    """اعتبارسنجی روز با توجه به ماه و سال شمسی"""
    if not is_valid_year(y) or not is_valid_month(m):
        return False
    if d < 1 or d > 31:
        return False
    try:
        jdatetime.date(y, m, d)
        return True
    except ValueError:
        return False


# ---------- تبدیل به رشته ----------
def format_jalali(y: int, m: int, d: int) -> str:
    """خروجی: 1403/05/12 (با صفر پیشوند)"""
    return f"{y:04d}/{m:02d}/{d:02d}"


def parse_jalali(text: str) -> Optional[Tuple[int, int, int]]:
    """
    رشته 1403/05/12 را به تاپل (y, m, d) تبدیل می‌کند.
    در صورت نامعتبر بودن None برمی‌گرداند.
    """
    if not text:
        return None
    parts = text.strip().replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    if not is_valid_day(y, m, d):
        return None
    return y, m, d


# ---------- تبدیل با میلادی ----------
def gregorian_to_jalali(g_date: date) -> str:
    j = jdatetime.date.fromgregorian(date=g_date)
    return format_jalali(j.year, j.month, j.day)


def jalali_to_gregorian(j_str: str) -> Optional[date]:
    parsed = parse_jalali(j_str)
    if not parsed:
        return None
    y, m, d = parsed
    try:
        g = jdatetime.date(y, m, d).togregorian()
        return g
    except Exception:
        return None


# ---------- امروز ----------
def today_jalali() -> str:
    """تاریخ امروز به شمسی بر اساس زمان سیستم (برای fallback)"""
    today = date.today()
    return gregorian_to_jalali(today)


def jalali_from_datetime(dt: datetime) -> str:
    """تاریخ شمسی از یک datetime (مثلاً زمان تهران)"""
    j = jdatetime.date.fromgregorian(date=dt.date())
    return format_jalali(j.year, j.month, j.day)