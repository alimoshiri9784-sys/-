"""
احراز هویت مدیر — ذخیره رمز به‌صورت SHA-256 + Salt
"""
import hashlib
import hmac
import os
import base64
from typing import Optional

from app.core.config import DEFAULT_ADMIN_PASSWORD
from app.core.database import Database

_SETTING_KEY = "admin_password_hash"


class AuthManager:
    """مدیریت رمز مدیر"""

    def __init__(self, db: Database):
        self.db = db
        self._ensure_default_password()

    # ---------- Salt + Hash ----------
    @staticmethod
    def _hash_password(password: str, salt: bytes) -> str:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return base64.b64encode(salt + dk).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        try:
            data = base64.b64decode(stored.encode("utf-8"))
            salt, expected = data[:16], data[16:]
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
            return hmac.compare_digest(dk, expected)
        except Exception:
            return False

    def _ensure_default_password(self) -> None:
        if not self.db.get_setting(_SETTING_KEY):
            self.set_password(DEFAULT_ADMIN_PASSWORD)

    def set_password(self, new_password: str) -> None:
        salt = os.urandom(16)
        self.db.set_setting(_SETTING_KEY, self._hash_password(new_password, salt))

    def check_password(self, password: str) -> bool:
        stored = self.db.get_setting(_SETTING_KEY)
        if not stored:
            return False
        return self._verify_password(password, stored)