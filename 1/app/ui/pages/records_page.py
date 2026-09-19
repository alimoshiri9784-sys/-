"""
صفحه ۴: مدیریت تردد
- افزودن / ویرایش / حذف رکورد
- جدول ۵۰۰ رکورد آخر
- بدون عنوان صفحه
"""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QGroupBox,
    QSizePolicy
)

from app.core.config import RECORDS_PAGE_LIMIT
from app.core.database import Database
from app.core.models import AttendanceRecord
from app.ui.icons import icon as svg_icon
from app.ui.widgets.jalali_date_input import JalaliDateInput
from app.ui.widgets.time_input import TimeInput
from app.ui.widgets.numeric_lineedit import NumericLineEdit
from app.ui.widgets.toast import show_success, show_warning
from app.ui.widgets.animations import apply_card_shadows
from app.utils.helpers import calculate_duration


class RecordsPage(QWidget):
    """صفحه مدیریت تردد"""

    dataChanged = Signal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._selected_id = None

        self._build_ui()
        apply_card_shadows(self)
        self.reload_table()

    # ==================== UI ====================
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # ← بدون عنوان «مدیریت تردد»

        # ---------- کارت فرم (فشرده) ----------
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setMaximumWidth(1100)
        form_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        grid = QGridLayout(form_card)
        grid.setContentsMargins(24, 18, 24, 18)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(12)

        def field(label_text, widget, min_w=0):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(8)
            h.setAlignment(Qt.AlignCenter)

            lbl = QLabel(label_text)
            lbl.setObjectName("FieldLabel")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFixedWidth(80)

            if min_w:
                widget.setMinimumWidth(min_w)
            widget.setMinimumHeight(40)

            h.addStretch(1)
            h.addWidget(lbl)
            h.addWidget(widget)
            h.addStretch(1)
            return w

        # ردیف ۱
        self.inp_code = NumericLineEdit(max_length=10)
        self.inp_code.setPlaceholderText("1001")
        self.inp_code.setFixedWidth(140)
        grid.addWidget(field("کد پرسنلی *", self.inp_code), 0, 0)

        self.inp_date = JalaliDateInput()
        grid.addWidget(field("تاریخ *", self.inp_date), 0, 1)

        # ردیف ۲
        self.inp_entry = TimeInput()
        grid.addWidget(field("ساعت ورود", self.inp_entry), 1, 0)

        self.inp_exit = TimeInput()
        grid.addWidget(field("ساعت خروج", self.inp_exit), 1, 1)

        # ردیف ۳
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("توضیح (اختیاری)")
        self.inp_desc.setMinimumHeight(40)
        grid.addWidget(field("توضیح", self.inp_desc), 2, 0, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        wrap_form = QHBoxLayout()
        wrap_form.addStretch(1)
        wrap_form.addWidget(form_card)
        wrap_form.addStretch(1)
        root.addLayout(wrap_form)

        # ---------- نوار دکمه‌ها ----------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch(1)

        self.btn_add = self._btn("افزودن", "plus", "Primary")
        self.btn_add.clicked.connect(self._add_record)

        self.btn_update = self._btn("ویرایش", "pencil")
        self.btn_update.clicked.connect(self._update_record)
        self.btn_update.setEnabled(False)

        self.btn_delete = self._btn("حذف", "trash", "Danger")
        self.btn_delete.clicked.connect(self._delete_record)
        self.btn_delete.setEnabled(False)

        self.btn_clear = self._btn("پاک‌سازی", "trash")
        self.btn_clear.clicked.connect(self._clear_form)

        self.btn_refresh = self._btn("بروزرسانی", "search")
        self.btn_refresh.clicked.connect(self.reload_table)

        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_delete)
        btn_row.addWidget(self.btn_update)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        # ---------- جدول ----------
        table_group = QGroupBox("🗂 %d رکورد آخر" % RECORDS_PAGE_LIMIT)
        table_group.setLayoutDirection(Qt.RightToLeft)
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 20, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "کد پرسنلی", "تاریخ", "ورود", "خروج",
            "مدت", "توضیح"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self._on_row_selected)

        table_layout.addWidget(self.table)
        root.addWidget(table_group, 1)

    def _btn(self, text, icon_name, obj=None):
        b = QPushButton("  %s" % text)
        if obj:
            b.setObjectName(obj)
        c = "#FFFFFF" if obj in ("Primary", "Danger") else "#6E7480"
        b.setIcon(svg_icon(icon_name, c, 14))
        b.setIconSize(QSize(14, 14))
        b.setMinimumHeight(38)
        b.setMinimumWidth(120)
        b.setCursor(Qt.PointingHandCursor)
        return b

    # ==================== جدول ====================
    def reload_table(self) -> None:
        records = self.db.get_recent_attendance(limit=RECORDS_PAGE_LIMIT)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(records))
            for i, rec in enumerate(records):
                duration = calculate_duration(
                    rec.entry_time or "", rec.exit_time or ""
                )
                cells = [
                    str(rec.id), rec.personnel_code, rec.jalali_date,
                    rec.entry_time or "—", rec.exit_time or "—",
                    duration or "—", rec.description or "—",
                ]
                for j, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    if not rec.is_complete and (rec.entry_time or rec.exit_time):
                        item.setForeground(Qt.red)
                    self.table.setItem(i, j, item)
        finally:
            self.table.setUpdatesEnabled(True)

    def _on_row_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_id = None
            self.btn_update.setEnabled(False)
            self.btn_delete.setEnabled(False)
            return

        row = rows[0].row()
        rec_id = int(self.table.item(row, 0).text())
        self._selected_id = rec_id
        self.btn_update.setEnabled(True)
        self.btn_delete.setEnabled(True)

        rec = self.db.get_attendance_by_id(rec_id)
        if not rec:
            return
        self.inp_code.setText(rec.personnel_code)
        self.inp_date.set_value(rec.jalali_date)
        self.inp_entry.set_value(rec.entry_time or "")
        self.inp_exit.set_value(rec.exit_time or "")
        self.inp_desc.setText(rec.description or "")

    # ==================== افزودن ====================
    def _add_record(self) -> None:
        emp, err = self._validate_and_get_employee()
        if not emp:
            if err:
                show_warning(self, err)
            return

        if not self.inp_date.value() or not self.inp_date.is_valid():
            show_warning(self, "تاریخ معتبر وارد کنید")
            return

        entry = self.inp_entry.value() or None
        exit_ = self.inp_exit.value() or None
        if not entry and not exit_:
            show_warning(self, "حداقل یکی از ساعت ورود/خروج لازم است")
            return

        rec = AttendanceRecord(
            employee_id=emp.id,
            jalali_date=self.inp_date.value(),
            entry_time=entry,
            exit_time=exit_,
            description=self.inp_desc.text().strip() or None,
        )
        self.db.add_attendance(rec)
        show_success(self, "رکورد اضافه شد")
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    # ==================== ویرایش ====================
    def _update_record(self) -> None:
        if not self._selected_id:
            return
        emp, err = self._validate_and_get_employee()
        if not emp:
            if err:
                show_warning(self, err)
            return

        if not self.inp_date.value() or not self.inp_date.is_valid():
            show_warning(self, "تاریخ معتبر وارد کنید")
            return

        rec = AttendanceRecord(
            id=self._selected_id,
            employee_id=emp.id,
            jalali_date=self.inp_date.value(),
            entry_time=self.inp_entry.value() or None,
            exit_time=self.inp_exit.value() or None,
            description=self.inp_desc.text().strip() or None,
        )
        self.db.update_attendance(rec)
        show_success(self, "رکورد ویرایش شد")
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    # ==================== حذف ====================
    def _delete_record(self) -> None:
        if not self._selected_id:
            return
        ans = QMessageBox.question(
            self, "تأیید حذف",
            "آیا از حذف این رکورد مطمئن هستید؟ این عمل بازگشت‌پذیر نیست.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans != QMessageBox.Yes:
            return
        self.db.delete_attendance(self._selected_id)
        show_success(self, "رکورد حذف شد")
        self._clear_form()
        self.reload_table()
        self.dataChanged.emit()

    # ==================== کمکی ====================
    def _validate_and_get_employee(self):
        code = self.inp_code.text().strip()
        if not code:
            return None, "کد پرسنلی را وارد کنید"
        emp = self.db.get_employee_by_code(code)
        if not emp:
            return None, "پرسنلی با کد «%s» یافت نشد" % code
        return emp, None

    def _clear_form(self) -> None:
        self._selected_id = None
        self.inp_code.clear()
        self.inp_date.clear()
        self.inp_entry.clear()
        self.inp_exit.clear()
        self.inp_desc.clear()
        self.btn_update.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.table.clearSelection()