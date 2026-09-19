"""
صفحه ۲: مدیریت کاربر (پرسنل)
- فرم + آپلود عکس
- کارت عملیات
- جدول با آواتار
"""
from pathlib import Path
import shutil
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QSizePolicy,
    QLineEdit, QFileDialog
)

from app.core.config import MAX_EMPLOYEES, DATA_DIR
from app.core.database import Database
from app.core.models import Employee
from app.ui.icons import icon as svg_icon
from app.ui.widgets.jalali_date_input import JalaliDateInput
from app.ui.widgets.numeric_lineedit import NumericLineEdit
from app.ui.widgets.toast import show_success, show_error, show_warning
from app.ui.widgets.animations import apply_card_shadows
from app.ui.widgets.empty_state import Avatar
from app.utils.validators import (
    is_valid_national_code, is_valid_personnel_code
)

PHOTOS_DIR = DATA_DIR / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


class UsersPage(QWidget):
    """صفحه مدیریت کاربر"""

    dataChanged = Signal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._editing_id = None
        self._selected_id = None
        self._photo_path = None   # عکس انتخابی فعلی

        self._build_ui()
        apply_card_shadows(self)
        self.reload_table()

    # ==================== UI ====================
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ---------- بدنه: فرم + کارت عملیات ----------
        body = QHBoxLayout()
        body.setSpacing(16)

        # === ستون راست: فرم ===
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setMaximumWidth(880)

        grid = QGridLayout(form_card)
        grid.setContentsMargins(24, 22, 24, 22)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)

        # آواتار (در گوشه بالا-راست فرم)
        self.avatar = Avatar("", size=120)
        av_wrap = QWidget()
        av_l = QVBoxLayout(av_wrap)
        av_l.setContentsMargins(0, 0, 0, 0)
        av_l.setSpacing(6)
        av_l.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        av_l.addWidget(self.avatar, 0, Qt.AlignCenter)

        # دکمه‌های عکس
        av_btns = QHBoxLayout()
        av_btns.setSpacing(4)
        self.btn_photo = QPushButton("انتخاب")
        self.btn_photo.setCursor(Qt.PointingHandCursor)
        self.btn_photo.setMinimumHeight(28)
        self.btn_photo.clicked.connect(self._choose_photo)

        self.btn_remove_photo = QPushButton("حذف")
        self.btn_remove_photo.setCursor(Qt.PointingHandCursor)
        self.btn_remove_photo.setMinimumHeight(28)
        self.btn_remove_photo.clicked.connect(self._remove_photo)

        av_btns.addWidget(self.btn_photo)
        av_btns.addWidget(self.btn_remove_photo)
        av_l.addLayout(av_btns)

        grid.addWidget(av_wrap, 0, 2, 3, 1)   # آواتار در ستون سوم، سه ردیف

        # ردیف ۱: کد پرسنلی | کد ملی
        self.inp_code = NumericLineEdit(max_length=10)
        self.inp_code.setPlaceholderText("1001")
        grid.addWidget(self._make_field("کد پرسنلی *", self.inp_code), 0, 0)

        self.inp_national = NumericLineEdit(max_length=10)
        self.inp_national.setPlaceholderText("۱۰ رقم")
        grid.addWidget(self._make_field("کد ملی", self.inp_national), 0, 1)

        # ردیف ۲: نام | نام خانوادگی
        self.inp_first = QLineEdit()
        self.inp_first.setPlaceholderText("زینب")
        grid.addWidget(self._make_field("نام *", self.inp_first), 1, 0)

        self.inp_last = QLineEdit()
        self.inp_last.setPlaceholderText("مشمول")
        grid.addWidget(self._make_field("نام خانوادگی *", self.inp_last), 1, 1)

        # ردیف ۳: سمت | تاریخ استخدام
        self.inp_position = QLineEdit()
        self.inp_position.setPlaceholderText("نسخه پیچ")
        grid.addWidget(self._make_field("سمت", self.inp_position), 2, 0)

        self.inp_hire = JalaliDateInput()
        grid.addWidget(self._make_field("تاریخ استخدام", self.inp_hire), 2, 1)

        self.inp_birth = JalaliDateInput()
        self.inp_birth.setVisible(False)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)

        body.addWidget(form_card, 1)
        body.addStretch(0)

        # === ستون چپ: کارت عملیات ===
        action_card = QFrame()
        action_card.setObjectName("Card")
        action_card.setMaximumWidth(260)
        action_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        al = QVBoxLayout(action_card)
        al.setContentsMargins(18, 18, 18, 18)
        al.setSpacing(10)

        self.btn_add = self._make_action_btn("افزودن پرسنل جدید", "plus", "Primary")
        self.btn_add.clicked.connect(self._add_employee)

        self.btn_update = self._make_action_btn("ویرایش اطلاعات", "pencil")
        self.btn_update.clicked.connect(self._update_employee)
        self.btn_update.setEnabled(False)

        self.btn_clear = self._make_action_btn("پاک‌سازی فرم", "trash")
        self.btn_clear.clicked.connect(self._clear_form)

        self.btn_deactivate = self._make_action_btn(
            "غیرفعال‌سازی", "trash", "Danger"
        )
        self.btn_deactivate.clicked.connect(self._deactivate_employee)
        self.btn_deactivate.setEnabled(False)

        al.addWidget(self.btn_add)
        al.addWidget(self.btn_update)
        al.addWidget(self.btn_clear)
        al.addStretch(1)
        al.addWidget(self.btn_deactivate)

        body.addWidget(action_card)
        root.addLayout(body)

        # ---------- جدول ----------
        table_group = QGroupBox("👥 لیست پرسنل فعال")
        table_group.setLayoutDirection(Qt.RightToLeft)
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 20, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "عکس", "کد پرسنلی", "نام", "نام خانوادگی",
            "کد ملی", "سمت", "تاریخ استخدام", "شناسه"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setColumnHidden(7, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 90)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 0)

        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        table_layout.addWidget(self.table)
        root.addWidget(table_group, 1)

    # ---------- کمکی ----------
    def _make_field(self, label_text, widget):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setObjectName("FieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        widget.setMinimumHeight(42)
        v.addWidget(lbl)
        v.addWidget(widget)
        return w

    def _make_action_btn(self, text, icon_name, obj=None):
        btn = QPushButton("  %s" % text)
        if obj:
            btn.setObjectName(obj)
        icon_color = "#FFFFFF" if obj in ("Primary", "Danger") else "#6E7480"
        btn.setIcon(svg_icon(icon_name, icon_color, 16))
        btn.setIconSize(QSize(16, 16))
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    # ==================== آپلود عکس ====================
    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب عکس پرسنل", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return

        # کپی به پوشه data/photos با نام بر اساس کد پرسنلی
        code = self.inp_code.text().strip() or "temp"
        ext = Path(path).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".bmp"):
            ext = ".jpg"
        dest = PHOTOS_DIR / f"{code}{ext}"

        try:
            shutil.copyfile(path, dest)
            self._photo_path = str(dest)
            # نمایش در فرم
            self.avatar.set_photo(str(dest), self.inp_first.text() or "?")
            show_success(self, "عکس انتخاب شد — برای ذخیره، دکمه افزودن/ویرایش را بزنید")
        except Exception as e:
            show_error(self, "خطا در کپی عکس: %s" % e)

    def _remove_photo(self):
        if self._photo_path:
            try:
                Path(self._photo_path).unlink(missing_ok=True)
            except Exception:
                pass
        self._photo_path = None
        self.avatar.set_name(self.inp_first.text() or "")

    # ==================== اعتبارسنجی ====================
    def _validate_form(self, exclude_id=None):
        code = self.inp_code.text().strip()
        national = self.inp_national.text().strip()
        first = self.inp_first.text().strip()
        last = self.inp_last.text().strip()

        if not is_valid_personnel_code(code):
            show_warning(self, "کد پرسنلی معتبر نیست")
            self.inp_code.setFocus()
            return False
        if not first:
            show_warning(self, "نام الزامی است")
            self.inp_first.setFocus()
            return False
        if not last:
            show_warning(self, "نام خانوادگی الزامی است")
            self.inp_last.setFocus()
            return False
        if self.db.is_personnel_code_taken(code, exclude_id):
            show_error(self, "کد پرسنلی «%s» قبلاً ثبت شده است" % code)
            self.inp_code.setFocus()
            return False
        if national:
            if not is_valid_national_code(national):
                show_warning(self, "کد ملی معتبر نیست")
                self.inp_national.setFocus()
                return False
            if self.db.is_national_code_taken(national, exclude_id):
                show_error(self, "کد ملی «%s» قبلاً ثبت شده است" % national)
                self.inp_national.setFocus()
                return False
        if self.inp_hire.value() and not self.inp_hire.is_valid():
            show_warning(self, "تاریخ استخدام معتبر نیست")
            self.inp_hire.setFocus()
            return False
        return True

    # ==================== افزودن / ویرایش ====================
    def _add_employee(self):
        if self.db.count_active_employees() >= MAX_EMPLOYEES:
            show_warning(self, "حداکثر %d پرسنل فعال مجاز است" % MAX_EMPLOYEES)
            return
        if not self._validate_form():
            return

        emp = Employee(
            personnel_code=self.inp_code.text().strip(),
            first_name=self.inp_first.text().strip(),
            last_name=self.inp_last.text().strip(),
            national_code=self.inp_national.text().strip() or None,
            hire_date=self.inp_hire.value() or None,
            position=self.inp_position.text().strip() or None,
            photo_path=self._photo_path,
        )
        self.db.add_employee(emp)
        show_success(self, "پرسنل «%s» اضافه شد" % emp.full_name)
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    def _update_employee(self):
        if not self._editing_id:
            return
        if not self._validate_form(exclude_id=self._editing_id):
            return

        emp = Employee(
            id=self._editing_id,
            personnel_code=self.inp_code.text().strip(),
            first_name=self.inp_first.text().strip(),
            last_name=self.inp_last.text().strip(),
            national_code=self.inp_national.text().strip() or None,
            hire_date=self.inp_hire.value() or None,
            position=self.inp_position.text().strip() or None,
            photo_path=self._photo_path,
        )
        self.db.update_employee(emp)
        show_success(self, "اطلاعات ویرایش شد")
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    def _deactivate_employee(self):
        if not self._selected_id:
            return
        emp = self.db.get_employee_by_id(self._selected_id)
        if not emp:
            return

        from PySide6.QtWidgets import QMessageBox
        ans = QMessageBox.question(
            self, "تأیید",
            "آیا از غیرفعال‌سازی «%s» مطمئن هستید؟" % emp.full_name,
            QMessageBox.Yes | QMessageBox.No
        )
        if ans != QMessageBox.Yes:
            return
        self.db.deactivate_employee(self._selected_id)
        show_success(self, "پرسنل غیرفعال شد")
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    # ==================== جدول ====================
    def reload_table(self):
        employees = self.db.get_all_active_employees()
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(employees))
            for i, emp in enumerate(employees):
                # آواتار
                av = Avatar("", size=56)
                if emp.photo_path:
                    av.set_photo(emp.photo_path, emp.full_name)
                else:
                    av.set_name(emp.full_name)

                av_wrap = QWidget()
                al = QHBoxLayout(av_wrap)
                al.setContentsMargins(4, 4, 4, 4)
                al.setAlignment(Qt.AlignCenter)
                al.addWidget(av)
                self.table.setCellWidget(i, 0, av_wrap)

                cells = [
                    emp.personnel_code, emp.first_name, emp.last_name,
                    emp.national_code or "—", emp.position or "—",
                    emp.hire_date or "—", str(emp.id),
                ]
                for j, text in enumerate(cells, start=1):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

                self.table.setRowHeight(i, 70)
        finally:
            self.table.setUpdatesEnabled(True)

    def _on_row_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_id = None
            self.btn_update.setEnabled(False)
            self.btn_deactivate.setEnabled(False)
            return
        row = rows[0].row()
        emp_id = int(self.table.item(row, 7).text())
        self._selected_id = emp_id
        self.btn_update.setEnabled(True)
        self.btn_deactivate.setEnabled(True)

    def _on_row_double_clicked(self, index):
        if index.row() < 0:
            return
        emp_id = int(self.table.item(index.row(), 7).text())
        emp = self.db.get_employee_by_id(emp_id)
        if not emp:
            return

        self._editing_id = emp.id
        self.inp_code.setText(emp.personnel_code)
        self.inp_first.setText(emp.first_name)
        self.inp_last.setText(emp.last_name)
        self.inp_national.setText(emp.national_code or "")
        self.inp_position.setText(emp.position or "")
        self.inp_hire.set_value(emp.hire_date or "")
        self._photo_path = emp.photo_path

        if emp.photo_path:
            self.avatar.set_photo(emp.photo_path, emp.full_name)
        else:
            self.avatar.set_name(emp.full_name)

        self.btn_update.setEnabled(True)

    # ==================== پاک‌سازی ====================
    def _clear_form(self):
        self._editing_id = None
        self._selected_id = None
        self._photo_path = None
        self.inp_code.clear()
        self.inp_first.clear()
        self.inp_last.clear()
        self.inp_national.clear()
        self.inp_position.clear()
        self.inp_hire.clear()
        self.avatar.set_name("")
        self.btn_update.setEnabled(False)
        self.btn_deactivate.setEnabled(False)
        self.table.clearSelection()