"""
انیمیشن‌های ظریف
- سایه نرم برای کارت‌ها
- Fade-in هنگام نمایش
- Pulse برای هشدارها
"""
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def add_shadow(widget: QWidget,
               blur: int = 20,
               offset_y: int = 4,
               color_alpha: int = 25) -> None:
    """
    افزودن سایه نرم به ویجت
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, color_alpha))
    shadow.setOffset(0, offset_y)
    widget.setGraphicsEffect(shadow)


def apply_card_shadows(root_widget: QWidget) -> None:
    """
    اعمال سایه به همه‌ی کارت‌ها و GroupBoxها در یک صفحه
    """
    from PySide6.QtWidgets import QFrame, QGroupBox

    for frame in root_widget.findChildren(QFrame):
        if frame.objectName() == "Card":
            add_shadow(frame, blur=24, offset_y=4, color_alpha=22)

    for gb in root_widget.findChildren(QGroupBox):
        add_shadow(gb, blur=18, offset_y=3, color_alpha=18)


def fade_in(widget: QWidget, duration: int = 280) -> None:
    """Fade-in ملایم برای ویجت"""
    widget.setWindowOpacity(0.0)

    anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    # حفظ رفرنس
    widget._fade_anim = anim
    anim.start()