"""
ویجت Empty State
- وقتی جدول یا لیست خالی است، پیام دوستانه با آیکون نمایش می‌دهد
- قابلیت جاسازی داخل QTableWidget
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy
)

from app.ui.icons import icon as svg_icon


class EmptyState(QWidget):
    """پیام خالی بودن"""

    def __init__(self, icon_name: str = "database",
                 title: str = "موردی یافت نشد",
                 subtitle: str = "",
                 parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        # آیکون
        icon_lbl = QLabel()
        icon_lbl.setPixmap(svg_icon(icon_name, "#9099A5", 56).pixmap(56, 56))
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # عنوان
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #6E7480;"
        )
        layout.addWidget(title_lbl)

        # توضیح
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setAlignment(Qt.AlignCenter)
            sub_lbl.setStyleSheet(
                "font-size: 12px; color: #9099A5;"
            )
            layout.addWidget(sub_lbl)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class Avatar(QLabel):
    """
    آواتار دایره‌ای با حرف اول نام یا عکس
    """

    COLORS = [
        ("#FFF1EB", "#FF6B35"),
        ("#E8F8F2", "#10B981"),
        ("#EFF6FF", "#3B82F6"),
        ("#FEF3C7", "#F59E0B"),
        ("#FDECEC", "#EF4444"),
        ("#F3E8FF", "#8B5CF6"),
        ("#E0F2FE", "#0EA5E9"),
    ]

    def __init__(self, name: str = "", size: int = 48, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.set_name(name)

    def set_name(self, name: str) -> None:
        """تعیین حرف اول و رنگ بر اساس نام"""
        if not name or name == "—":
            self.setText("?")
            bg, fg = "#F0F1F4", "#9099A5"
        else:
            first = name.strip()[0]
            self.setText(first)
            idx = sum(ord(c) for c in name) % len(self.COLORS)
            bg, fg = self.COLORS[idx]

        font_size = int(self._size * 0.42)
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: {self._size // 2}px;
            font-size: {font_size}px;
            font-weight: 700;
        """)

    def set_photo(self, photo_path: str, fallback_name: str = "") -> None:
        """نمایش عکس؛ اگر عکس نبود، حرف اول نام"""
        from pathlib import Path
        from PySide6.QtGui import QPainter, QPainterPath, QPixmap
        from PySide6.QtCore import Qt as _Qt

        p = Path(photo_path) if photo_path else None
        if p and p.exists() and p.is_file():
            pixmap = QPixmap(str(p))
            if not pixmap.isNull():
                # اسکیل و برش
                pixmap = pixmap.scaled(
                    self._size, self._size,
                    _Qt.KeepAspectRatioByExpanding,
                    _Qt.SmoothTransformation,
                )

                # برش دایره‌ای
                rounded = QPixmap(self._size, self._size)
                rounded.fill(_Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, self._size, self._size)
                painter.setClipPath(path)
                # مرکز کردن
                x = (self._size - pixmap.width()) // 2
                y = (self._size - pixmap.height()) // 2
                painter.drawPixmap(x, y, pixmap)
                painter.end()

                self.setPixmap(rounded)
                self.setText("")
                self.setStyleSheet("background: transparent;")
                return

        # fallback
        self.set_name(fallback_name)