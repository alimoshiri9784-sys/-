"""
مدیریت آیکون‌های SVG
- تبدیل SVG → QIcon با رنگ دلخواه
- کش کردن آیکون‌ها برای سرعت
"""
from pathlib import Path
from typing import Dict, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

from app.core.config import ASSETS_DIR


ICONS_DIR = ASSETS_DIR / "icons"

# کش
_icon_cache: Dict[Tuple[str, str, int], QIcon] = {}


def icon(name: str, color: str = "#1A1D21", size: int = 20) -> QIcon:
    """
    دریافت QIcon از فایل SVG با رنگ دلخواه

    Args:
        name: نام فایل بدون پسوند (مثل "user")
        color: رنگ hex (مثل "#FF6B35")
        size: اندازه آیکون (px)

    Returns:
        QIcon آماده استفاده
    """
    key = (name, color, size)
    if key in _icon_cache:
        return _icon_cache[key]

    svg_path = ICONS_DIR / f"{name}.svg"
    if not svg_path.exists():
        # آیکون نبود → آیکون خالی برگردان
        return QIcon()

    # رندر SVG
    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    # رنگ‌آمیزی
    colored = QPixmap(size, size)
    colored.fill(QColor(0, 0, 0, 0))
    painter = QPainter(colored)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QColor(color))
    painter.end()

    qicon = QIcon(colored)
    _icon_cache[key] = qicon
    return qicon


def clear_cache() -> None:
    """پاک کردن کش (هنگام تغییر تم)"""
    _icon_cache.clear()