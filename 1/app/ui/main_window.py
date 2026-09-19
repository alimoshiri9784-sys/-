"""
پنجره اصلی
- Sidebar (منوی کناری)
- Topbar
- QStackedWidget برای ۵ صفحه
- Idle Timeout برای مدیر (۵ دقیقه)
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QMessageBox,
    QInputDialog, QLineEdit, QTableWidget
)

from app.core.auth import AuthManager
from app.core.config import APP_NAME, ADMIN_IDLE_TIMEOUT_SECONDS
from app.core.database import Database
from app.core.time_service import TimeService
from app.ui.theme import ThemeMode, apply_theme
from app.ui.widgets.topbar import Topbar
from app.ui.icons import icon as svg_icon
from PySide6.QtCore import Qt, QTimer, Signal, QSize


class MainWindow(QMainWindow):
    """پنجره اصلی برنامه"""

    def __init__(self, db: Database, auth: AuthManager, time_service: TimeService):
        super().__init__()
        self.db = db
        self.auth = auth
        self.time_service = time_service

        self._is_admin = False
        self._theme_mode = ThemeMode.LIGHT
        self._pages = []
        self._nav_buttons = []

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 750)

        self._build_ui()
        self._apply_theme()
        self._setup_idle_timer()
        self._lock_admin_pages()

    # ---------- ساخت UI ----------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        self.topbar = Topbar(self.time_service)
        self.topbar.themeToggleRequested.connect(self._toggle_theme)
        self.topbar.adminLoginRequested.connect(self._request_admin_login)
        self.topbar.adminLogoutRequested.connect(self._admin_logout)
        root.addWidget(self.topbar)

        # بدنه: Sidebar + Pages
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        body.addWidget(self.sidebar)

        # صفحات
        self.stack = QStackedWidget()
        self._build_pages()
        body.addWidget(self.stack, 1)

        root.addLayout(body)

    def _build_sidebar(self) -> QFrame:
        from PySide6.QtWidgets import QSizePolicy

        sb = QFrame()
        sb.setObjectName("Sidebar")
        sb.setFixedWidth(260)

        layout = QVBoxLayout(sb)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # --- عنوان با آیکون ---
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setContentsMargins(12, 12, 12, 6)

        title = QLabel("داروخانه دکتر مشیری راد")
        title.setObjectName("SidebarTitle")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        title_icon = QLabel()
        title_icon.setPixmap(svg_icon("database", "#FF6B35", 22).pixmap(22, 22))
        title_icon.setFixedWidth(24)

        title_row.addStretch(1)
        title_row.addWidget(title)
        title_row.addWidget(title_icon)
        layout.addLayout(title_row)

        layout.addSpacing(10)

        # --- آیتم‌های منو ---
        items = [
            ("clock",    "ثبت تردد",       0, False),
            ("users",    "مدیریت کاربر",   1, True),
            ("chart",    "گزارش",          2, True),
            ("database", "مدیریت تردد",    3, True),
            ("settings", "تنظیمات",        4, True),
        ]

        for icon_name, text, index, needs_admin in items:
            widget = self._make_sidebar_item(icon_name, text, index, needs_admin)
            layout.addWidget(widget)

        layout.addStretch(1)

        self._nav_buttons[0][0].setChecked(True)
        self._update_sidebar_styles()
        return sb

    def _make_sidebar_item(self, icon_name: str, text: str,
                           index: int, needs_admin: bool):
        """ساخت یک آیتم سفارشی Sidebar"""
        from PySide6.QtWidgets import QSizePolicy

        btn = QPushButton()
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # داخل دکمه، یک layout با آیکون و متن می‌گذاریم
        h = QHBoxLayout(btn)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)

        # آیکون
        icon_lbl = QLabel()
        icon_lbl.setPixmap(svg_icon(icon_name, "#C9CDD4", 20).pixmap(20, 20))
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        # متن
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(
            "background: transparent; border: none; "
            "color: #C9CDD4; font-size: 13px; font-weight: 600;"
        )
        text_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        # چیدمان RTL: اول stretch (چپ)، بعد متن، بعد آیکون (راست)
        h.addStretch(1)
        h.addWidget(text_lbl)
        h.addWidget(icon_lbl)

        # بروزرسانی رنگ متن/آیکون هنگام toggle
        btn.toggled.connect(
            lambda checked, b=btn, t=text_lbl, i=icon_lbl, ic=icon_name:
            self._update_item_style(b, t, i, ic, checked)
        )

        btn.clicked.connect(lambda _, i=index: self._switch_page(i))
        self._nav_buttons.append((btn, needs_admin))
        return btn

    def _update_item_style(self, btn, text_lbl, icon_lbl, icon_name, checked):
        """رنگ متن و آیکون بر اساس حالت انتخاب"""
        if checked:
            text_lbl.setStyleSheet(
                "background: transparent; border: none; "
                "color: #FFFFFF; font-size: 13px; font-weight: 700;"
            )
            icon_lbl.setPixmap(svg_icon(icon_name, "#FFFFFF", 20).pixmap(20, 20))
        else:
            text_lbl.setStyleSheet(
                "background: transparent; border: none; "
                "color: #C9CDD4; font-size: 13px; font-weight: 600;"
            )
            icon_lbl.setPixmap(svg_icon(icon_name, "#C9CDD4", 20).pixmap(20, 20))

    def _update_sidebar_styles(self):
        """اعمال رنگ پیش‌فرض روی همه آیتم‌های sidebar"""
        for btn, _ in self._nav_buttons:
            # layout داخل دکمه را می‌گیریم
            h = btn.layout()
            if h is None:
                continue
            # آیتم آخر (متن) و یکی مانده به آخر (آیکون)
            for i in range(h.count()):
                w = h.itemAt(i).widget()
                if w is None:
                    continue
                # فقط وقتی checked=False
                if not btn.isChecked():
                    pass   # رنگ پیش‌فرض در QSS اعمال می‌شود


    def _build_pages(self) -> None:
        from app.ui.pages.attendance_page import AttendancePage
        from app.ui.pages.users_page import UsersPage
        from app.ui.pages.reports_page import ReportsPage
        from app.ui.pages.records_page import RecordsPage
        from app.ui.pages.settings_page import SettingsPage

        self.page_attendance = AttendancePage(self.db, self.time_service)
        self.page_users = UsersPage(self.db)
        self.page_reports = ReportsPage(self.db, self.time_service)
        self.page_records = RecordsPage(self.db)
        self.page_settings = SettingsPage(self.db, self.auth)

        for p in (self.page_attendance, self.page_users, self.page_reports,
                  self.page_records, self.page_settings):
            self.stack.addWidget(p)
            self._pages.append(p)

        # ⭐ تنظیم ارتفاع ردیف جدول‌ها
        self._style_tables()

        # اتصال signals
        if hasattr(self.page_users, "dataChanged"):
            self.page_users.dataChanged.connect(self.page_attendance.reload_today_table)
            self.page_users.dataChanged.connect(self.page_records.reload_table)
        if hasattr(self.page_records, "dataChanged"):
            self.page_records.dataChanged.connect(self.page_attendance.reload_today_table)
        if hasattr(self.page_attendance, "dataChanged"):
            self.page_attendance.dataChanged.connect(self.page_records.reload_table)

    def _style_tables(self) -> None:
        """اعمال استایل به همه جدول‌ها در همه صفحات"""
        from PySide6.QtWidgets import QTableWidget, QApplication
        
        # روی همه ویجت‌های برنامه (نه فقط صفحات)
        app = QApplication.instance()
        if app is None:
            return
        for table in app.allWidgets():
            if isinstance(table, QTableWidget):
                self._style_single_table(table)

    def _style_single_table(self, table) -> None:
        """استایل یک جدول"""
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(44)
        vh.setMinimumSectionSize(40)
        
        hh = table.horizontalHeader()
        hh.setFixedHeight(48)
        hh.setDefaultAlignment(Qt.AlignCenter)
        
        table.setShowGrid(False)
        try:
            table.setFrameShape(QTableWidget.NoFrame)
        except AttributeError:
            pass

    # ---------- ناوبری ----------
    def _switch_page(self, index: int) -> None:
        btn, needs_admin = self._nav_buttons[index]
        if needs_admin and not self._is_admin:
            QMessageBox.warning(
                self, "دسترسی محدود",
                "این صفحه فقط برای مدیر قابل دسترسی است.\n"
                "ابتدا از دکمه «ورود مدیر» در نوار بالا استفاده کنید."
            )
            self._sync_sidebar_checks()
            return

        self.stack.setCurrentIndex(index)
        self.topbar.set_title(btn.text().strip())

    def _sync_sidebar_checks(self) -> None:
        current = self.stack.currentIndex()
        for i, (btn, _) in enumerate(self._nav_buttons):
            btn.setChecked(i == current)

    # ---------- قفل صفحات مدیر ----------
    def _lock_admin_pages(self) -> None:
        for i, (btn, needs_admin) in enumerate(self._nav_buttons):
            if needs_admin:
                btn.setEnabled(False)
                btn.setToolTip("🔒 نیاز به ورود مدیر")
            else:
                btn.setEnabled(True)
                btn.setToolTip("")
        if self.stack.currentIndex() != 0:
            self.stack.setCurrentIndex(0)
            self._nav_buttons[0][0].setChecked(True)
            self.topbar.set_title(self._nav_buttons[0][0].text().strip())

    def _unlock_admin_pages(self) -> None:
        for btn, needs_admin in self._nav_buttons:
            if needs_admin:
                btn.setEnabled(True)
                btn.setToolTip("")

    # ---------- ورود/خروج مدیر ----------
    def _request_admin_login(self) -> None:
        password, ok = QInputDialog.getText(
            self, "ورود مدیر", "رمز مدیر را وارد کنید:",
            QLineEdit.Password
        )
        if not ok:
            return
        if self.auth.check_password(password):
            self._is_admin = True
            self.topbar.set_admin_state(True)
            self._unlock_admin_pages()
            self._restart_idle_timer()
            QMessageBox.information(self, "خوش آمدید", "دسترسی مدیر فعال شد.")
        else:
            QMessageBox.critical(self, "خطا", "رمز اشتباه است.")

    def _admin_logout(self) -> None:
        self._is_admin = False
        self.topbar.set_admin_state(False)
        self._lock_admin_pages()
        self._stop_idle_timer()
        QMessageBox.information(self, "خروج", "دسترسی مدیر غیرفعال شد.")

    # ---------- Idle Timeout ----------
    def _setup_idle_timer(self) -> None:
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(ADMIN_IDLE_TIMEOUT_SECONDS * 1000)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

    def _restart_idle_timer(self) -> None:
        if self._is_admin:
            self._idle_timer.start()

    def _stop_idle_timer(self) -> None:
        self._idle_timer.stop()

    def _on_idle_timeout(self) -> None:
        if not self._is_admin:
            return
        self._is_admin = False
        self.topbar.set_admin_state(False)
        self._lock_admin_pages()
        QMessageBox.information(
            self, "قفل خودکار",
            "به دلیل ۵ دقیقه بی‌کاری، دسترسی مدیر قفل شد."
        )

    # ---------- تم ----------
    def _toggle_theme(self) -> None:
        self._theme_mode = (
            ThemeMode.DARK if self._theme_mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        )
        self._apply_theme()

    def _apply_theme(self) -> None:
        from PySide6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), self._theme_mode)
        self.topbar.set_theme_icon(self._theme_mode)

    # ---------- رویدادها ----------
    def mousePressEvent(self, event):  # noqa: N802
        self._restart_idle_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):  # noqa: N802
        self._restart_idle_timer()
        super().keyPressEvent(event)