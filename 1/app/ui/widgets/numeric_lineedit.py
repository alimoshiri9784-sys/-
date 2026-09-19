"""
QLineEdit که فقط عدد می‌پذیرد و همیشه LTR است
"""
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit

from app.utils.validators import normalize_digits

# حداکثر مقداری که QIntValidator پشتیبانی می‌کند: 2^31 - 1
_INT_MAX = 2_147_483_647


class NumericLineEdit(QLineEdit):
    """
    ورودی فقط عددی، LTR، با پشتیبانی از Paste تمیز
    - اگر max_length کوچک باشد (<= 9 رقم) از QIntValidator استفاده می‌کند
    - در غیر این صورت از Regex استفاده می‌کند تا Overflow رخ ندهد
    """

    def __init__(self, max_length: int = 10, parent=None):
        super().__init__(parent)
        self._max_length = max_length
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setMaxLength(max_length)

        # اگر max_length منجر به مقداری بیش از INT_MAX شود، از Regex استفاده کن
        max_value = 10 ** max_length - 1
        if max_value <= _INT_MAX:
            from PySide6.QtGui import QIntValidator
            self.setValidator(QIntValidator(0, max_value, self))
        else:
            # فقط رقم انگلیسی
            regex = QRegularExpression(r"^\d{0,%d}$" % max_length)
            self.setValidator(QRegularExpressionValidator(regex, self))

    def setText(self, text: str) -> None:  # type: ignore[override]
        super().setText(normalize_digits(text or ""))

    def text(self) -> str:  # type: ignore[override]
        return normalize_digits(super().text())