"""
مدیریت تم روشن/تاریک و استایل‌های QSS
نسخه ارتقاءیافته: تایپوگرافی معنادار + جدول‌های بهتر + Badge
"""
from enum import Enum

from PySide6.QtWidgets import QApplication


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


# ============================================================
# پالت رنگ — روشن (نارنجی گرم)
# ============================================================
LIGHT_COLORS = {
    "bg":              "#F4F5F7",
    "surface":         "#FFFFFF",
    "surface_alt":     "#FAFBFC",
    "surface_hover":   "#F0F1F4",
    "border":          "#E8EAED",
    "border_strong":   "#D5D8DD",
    "text":            "#1A1D21",
    "text_muted":      "#6E7480",
    "text_soft":       "#9099A5",
    "primary":         "#FF6B35",
    "primary_hover":   "#F25A20",
    "primary_soft":    "#FFF1EB",
    "primary_text":    "#FFFFFF",
    "success":         "#10B981",
    "success_soft":    "#E8F8F2",
    "danger":          "#EF4444",
    "danger_soft":     "#FDECEC",
    "warning":         "#F59E0B",
    "warning_soft":    "#FEF3C7",
    "info":            "#3B82F6",
    "info_soft":       "#EFF6FF",
    "sidebar_bg":      "#1E2128",
    "sidebar_text":    "#C9CDD4",
    "sidebar_hover":   "#2A2E37",
    "sidebar_active":  "#FF6B35",
    "topbar_bg":       "#FFFFFF",
    "topbar_border":   "#EDEEF1",
}

# ============================================================
# پالت رنگ — تاریک
# ============================================================
DARK_COLORS = {
    "bg":              "#14161A",
    "surface":         "#1E2128",
    "surface_alt":     "#262A33",
    "surface_hover":   "#2D323D",
    "border":          "#333944",
    "border_strong":   "#424A58",
    "text":            "#F1F3F6",
    "text_muted":      "#9CA3AF",
    "text_soft":       "#6E7480",
    "primary":         "#FF7A4D",
    "primary_hover":   "#FF8B63",
    "primary_soft":    "#3A2418",
    "primary_text":    "#FFFFFF",
    "success":         "#34D399",
    "success_soft":    "#14332B",
    "danger":          "#F87171",
    "danger_soft":     "#3A1E1E",
    "warning":         "#FBBF24",
    "warning_soft":    "#3A2E14",
    "info":            "#60A5FA",
    "info_soft":       "#1E2A44",
    "sidebar_bg":      "#0F1218",
    "sidebar_text":    "#B8BDC7",
    "sidebar_hover":   "#1E2128",
    "sidebar_active":  "#FF7A4D",
    "topbar_bg":       "#1E2128",
    "topbar_border":   "#2A2E37",
}


def get_colors(mode: ThemeMode) -> dict:
    return DARK_COLORS if mode == ThemeMode.DARK else LIGHT_COLORS


