"""
سرویس ساعت تهران
- اتصال به API زمان با دو لینک Fallback (فقط هر ۳۰ دقیقه یک‌بار)
- ذخیره Offset برای حالت آفلاین
- محاسبه زمان جاری به‌صورت محلی و سریع
"""
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests

from app.core.config import TIME_API_URLS
from app.core.database import Database

_SETTING_OFFSET = "time_offset_seconds"
_SETTING_LAST_SYNC = "time_last_sync_ts"

STATUS_ONLINE = "online"
STATUS_SAVED = "saved"
STATUS_OFFLINE = "offline"

TEHRAN_FALLBACK_OFFSET = 3 * 3600 + 30 * 60

# فاصله بین دو تلاش برای بروزرسانی از API (ثانیه)
SYNC_INTERVAL_SECONDS = 30 * 60   # ۳۰ دقیقه


@dataclass
class TimeStatus:
    status: str
    tehran_now: datetime
    message: str = ""


class TimeService:
    """سرویس مدیریت زمان تهران (بدون بلاک کردن UI)"""

    def __init__(self, db: Database, request_timeout: float = 3.0):
        self.db = db
        self.timeout = request_timeout
        self._cached_offset: Optional[int] = self._load_offset()
        self._last_status: str = STATUS_OFFLINE
        self._last_message: str = ""

        # زمان آخرین sync موفق (Unix)
        last_sync_str = db.get_setting(_SETTING_LAST_SYNC)
        self._last_sync_ts: float = float(last_sync_str) if last_sync_str else 0.0

        # اگر offset ذخیره‌شده داریم، وضعیت را saved قرار بده
        if self._cached_offset is not None:
            self._last_status = STATUS_SAVED
            self._last_message = "استفاده از آخرین زمان ذخیره‌شده"

    # ---------- Offset ----------
    def _load_offset(self) -> Optional[int]:
        val = self.db.get_setting(_SETTING_OFFSET)
        if val is None:
            return None
        try:
            return int(val)
        except ValueError:
            return None

    def _save_offset(self, offset_seconds: int) -> None:
        self._cached_offset = offset_seconds
        self._last_sync_ts = time.time()
        self.db.set_setting(_SETTING_OFFSET, str(offset_seconds))
        self.db.set_setting(_SETTING_LAST_SYNC, str(int(self._last_sync_ts)))

    # ---------- دریافت از API ----------
    def _try_fetch_from_api(self) -> Optional[int]:
        for url in TIME_API_URLS:
            try:
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code != 200:
                    continue
                data = resp.json()

                if "utc_offset" in data and "datetime" in data:
                    off_str = data["utc_offset"]
                    sign = 1 if off_str[0] == "+" else -1
                    hh, mm = off_str[1:].split(":")
                    return sign * (int(hh) * 3600 + int(mm) * 60)

                if "currentUtcOffset" in data and "seconds" in data["currentUtcOffset"]:
                    return int(data["currentUtcOffset"]["seconds"])

            except (requests.RequestException, ValueError, KeyError):
                continue
        return None

    def maybe_sync(self) -> None:
        """
        اگر بیش از SYNC_INTERVAL_SECONDS از آخرین sync گذشته باشد،
        تلاش می‌کند زمان را از API بگیرد.
        ⚠️ این متد در Thread جداگانه صدا زده می‌شود تا UI بلاک نشود.
        """
        if time.time() - self._last_sync_ts < SYNC_INTERVAL_SECONDS:
            return
        offset = self._try_fetch_from_api()
        if offset is not None:
            self._save_offset(offset)
            self._last_status = STATUS_ONLINE
            self._last_message = "ساعت از API آنلاین دریافت شد"
        else:
            if self._cached_offset is not None:
                self._last_status = STATUS_SAVED
                self._last_message = "استفاده از آخرین زمان ذخیره‌شده"
            else:
                self._last_status = STATUS_OFFLINE
                self._last_message = "هشدار: ساعت سیستم استفاده می‌شود"

    # ---------- زمان جاری (سریع، بدون HTTP) ----------
    def get_tehran_now(self) -> TimeStatus:
        utc_now = datetime.utcnow()

        if self._cached_offset is not None:
            return TimeStatus(
                status=self._last_status,
                tehran_now=utc_now + timedelta(seconds=self._cached_offset),
                message=self._last_message,
            )

        # اولین اجرا و بدون offset
        return TimeStatus(
            status=STATUS_OFFLINE,
            tehran_now=utc_now + timedelta(seconds=TEHRAN_FALLBACK_OFFSET),
            message="هشدار: ساعت سیستم استفاده می‌شود",
        )

    # ---------- کمک ----------
    def get_status_label(self) -> Tuple[str, str]:
        if self._last_status == STATUS_ONLINE:
            return "🟢", "آنلاین"
        if self._last_status == STATUS_SAVED:
            return "🟡", "زمان ذخیره‌شده"
        return "🔴", "آفلاین"

    @property
    def last_status(self) -> str:
        return self._last_status

    @property
    def last_message(self) -> str:
        return self._last_message