"""
نقطه ورود برنامه
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont

from app.core.config import APP_NAME, ORG_NAME, FONTS_DIR
from app.core.database import Database
from app.core.auth import AuthManager
from app.core.time_service import TimeService
from app.ui.main_window import MainWindow
from app.utils.enter_navigation import install_enter_navigation

def load_fonts() -> str:
    """
    بارگذاری فونت وزیرمتن از پوشه assets/fonts
    اگر پیدا نشد، از فونت سیستم استفاده می‌شود
    """
    family = "Vazirmatn"
    loaded_any = False
    if FONTS_DIR.exists():
        for ttf in sorted(FONTS_DIR.glob("*.ttf")):
            fid = QFontDatabase.addApplicationFont(str(ttf))
            if fid != -1:
                families = QFontDatabase.applicationFontFamilies(fid)
                if families:
                    family = families[0]
                    loaded_any = True

    if not loaded_any:
        # فونت وزیرمتن پیدا نشد → از فونت سیستم استفاده کن
        family = "Segoe UI"
    return family


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setLayoutDirection(Qt.RightToLeft)

    # فونت
    family = load_fonts()
    font = QFont(family, 10)
    app.setFont(font)

    # ناوبری با Enter در ویجت‌های ورودی
    install_enter_navigation(app)

    # سرویس‌ها
    db = Database()
    auth = AuthManager(db)
    time_service = TimeService(db)

    # پنجره اصلی
    win = MainWindow(db, auth, time_service)
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())