# ============================================================
# قالب QSS — با placeholder های امن @@نام@@
# ============================================================
_QSS_TEMPLATE = """
/* ==================== عمومی ==================== */
QWidget {
    font-family: @@font_stack@@;
    font-size: 13px;
    color: @@text@@;
}

QMainWindow, QDialog {
    background-color: @@bg@@;
}

/* ==================== کارت‌ها ==================== */
QFrame#Card {
    background-color: @@surface@@;
    border: 1px solid @@border@@;
    border-radius: 16px;
}

QFrame#Topbar {
    background-color: @@topbar_bg@@;
    border-bottom: 1px solid @@topbar_border@@;
}

QFrame#Sidebar {
    background-color: @@sidebar_bg@@;
    border: none;
}

/* ==================== تایپوگرافی ==================== */
QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: @@text@@;
    padding: 6px 0 10px 0;
}

QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: @@text@@;
}

QLabel#FieldLabel {
    color: @@text_muted@@;
    font-size: 12px;
    font-weight: 500;
}

QLabel#InfoValue {
    color: @@text@@;
    font-size: 14px;
    font-weight: 700;
}

QLabel#Caption {
    color: @@text_soft@@;
    font-size: 11px;
    font-weight: 500;
}

QLabel#SummaryLabel {
    color: @@primary@@;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 6px;
}

QLabel#StatusComplete {
    color: @@success@@;
    font-weight: 700;
}

QLabel#StatusIncomplete {
    color: @@danger@@;
    font-weight: 700;
}

/* ==================== دکمه‌ها ==================== */
QPushButton {
    background-color: @@surface@@;
    color: @@text@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 8px 16px;
    min-height: 20px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: @@surface_hover@@;
    border-color: @@border_strong@@;
}
QPushButton:pressed {
    background-color: @@border@@;
}
QPushButton:disabled {
    color: @@text_soft@@;
    background-color: @@surface_alt@@;
    border-color: @@border@@;
}

QPushButton#Primary {
    background-color: @@primary@@;
    color: @@primary_text@@;
    border: none;
    font-weight: 700;
    padding: 10px 24px;
    min-height: 24px;
}
QPushButton#Primary:hover {
    background-color: @@primary_hover@@;
}
QPushButton#Primary:pressed {
    background-color: @@primary@@;
}
QPushButton#Primary:disabled {
    background-color: @@border@@;
    color: @@text_soft@@;
}

QPushButton#Danger {
    background-color: @@danger@@;
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}
QPushButton#Danger:hover {
    background-color: #B91C1C;
}

QPushButton#Success {
    background-color: @@success@@;
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}
QPushButton#Success:hover {
    background-color: #059669;
}

/* ==================== Sidebar ==================== */
QPushButton#SidebarButton {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 0;
}
QPushButton#SidebarButton:hover {
    background-color: @@sidebar_hover@@;
}
QPushButton#SidebarButton:checked {
    background-color: @@sidebar_active@@;
}
QPushButton#SidebarButton:disabled {
    background-color: transparent;
}

QLabel#SidebarTitle {
    color: #F9FAFB;
    font-size: 17px;
    font-weight: 700;
    padding: 0;
}


/* ==================== Topbar ==================== */
QLabel#TopbarTitle {
    font-size: 17px;
    font-weight: 700;
    color: @@text@@;
}

QLabel#TopbarClock {
    font-family: @@font_mono@@;
    font-size: 13px;
    font-weight: 700;
    color: @@primary@@;
    padding: 8px 14px;
    background-color: @@primary_soft@@;
    border-radius: 10px;
}

QLabel#TopbarStatus {
    font-size: 12px;
    color: @@text_muted@@;
    padding: 6px 12px;
    background-color: @@surface_alt@@;
    border-radius: 10px;
}

QPushButton#TopbarButton {
    background-color: @@surface_alt@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton#TopbarButton:hover {
    background-color: @@surface_hover@@;
    border-color: @@border_strong@@;
}
QPushButton#TopbarButton:checked {
    background-color: @@primary@@;
    color: #FFFFFF;
    border-color: @@primary@@;
}

/* ==================== ورودی‌ها ==================== */
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
    background-color: @@surface@@;
    color: @@text@@;
    border: 1.5px solid @@border@@;
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: @@primary@@;
    selection-color: #FFFFFF;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid @@primary@@;
}
QLineEdit:disabled, QComboBox:disabled {
    background-color: @@surface_alt@@;
    color: @@text_soft@@;
}
QLineEdit:hover, QComboBox:hover {
    border-color: @@border_strong@@;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background-color: @@surface@@;
    color: @@text@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 6px;
    selection-background-color: @@primary_soft@@;
    selection-color: @@primary@@;
    outline: none;
}

/* ==================== ورودی تاریخ/ساعت ==================== */
QLineEdit#DatePart, QLineEdit#TimePart {
    min-height: 22px;
    padding: 6px 4px;
    font-family: @@font_mono@@;
    font-weight: 700;
    font-size: 14px;
}
QLineEdit#DatePart:focus, QLineEdit#TimePart:focus {
    border: 1.5px solid @@primary@@;
    background-color: @@primary_soft@@;
}

/* ==================== جدول ==================== */
QTableWidget, QTableView {
    background-color: @@surface@@;
    alternate-background-color: @@surface_alt@@;
    gridline-color: transparent;
    border: 1px solid @@border@@;
    border-radius: 14px;
    selection-background-color: @@primary_soft@@;
    selection-color: @@primary@@;
    outline: none;
    padding: 4px;
}
QTableWidget::item {
    padding: 12px 10px;
    border-bottom: 1px solid @@border@@;
    font-size: 13px;
}
QTableWidget::item:selected {
    background-color: @@primary_soft@@;
    color: @@primary@@;
}
QHeaderView::section {
    background-color: @@surface_alt@@;
    color: @@text_muted@@;
    padding: 13px 10px;
    border: none;
    border-bottom: 2px solid @@border@@;
    font-weight: 700;
    font-size: 12px;
}
QHeaderView::section:first {
    border-top-right-radius: 12px;
}
QHeaderView::section:last {
    border-top-left-radius: 12px;
}
QTableCornerButton::section {
    background-color: @@surface_alt@@;
    border: none;
}

/* ==================== Badge ها ==================== */
QLabel#BadgeSuccess {
    background-color: @@success_soft@@;
    color: @@success@@;
    padding: 4px 12px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#BadgeDanger {
    background-color: @@danger_soft@@;
    color: @@danger@@;
    padding: 4px 12px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#BadgeWarning {
    background-color: @@warning_soft@@;
    color: @@warning@@;
    padding: 4px 12px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#BadgeInfo {
    background-color: @@info_soft@@;
    color: @@info@@;
    padding: 4px 12px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}

/* ==================== Radio / Check ==================== */
QRadioButton, QCheckBox {
    color: @@text@@;
    spacing: 8px;
    padding: 4px;
    font-size: 13px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid @@border_strong@@;
    background-color: @@surface@@;
}
QRadioButton::indicator {
    border-radius: 9px;
}
QCheckBox::indicator {
    border-radius: 5px;
}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background-color: @@primary@@;
    border-color: @@primary@@;
}
QRadioButton::indicator:hover, QCheckBox::indicator:hover {
    border-color: @@primary@@;
}

/* ==================== Scrollbar ==================== */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: @@border_strong@@;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: @@text_muted@@;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: @@border_strong@@;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: @@text_muted@@;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ==================== GroupBox ==================== */
QGroupBox {
    background-color: @@surface@@;
    border: 1px solid @@border@@;
    border-radius: 16px;
    margin-top: 16px;
    padding: 22px 14px 14px 14px;
    font-weight: 700;
    font-size: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    right: 20px;
    padding: 0 10px;
    color: @@text@@;
    background-color: @@surface@@;
}

/* ==================== Message Box ==================== */
QMessageBox {
    background-color: @@surface@@;
}
QMessageBox QLabel {
    color: @@text@@;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 100px;
    padding: 8px 18px;
}

/* ==================== Tooltip ==================== */
QToolTip {
    background-color: @@sidebar_bg@@;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ==================== Menu ==================== */
QMenu {
    background-color: @@surface@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 8px 22px 8px 14px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: @@primary_soft@@;
    color: @@primary@@;
}

QInputDialog {
    background-color: @@surface@@;
}
"""


def build_qss(mode: ThemeMode) -> str:
    """ساخت QSS با جایگزینی امن متغیرها"""
    c = get_colors(mode)

    # اضافه کردن فونت‌ها
    colors = dict(c)
    colors["font_stack"] = '"Vazirmatn", "IRANSans", "Segoe UI", "Tahoma", sans-serif'
    colors["font_mono"] = '"JetBrains Mono", "Consolas", "Courier New", monospace'

    # جایگزینی امن
    qss = _QSS_TEMPLATE
    for key, value in colors.items():
        qss = qss.replace(f"@@{key}@@", str(value))

    return qss


def apply_theme(app: QApplication, mode: ThemeMode) -> None:
    """اعمال تم روی کل اپلیکیشن"""
    app.setStyleSheet(build_qss(mode))