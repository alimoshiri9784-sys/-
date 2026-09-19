"""
توابع کمکی عمومی
"""
from datetime import datetime
from typing import Optional


def calculate_duration(entry: str, exit_: str) -> Optional[str]:
    """
    محاسبه مدت حضور بین دو ساعت "HH:MM"
    خروجی: "HH:MM" یا None
    """
    if not entry or not exit_:
        return None
    try:
        h1, m1 = map(int, entry.split(":"))
        h2, m2 = map(int, exit_.split(":"))
        total1 = h1 * 60 + m1
        total2 = h2 * 60 + m2
        diff = total2 - total1
        if diff < 0:
            # شیفت شبانه
            diff += 24 * 60
        hh = diff // 60
        mm = diff % 60
        return f"{hh:02d}:{mm:02d}"
    except (ValueError, AttributeError):
        return None


def duration_to_minutes(duration: Optional[str]) -> int:
    """تبدیل "HH:MM" به دقیقه"""
    if not duration:
        return 0
    try:
        h, m = map(int, duration.split(":"))
        return h * 60 + m
    except (ValueError, AttributeError):
        return 0


def minutes_to_duration(total_minutes: int) -> str:
    """تبدیل دقیقه به "HH:MM" """
    if total_minutes <= 0:
        return "00:00"
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"


def current_time_hhmm() -> str:
    """ساعت فعلی سیستم به شکل HH:MM"""
    return datetime.now().strftime("%H:%M")


def safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text)
    except (ValueError, TypeError):
        return default