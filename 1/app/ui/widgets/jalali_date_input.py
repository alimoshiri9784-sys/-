"""
ورودی تاریخ شمسی: [YYYY] / [MM] / [DD]
- پرش خودکار بین کادرها
- اعتبارسنجی
- Enter برای رفتن به ویجت بعدی
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit

from app.utils.validators import normalize_digits
from app.utils.jalali_utils import is_valid_day, is_valid_year, is_valid_month


class _DigitBox(QLineEdit):
    """کادر عدد با پرش خودکار"""

    filled = Signal()
    nextRequested = Signal()

    def __init__(self, max_length: int, max_value: int, parent=None):
        super().__init__(parent)
        self.max_length = max_length
        self.max_value = max_value
        self.setObjectName("DatePart")            # ← ← ← اضافه شد
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAlignment(Qt.AlignCenter)
        self.setMaxLength(max_length)
        self.setFixedWidth(56 if max_length == 4 else 44)
        self.setMinimumHeight(36)                 # ← ← ← اضافه شد
        self.setValidator(QIntValidator(0, max_value, self))
        self.textChanged.connect(self._on_changed)

    def _on_changed(self, text: str) -> None:
        norm = normalize_digits(text)
        if norm != text:
            self.blockSignals(True)
            self.setText(norm)
            self.blockSignals(False)
            text = norm
        if len(text) == self.max_length:
            QTimer.singleShot(0, self.filled.emit)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.nextRequested.emit()
            return
        if event.key() == Qt.Key_Backspace and not self.text():
            self.parent().backspaceFromEmptyBox(self)  # type: ignore
            return
        super().keyPressEvent(event)


class JalaliDateInput(QWidget):
    """ویجت [YYYY] / [MM] / [DD]"""

    valueChanged = Signal(str)   # "1403/05/12" یا ""
    submitted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LeftToRight)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.year_box = _DigitBox(4, 1500)
        self.month_box = _DigitBox(2, 12)
        self.day_box = _DigitBox(2, 31)

        sep1 = QLabel("/")
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setFixedWidth(10)
        sep1.setStyleSheet("font-weight: bold; font-size: 14px;")
        sep2 = QLabel("/")
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setFixedWidth(10)
        sep2.setStyleSheet("font-weight: bold; font-size: 14px;")

        layout.addWidget(self.year_box)
        layout.addWidget(sep1)
        layout.addWidget(self.month_box)
        layout.addWidget(sep2)
        layout.addWidget(self.day_box)

        self.year_box.filled.connect(lambda: self.month_box.setFocus())
        self.month_box.filled.connect(lambda: self.day_box.setFocus())

        self.year_box.nextRequested.connect(self._on_year_enter)
        self.month_box.nextRequested.connect(self._on_month_enter)
        self.day_box.nextRequested.connect(self._on_day_enter)

        for box in (self.year_box, self.month_box, self.day_box):
            box.textChanged.connect(self._emit_changed)

    def value(self) -> str:
        y = self.year_box.text().strip()
        m = self.month_box.text().strip()
        d = self.day_box.text().strip()
        if not (y and m and d):
            return ""
        y = y.zfill(4)
        m = m.zfill(2)
        d = d.zfill(2)
        return f"{y}/{m}/{d}"

    def is_valid(self) -> bool:
        y = self.year_box.text().strip()
        m = self.month_box.text().strip()
        d = self.day_box.text().strip()
        if not (y and m and d):
            return False
        try:
            return is_valid_day(int(y), int(m), int(d))
        except ValueError:
            return False

    def set_value(self, value: str) -> None:
        self.year_box.blockSignals(True)
        self.month_box.blockSignals(True)
        self.day_box.blockSignals(True)
        try:
            if value and "/" in value:
                parts = value.split("/")
                if len(parts) == 3:
                    y, m, d = parts
                    self.year_box.setText(y.zfill(4))
                    self.month_box.setText(m.zfill(2))
                    self.day_box.setText(d.zfill(2))
                    return
            self.year_box.clear()
            self.month_box.clear()
            self.day_box.clear()
        finally:
            self.year_box.blockSignals(False)
            self.month_box.blockSignals(False)
            self.day_box.blockSignals(False)
        self._emit_changed()

    def clear(self) -> None:
        self.set_value("")

    def setFocus(self) -> None:  # type: ignore[override]
        self.year_box.setFocus()
        self.year_box.selectAll()

    def backspaceFromEmptyBox(self, box: QLineEdit) -> None:
        if box is self.day_box:
            self.month_box.setFocus()
            self.month_box.setCursorPosition(len(self.month_box.text()))
        elif box is self.month_box:
            self.year_box.setFocus()
            self.year_box.setCursorPosition(len(self.year_box.text()))

    def _emit_changed(self, *_):
        self.valueChanged.emit(self.value())

    def _on_year_enter(self):
        if len(self.year_box.text()) == 4:
            self.month_box.setFocus()
            self.month_box.selectAll()
        else:
            self.submitted.emit()

    def _on_month_enter(self):
        if len(self.month_box.text()) in (1, 2):
            self.day_box.setFocus()
            self.day_box.selectAll()
        else:
            self.submitted.emit()

    def _on_day_enter(self):
        self.submitted.emit()