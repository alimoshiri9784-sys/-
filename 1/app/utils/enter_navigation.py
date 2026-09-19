"""
ناوبری با Enter فقط در ویجت‌های ورودی
- دکمه‌ها: Enter = کلیک (بدون تغییر)
- QLineEdit / QComboBox / SpinBox / ورودی‌های سفارشی: Enter = ویجت بعدی
- اگر ویجت returnPressed متصل دارد: همان اجرا می‌شود
- QTextEdit / QPlainTextEdit: خط جدید (بدون تغییر)
"""
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QLineEdit, QComboBox, QAbstractSpinBox,
    QPushButton, QTextEdit, QPlainTextEdit, QWidget
)


# فقط این نوع ویجت‌ها Enter → بعدی
_INPUT_TYPES = (QLineEdit, QComboBox, QAbstractSpinBox)


class _EnterNavigation(QObject):
    """فیلتر سراسری Enter"""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.KeyPress:
            return False
        if event.key() not in (Qt.Key_Return, Qt.Key_Enter):
            return False

        # 1) QTextEdit / QPlainTextEdit → خط جدید
        if isinstance(obj, (QTextEdit, QPlainTextEdit)):
            return False

        # 2) اگر ویجت خودش returnPressed متصل دارد → اجرا شود
        if isinstance(obj, QLineEdit):
            try:
                if obj.receivers(obj.returnPressed) > 0:
                    return False
            except Exception:
                pass

        # 3) فقط ویجت‌های ورودی → ناوبری
        if isinstance(obj, _INPUT_TYPES):
            backward = bool(event.modifiers() & Qt.ShiftModifier)
            key = Qt.Key_Backtab if backward else Qt.Key_Tab
            tab_event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
            QApplication.sendEvent(obj, tab_event)
            return True

        # 4) بقیه (دکمه‌ها، جداول و ...) → بدون تغییر
        return False


def install_enter_navigation(app: QApplication) -> None:
    """نصب فیلتر ناوبری Enter"""
    filter_obj = _EnterNavigation(app)
    app.installEventFilter(filter_obj)
    app._enter_navigation_filter = filter_obj   # جلوگیری از GC