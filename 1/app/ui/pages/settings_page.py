"""
صفحه ۵: تنظیمات
- تغییر رمز مدیر (رمز فعلی + رمز جدید + تکرار)
- اطلاعات سیستم
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QGroupBox, QSizePolicy
)

from app.core.auth import AuthManager
from app.core.database import Database
from app.core.config import (
    APP_NAME, APP_VERSION, DB_PATH, MAX_EMPLOYEES
)
from app.utils.validators import normalize_digits
from app.ui.icons import icon as svg_icon
from app.ui.widgets.toast import show_success, show_error, show_warning
from app.ui.widgets.animations import apply_card_shadows


class SettingsPage(QWidget):
    """صفحه تنظیمات"""

    def __init__(self, db: Database, auth: AuthManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.auth = auth

        self._build_ui()
        apply_card_shadows(self)

    # ==================== UI ====================
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ← بدون عنوان «تنظیمات»

        # ---------- کارت تغییر رمز (عرض محدود) ----------
        wrap = QHBoxLayout()
        wrap.addStretch(1)

        pwd_card = QFrame()
        pwd_card.setObjectName("Card")
        pwd_card.setMaximumWidth(620)          # ← کوچک‌تر
        pwd_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        pl = QVBoxLayout(pwd_card)
        pl.setContentsMargins(28, 22, 28, 22)
        pl.setSpacing(14)

        # عنوان کارت
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("🔐  تغییر رمز مدیر")
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #1A1D21;"
        )
        title_row.addWidget(title_lbl)
        title_row.addStretch(1)
        pl.addLayout(title_row)

        # فرم: برچسب راست + ورودی (لیبل بالا)
        def field(label_text, widget):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(4)

            lbl = QLabel(label_text)
            lbl.setObjectName("FieldLabel")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            v.addWidget(lbl)
            v.addWidget(widget)
            return w

        self.inp_current = QLineEdit()
        self.inp_current.setEchoMode(QLineEdit.Password)
        self.inp_current.setLayoutDirection(Qt.LeftToRight)
        self.inp_current.setMaxLength(64)
        self.inp_current.setMinimumHeight(42)
        pl.addWidget(field("رمز فعلی", self.inp_current))

        self.inp_new = QLineEdit()
        self.inp_new.setEchoMode(QLineEdit.Password)
        self.inp_new.setLayoutDirection(Qt.LeftToRight)
        self.inp_new.setMaxLength(64)
        self.inp_new.setMinimumHeight(42)
        pl.addWidget(field("رمز جدید", self.inp_new))

        self.inp_confirm = QLineEdit()
        self.inp_confirm.setEchoMode(QLineEdit.Password)
        self.inp_confirm.setLayoutDirection(Qt.LeftToRight)
        self.inp_confirm.setMaxLength(64)
        self.inp_confirm.setMinimumHeight(42)
        pl.addWidget(field("تکرار رمز جدید", self.inp_confirm))

        # راهنما
        hint = QLabel("رمز باید حداقل ۴ کاراکتر باشد و به‌صورت هش‌شده ذخیره می‌شود.")
        hint.setStyleSheet("color: #9099A5; font-size: 11px;")
        hint.setAlignment(Qt.AlignRight)
        pl.addWidget(hint)

        # دکمه‌ها — راست‌چین
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch(1)

        self.btn_clear = QPushButton("  پاک‌سازی فرم")
        self.btn_clear.setIcon(svg_icon("trash", "#6E7480", 14))
        self.btn_clear.setIconSize(self.btn_clear.iconSize())
        self.btn_clear.setMinimumHeight(42)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_form)

        self.btn_save = QPushButton("  ذخیره رمز جدید")
        self.btn_save.setObjectName("Primary")
        self.btn_save.setIcon(svg_icon("save", "#FFFFFF", 14))
        self.btn_save.setMinimumHeight(42)
        self.btn_save.setMinimumWidth(170)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._change_password)

        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_save)
        pl.addLayout(btn_row)

        wrap.addWidget(pwd_card)
        wrap.addStretch(1)
        root.addLayout(wrap)

        # ---------- کارت اطلاعات سیستم (عرض محدود) ----------
        info_wrap = QHBoxLayout()
        info_wrap.addStretch(1)

        info_card = QFrame()
        info_card.setObjectName("Card")
        info_card.setMaximumWidth(620)          # ← هم‌عرض کارت بالا
        info_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        il = QVBoxLayout(info_card)
        il.setContentsMargins(28, 22, 28, 22)
        il.setSpacing(12)

        info_title = QLabel("ℹ️  اطلاعات سیستم")
        info_title.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #1A1D21;"
        )
        info_title.setAlignment(Qt.AlignRight)
        il.addWidget(info_title)

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(16)
        info_grid.setVerticalSpacing(8)

        items = [
            ("نام برنامه:", APP_NAME),
            ("نسخه:", APP_VERSION),
            ("مسیر دیتابیس:", str(DB_PATH)),
            ("حداکثر پرسنل فعال:", str(MAX_EMPLOYEES)),
            ("زمان قفل خودکار مدیر:", "۵ دقیقه بی‌کاری"),
        ]
        for i, (k, v) in enumerate(items):
            lk = QLabel(k)
            lk.setStyleSheet("color: #6E7480; font-size: 12px;")
            lk.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            lv = QLabel(v)
            lv.setStyleSheet(
                "color: #1A1D21; font-size: 12px; font-weight: 600;"
            )
            lv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lv.setTextInteractionFlags(Qt.TextSelectableByMouse)

            info_grid.addWidget(lk, i, 0)
            info_grid.addWidget(lv, i, 1)

        info_grid.setColumnStretch(1, 1)
        il.addLayout(info_grid)

        info_wrap.addWidget(info_card)
        info_wrap.addStretch(1)
        root.addLayout(info_wrap)

        root.addStretch(1)

    # ==================== تغییر رمز ====================
    def _change_password(self) -> None:
        current = normalize_digits(self.inp_current.text())
        new = normalize_digits(self.inp_new.text())
        confirm = normalize_digits(self.inp_confirm.text())

        if not current:
            show_warning(self, "رمز فعلی را وارد کنید")
            self.inp_current.setFocus()
            return

        if not self.auth.check_password(current):
            show_error(self, "رمز فعلی اشتباه است")
            self.inp_current.setFocus()
            self.inp_current.selectAll()
            return

        if len(new) < 4:
            show_warning(self, "رمز جدید باید حداقل ۴ کاراکتر باشد")
            self.inp_new.setFocus()
            return

        if new != confirm:
            show_warning(self, "رمز جدید و تکرار آن یکسان نیستند")
            self.inp_confirm.setFocus()
            self.inp_confirm.selectAll()
            return

        self.auth.set_password(new)
        show_success(self, "رمز مدیر با موفقیت تغییر کرد")
        self._clear_form()

    # ==================== پاک‌سازی ====================
    def _clear_form(self) -> None:
        self.inp_current.clear()
        self.inp_new.clear()
        self.inp_confirm.clear()
        self.inp_current.setFocus()