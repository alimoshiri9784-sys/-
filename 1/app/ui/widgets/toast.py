"""
Toast Notification
- پیام موفقیت/خطا/هشدار به‌صورت شناور
- نمایش در گوشه‌ی بالا-راست
- ناپدید شدن خودکار پس از چند ثانیه
- انیمیشن fade + slide
"""
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QParallelAnimationGroup, Signal
)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect
)

from app.ui.icons import icon as svg_icon


class Toast(QWidget):
    """پیام شناور"""

    closed = Signal()

    # انواع
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    _CONFIG = {
        SUCCESS: {"icon": "check-circle", "color": "#10B981", "bg": "#E8F8F2"},
        ERROR:   {"icon": "alert",        "color": "#EF4444", "bg": "#FDECEC"},
        WARNING: {"icon": "alert",        "color": "#F59E0B", "bg": "#FEF3C7"},
        INFO:    {"icon": "alert",        "color": "#3B82F6", "bg": "#EFF6FF"},
    }

    def __init__(self, parent, message: str, kind: str = SUCCESS,
                 duration_ms: int = 2500):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        cfg = self._CONFIG.get(kind, self._CONFIG[SUCCESS])

        # محتوا
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(svg_icon(cfg["icon"], cfg["color"], 22).pixmap(22, 22))
        icon_lbl.setFixedSize(24, 24)

        text_lbl = QLabel(message)
        text_lbl.setStyleSheet(
            f"color: {cfg['color']}; font-size: 13px; font-weight: 600;"
        )
        text_lbl.setWordWrap(False)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        layout.addStretch()

        # استایل کل Toast
        self.setStyleSheet(f"""
            Toast {{
                background-color: {cfg['bg']};
                border: 1px solid {cfg['color']};
                border-radius: 12px;
            }}
        """)

        # سایه
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        # Opacity effect برای fade
        self._opacity = QGraphicsOpacityEffect(self)
        # نمی‌توانیم هم‌زمان graphicsEffect داشته باشیم
        # پس opacity را با QPropertyAnimation روی windowOpacity اعمال می‌کنیم
        self.setWindowOpacity(0.0)

        # اندازه
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

        # موقعیت: گوشه بالا-راست پنجره والد
        self._reposition()

        # Timer بستن
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._fade_out)
        self._close_timer.start(duration_ms)

    def _reposition(self) -> None:
        """قرار دادن Toast در گوشه‌ی بالا-راست پنجره والد"""
        parent = self.parent()
        if parent is None:
            return
        parent_geo = parent.geometry()
        parent_top_right = parent.mapToGlobal(
            QPoint(parent_geo.width(), 0)
        )
        x = parent_top_right.x() - self.width() - 24
        y = parent_top_right.y() + 80
        self.move(x, y)

    def show_with_animation(self) -> None:
        """نمایش با انیمیشن fade-in"""
        self.show()
        self._fade_in()

    def _fade_in(self) -> None:
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def _fade_out(self) -> None:
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(250)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self._finish)
        self._anim.start()

    def _finish(self) -> None:
        self.closed.emit()
        self.close()
        self.deleteLater()


# ============================================================
# توابع راحت برای استفاده در همه جا
# ============================================================

def show_success(parent: QWidget, message: str, duration_ms: int = 2500) -> None:
    _show(parent, message, Toast.SUCCESS, duration_ms)


def show_error(parent: QWidget, message: str, duration_ms: int = 3500) -> None:
    _show(parent, message, Toast.ERROR, duration_ms)


def show_warning(parent: QWidget, message: str, duration_ms: int = 3000) -> None:
    _show(parent, message, Toast.WARNING, duration_ms)


def show_info(parent: QWidget, message: str, duration_ms: int = 2500) -> None:
    _show(parent, message, Toast.INFO, duration_ms)


def _show(parent: QWidget, message: str, kind: str, duration_ms: int) -> None:
    """نمایش Toast روی پنجره اصلی"""
    # پنجره اصلی را پیدا کن
    top = parent.window()
    if top is None:
        top = parent

    toast = Toast(top, message, kind, duration_ms)
    toast.show_with_animation()