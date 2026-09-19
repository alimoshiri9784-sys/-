"""
ورودی ساعت به‌صورت دو کادر: HH : MM
- پرش خودکار
- اعتبارسنجی
- Enter به ویجت بعدی
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit

from app.utils.validators import normalize_digits


class _DigitBox(QLineEdit):
    """کادر دو رقمی با LTR و پرش خودکار"""

    filled = Signal()
    nextRequested = Signal()

    def __init__(self, max_value: int, parent=None):
        super().__init__(parent)
        self.max_value = max_value
        self.setObjectName("TimePart")            # ← ← ← اضافه شد
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAlignment(Qt.AlignCenter)
        self.setMaxLength(2)
        self.setFixedWidth(48)
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

        if len(text) == 2:
            try:
                val = int(text)
            except ValueError:
                return
            if val > self.max_value:
                self.blockSignals(True)
                self.setText(f"0{text[1]}")
                self.blockSignals(False)
            QTimer.singleShot(0, self.filled.emit)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.nextRequested.emit()
            return
        super().keyPressEvent(event)


class TimeInput(QWidget):
    """ویجت [HH] : [MM]"""

    valueChanged = Signal(str)  # "HH:MM" یا ""
    submitted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LeftToRight)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.hour_box = _DigitBox(23)
        self.minute_box = _DigitBox(59)

        sep = QLabel(":")
        sep.setAlignment(Qt.AlignCenter)
        sep.setFixedWidth(10)
        sep.setStyleSheet("font-weight: bold; font-size: 14px;")

        layout.addWidget(self.hour_box)
        layout.addWidget(sep)
        layout.addWidget(self.minute_box)

        self.hour_box.filled.connect(lambda: self.minute_box.setFocus())
        self.hour_box.nextRequested.connect(self._on_hour_enter)
        self.minute_box.nextRequested.connect(self._on_minute_enter)

        self.hour_box.textChanged.connect(self._emit_changed)
        self.minute_box.textChanged.connect(self._emit_changed)

    def value(self) -> str:
        h = self.hour_box.text().strip()
        m = self.minute_box.text().strip()
        if not h and not m:
            return ""
        h = h.zfill(2) if h else "00"
        m = m.zfill(2) if m else "00"
        return f"{h}:{m}"

    def set_value(self, value: str) -> None:
        self.hour_box.blockSignals(True)
        self.minute_box.blockSignals(True)
        try:
            if value and ":" in value:
                h, m = value.split(":")
                self.hour_box.setText(h.zfill(2))
                self.minute_box.setText(m.zfill(2))
            else:
                self.hour_box.clear()
                self.minute_box.clear()
        finally:
            self.hour_box.blockSignals(False)
            self.minute_box.blockSignals(False)
        self._emit_changed()

    def clear(self) -> None:
        self.set_value("")

    def setFocus(self) -> None:  # type: ignore[override]
        self.hour_box.setFocus()
        self.hour_box.selectAll()

    def _emit_changed(self, *_):
        self.valueChanged.emit(self.value())

    def _on_hour_enter(self):
        if len(self.hour_box.text()) == 2:
            self.minute_box.setFocus()
            self.minute_box.selectAll()
        else:
            self.submitted.emit()

    def _on_minute_enter(self):
        self.submitted.emit()