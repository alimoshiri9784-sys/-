"""
اعتبارسنجی‌های عمومی
"""
from typing import Optional


def is_valid_national_code(code: str) -> bool:
    """
    اعتبارسنجی کد ملی ۱۰ رقمی ایران با الگوریتم checksum
    """
    if not code:
        return True  # اختیاری
    code = code.strip()
    if not code.isdigit() or len(code) != 10:
        return False
    if len(set(code)) == 1:  # مثل 1111111111
        return False
    check = int(code[9])
    s = sum(int(code[i]) * (10 - i) for i in range(9))
    r = s % 11
    return (r < 2 and check == r) or (r >= 2 and check == 11 - r)


def is_valid_personnel_code(code: str) -> bool:
    """کد پرسنلی: فقط عدد، حداقل ۱ رقم"""
    if not code:
        return False
    return code.strip().isdigit() and len(code.strip()) >= 1


def is_valid_time(hh: int, mm: int) -> bool:
    return 0 <= hh <= 23 and 0 <= mm <= 59


def normalize_digits(text: str) -> str:
    """
    تبدیل اعداد فارسی/عربی به انگلیسی
    """
    if not text:
        return text
    trans = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )
    return text.translate(trans)