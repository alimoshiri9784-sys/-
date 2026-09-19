"""
نوار بالای برنامه
- ساعت زنده از TimeService
- تاریخ شمسی + میلادی
- وضعیت شبکه
- دکمه تم
- دکمه ورود مدیر
- Thread جداگانه برای sync زمان
"""
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QSize
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton
)

from app.core.time_service import (
    TimeService, STATUS_ONLINE, STATUS_SAVED
)
from app.ui.theme import ThemeMode
from app.utils.jalali_utils import jalali_from_datetime
from app.ui.icons import icon as svg_icon


class _TimeSyncWorker(QThread):
    """Thread جداگانه برای sync زمان بدون بلاک کردن UI"""

    def __init__(self, time_service: TimeService, parent=None):
        super().__init__(parent)
        self.time_service = time_service

    def run(self) -> None:
        try:
            self.time_service.maybe_sync()
        except Exception:
            pass


class Topbar(QFrame):
    """نوار بالا"""

    themeToggleRequested = Signal()
    adminLoginRequested = Signal()
    adminLogoutRequested = Signal()

    def __init__(self, time_service: TimeService, parent=None):
        super().__init__(parent)
        self.setObjectName("Topbar")
        self.setFixedHeight(64)

        self.time_service = time_service
        self._is_admin = False
        self._theme_mode = ThemeMode.LIGHT
        self._sync_worker = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 6, 18, 6)
        layout.setSpacing(10)

        # --- عنوان صفحه ---
        self.title_label = QLabel("ثبت تردد")
        self.title_label.setObjectName("TopbarTitle")

        # --- ساعت + تاریخ ---
        self.clock_label = QLabel("--:--:--  |  ----/--/--  |  ----/--/--")
        self.clock_label.setObjectName("TopbarClock")
        self.clock_label.setLayoutDirection(Qt.LeftToRight)
        self.clock_label.setAlignment(Qt.AlignCenter)

        # --- وضعیت شبکه ---
        self.status_label = QLabel("آفلاین")
        self.status_label.setObjectName("TopbarStatus")

        # --- دکمه تم ---
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("TopbarButton")
        self.theme_btn.setFixedSize(40, 36)
        self.theme_btn.setIcon(svg_icon("moon", "#6E7480", 18))
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.setToolTip("تغییر تم روشن/تاریک")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.themeToggleRequested.emit)

        # --- دکمه ورود مدیر ---
        self.admin_btn = QPushButton("  ورود مدیر")
        self.admin_btn.setObjectName("TopbarButton")
        self.admin_btn.setIcon(svg_icon("lock", "#6E7480", 16))
        self.admin_btn.setIconSize(QSize(16, 16))
        self.admin_btn.setToolTip("ورود به حالت مدیر")
        self.admin_btn.setCursor(Qt.PointingHandCursor)
        self.admin_btn.clicked.connect(self._on_admin_clicked)

        # --- چیدمان ---
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.clock_label)
        layout.addWidget(self.theme_btn)
        layout.addWidget(self.admin_btn)

        # --- تایمر ساعت ---
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick)
        self._clock_timer.start()
        self._tick()

        # --- اولین sync در پس‌زمینه ---
        QTimer.singleShot(100, self._start_sync_in_background)

    # ---------- API ----------
    def set_title(self, text: str) -> None:
        self.title_label.setText(text)

    def set_admin_state(self, is_admin: bool) -> None:
        """تغییر وضعیت دکمه ورود/خروج مدیر"""
        self._is_admin = is_admin

        if is_admin:
            self.admin_btn.setText("  خروج مدیر")
            self.admin_btn.setObjectName("Primary")
            self.admin_btn.setIcon(svg_icon("unlock", "#FFFFFF", 16))
        else:
            self.admin_btn.setText("  ورود مدیر")
            self.admin_btn.setObjectName("TopbarButton")
            self.admin_btn.setIcon(svg_icon("lock", "#6E7480", 16))

        # اعمال مجدد استایل برای تغییر objectName
        self.admin_btn.style().unpolish(self.admin_btn)
        self.admin_btn.style().polish(self.admin_btn)

    def set_theme_icon(self, mode: ThemeMode) -> None:
        """تغییر آیکون دکمه تم"""
        self._theme_mode = mode
        if mode == ThemeMode.DARK:
            self.theme_btn.setIcon(svg_icon("sun", "#FF6B35", 18))
        else:
            self.theme_btn.setIcon(svg_icon("moon", "#6E7480", 18))

    # ---------- داخلی ----------
    def _on_admin_clicked(self):
        if self._is_admin:
            self.adminLogoutRequested.emit()
        else:
            self.adminLoginRequested.emit()

    def _start_sync_in_background(self) -> None:
        """شروع Thread برای sync زمان"""
        if self._sync_worker is not None and self._sync_worker.isRunning():
            return
        self._sync_worker = _TimeSyncWorker(self.time_service, self)
        self._sync_worker.finished.connect(self._on_sync_finished)
        self._sync_worker.start()

    def _on_sync_finished(self) -> None:
        """پس از پایان sync، مجدداً برنامه‌ریزی کن"""
        self._update_status_label()
        QTimer.singleShot(30 * 60 * 1000, self._start_sync_in_background)

    def _update_status_label(self) -> None:
        """بروزرسانی متن وضعیت شبکه"""
        status = self.time_service.last_status
        msg = self.time_service.last_message

        if status == STATUS_ONLINE:
            self.status_label.setText("  آنلاین")
            self.status_label.setStyleSheet("color: #10B981;")
        elif status == STATUS_SAVED:
            self.status_label.setText("  زمان ذخیره‌شده")
            self.status_label.setStyleSheet("color: #F59E0B;")
        else:
            self.status_label.setText("  آفلاین")
            self.status_label.setStyleSheet("color: #EF4444;")

        self.status_label.setToolTip(msg)

    def _tick(self) -> None:
        """هر ثانیه: ساعت + تاریخ شمسی + تاریخ میلادی"""
        ts = self.time_service.get_tehran_now()
        now = ts.tehran_now

        time_text = now.strftime("%H:%M:%S")
        jalali_date = jalali_from_datetime(now)
        gregorian_date = now.strftime("%Y/%m/%d")

        self.clock_label.setText(
            f"{time_text}   |   {jalali_date}   |   {gregorian_date}"
        )

        self._update_status_label()