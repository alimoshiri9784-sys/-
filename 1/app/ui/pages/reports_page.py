"""
صفحه ۳: گزارش
- Preset های کلیک‌پذیر (امروز / هفته / ماه / همه)
- فیلتر دستی تاریخ و ساعت
- جدول با خروجی CSV و PDF
"""
import jdatetime
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QCheckBox,
    QFileDialog, QSizePolicy
)

from app.core.database import Database
from app.core.models import AttendanceRecord, Employee
from app.core.time_service import TimeService
from app.ui.icons import icon as svg_icon
from app.ui.widgets.jalali_date_input import JalaliDateInput
from app.ui.widgets.time_input import TimeInput
from app.ui.widgets.toast import show_success, show_error, show_warning
from app.ui.widgets.animations import apply_card_shadows
from app.utils.exporters import export_to_csv, export_to_pdf
from app.utils.helpers import (
    calculate_duration, duration_to_minutes, minutes_to_duration
)


# ============================================================
# Preset Card — کلیک‌پذیر
# ============================================================
class PresetCard(QFrame):
    """کارت Preset کلیک‌پذیر"""

    clicked = Signal()

    def __init__(self, icon_name, label, sub, preset_key="",
                 active=False, parent=None):
        super().__init__(parent)
        self._active = active
        self._icon_name = icon_name
        self.preset_key = preset_key
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(76)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._icon_lbl = None
        self._title_lbl = None
        self._sub_lbl = None

        self._build(icon_name, label, sub)
        self._update_style()

    def _build(self, icon_name, label, sub):
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 10, 16, 10)
        h.setSpacing(12)
        h.setAlignment(Qt.AlignCenter)

        color = "#FF6B35" if self._active else "#1A1D21"

        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(svg_icon(icon_name, color, 26).pixmap(26, 26))
        self._icon_lbl.setFixedSize(28, 28)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        txt_box = QVBoxLayout()
        txt_box.setSpacing(2)
        txt_box.setAlignment(Qt.AlignVCenter)

        self._title_lbl = QLabel(label)
        self._title_lbl.setStyleSheet(
            "color: %s; font-size: 15px; font-weight: 700; "
            "background: transparent;" % color
        )
        self._title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._sub_lbl = QLabel(sub)
        self._sub_lbl.setStyleSheet(
            "color: %s; font-size: 12px; background: transparent;" % color
        )
        self._sub_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        txt_box.addWidget(self._title_lbl)
        txt_box.addWidget(self._sub_lbl)

        h.addStretch()
        h.addWidget(self._icon_lbl)
        h.addLayout(txt_box)
        h.addStretch()

    def set_active(self, active):
        if self._active == active:
            return
        self._active = active
        self._update_style()

    def set_sub(self, text):
        if self._sub_lbl:
            self._sub_lbl.setText(text)

    def _update_style(self):
        if self._active:
            self.setStyleSheet(
                "PresetCard { background: #FFF1EB; "
                "border: 2px solid #FF6B35; border-radius: 12px; }"
            )
            color = "#FF6B35"
        else:
            self.setStyleSheet(
                "PresetCard { background: #FFFFFF; "
                "border: 1px solid #E8EAED; border-radius: 12px; }"
            )
            color = "#1A1D21"

        if self._icon_lbl:
            self._icon_lbl.setPixmap(
                svg_icon(self._icon_name, color, 26).pixmap(26, 26)
            )
        if self._title_lbl:
            self._title_lbl.setStyleSheet(
                "color: %s; font-size: 15px; font-weight: 700; "
                "background: transparent;" % color
            )
        if self._sub_lbl:
            self._sub_lbl.setStyleSheet(
                "color: %s; font-size: 12px; background: transparent;" % color
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._active:
            self.setStyleSheet(
                "PresetCard { background: #FAFBFC; "
                "border: 1px solid #D5D8DD; border-radius: 12px; }"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style()
        super().leaveEvent(event)


# ============================================================
# صفحه گزارش
# ============================================================
class ReportsPage(QWidget):
    """صفحه گزارش‌گیری"""

    def __init__(self, db: Database, time_service: TimeService, parent=None):
        super().__init__(parent)
        self.db = db
        self.time_service = time_service
        self._results = []
        self._preset_cards = {}
        self._active_preset = "today"

        self._build_ui()
        apply_card_shadows(self)
        self._load_filters()
        self._on_preset_clicked("today", apply=True)

    # ==================== UI ====================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(10)

        # Preset row
        root.addLayout(self._preset_row())

        # Filter card
        mid = QHBoxLayout()
        mid.setSpacing(12)
        mid.addStretch(1)
        mid.addWidget(self._filter_card())
        mid.addStretch(1)
        root.addLayout(mid)

        # Action bar
        root.addLayout(self._action_bar())

        # Results
        root.addWidget(self._results_group(), 1)

    def _preset_row(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        specs = [
            ("today", "clock", "امروز", "9 رکورد"),
            ("week", "chart", "این هفته", "48 رکورد"),
            ("month", "database", "این ماه", "212 رکورد"),
            ("all", "users", "همه", "1,542 رکورد"),
        ]
        for key, icon_name, label, sub in specs:
            card = PresetCard(icon_name, label, sub, preset_key=key,
                              active=(key == "today"))
            card.clicked.connect(lambda k=key: self._on_preset_clicked(k))
            self._preset_cards[key] = card
            row.addWidget(card)

        return row

    def _filter_card(self):
        card = QFrame()
        card.setObjectName("Card")
        card.setMaximumWidth(720)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 18, 24, 18)
        v.setSpacing(10)

        # ردیف ۱
        row1 = QHBoxLayout()
        row1.setSpacing(20)
        row1.setAlignment(Qt.AlignCenter)
        row1.addStretch(1)

        self.inp_from_date = JalaliDateInput()
        self.inp_to_date = JalaliDateInput()
        row1.addWidget(self._labeled("از تاریخ:", self.inp_from_date, 60))
        row1.addWidget(self._labeled("تا تاریخ:", self.inp_to_date, 60))
        row1.addStretch(1)
        v.addLayout(row1)

        # ردیف ۲
        row2 = QHBoxLayout()
        row2.setSpacing(20)
        row2.setAlignment(Qt.AlignCenter)
        row2.addStretch(1)

        self.inp_from_time = TimeInput()
        self.inp_to_time = TimeInput()
        row2.addWidget(self._labeled("از ساعت:", self.inp_from_time, 60))
        row2.addWidget(self._labeled("تا ساعت:", self.inp_to_time, 60))
        row2.addStretch(1)
        v.addLayout(row2)

        # ردیف ۳
        row3 = QHBoxLayout()
        row3.setSpacing(14)
        row3.setAlignment(Qt.AlignCenter)

        self.cmb_employee = QComboBox()
        self.cmb_employee.setFixedWidth(140)

        self.cmb_position = QComboBox()
        self.cmb_position.setFixedWidth(140)

        self.chk_complete = QCheckBox("فقط کامل")

        row3.addStretch(1)
        row3.addWidget(self._labeled("کاربر:", self.cmb_employee, 45))
        row3.addWidget(self._labeled("سمت:", self.cmb_position, 40))
        row3.addWidget(self.chk_complete)
        row3.addStretch(1)
        v.addLayout(row3)

        return card

    def _labeled(self, label_text, widget, label_w=60, widget_w=0):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignCenter)

        lbl = QLabel(label_text)
        lbl.setObjectName("FieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setFixedWidth(label_w)

        if widget_w:
            widget.setFixedWidth(widget_w)

        h.addWidget(lbl)
        h.addWidget(widget)
        return w

    def _action_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(8)
        bar.addStretch(1)

        self.btn_csv = QPushButton("  خروجی CSV")
        self.btn_csv.setIcon(svg_icon("save", "#6E7480", 14))
        self.btn_csv.setIconSize(QSize(14, 14))
        self.btn_csv.setMinimumHeight(38)
        self.btn_csv.setCursor(Qt.PointingHandCursor)
        self.btn_csv.clicked.connect(self._export_csv)

        self.btn_pdf = QPushButton("  خروجی PDF")
        self.btn_pdf.setIcon(svg_icon("download", "#6E7480", 14))
        self.btn_pdf.setIconSize(QSize(14, 14))
        self.btn_pdf.setMinimumHeight(38)
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.clicked.connect(self._export_pdf)

        self.btn_clear = QPushButton("  پاک‌سازی")
        self.btn_clear.setIcon(svg_icon("trash", "#6E7480", 14))
        self.btn_clear.setIconSize(QSize(14, 14))
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_filters)

        self.btn_search = QPushButton("  اعمال فیلتر")
        self.btn_search.setObjectName("Primary")
        self.btn_search.setIcon(svg_icon("search", "#FFFFFF", 14))
        self.btn_search.setIconSize(QSize(14, 14))
        self.btn_search.setMinimumHeight(38)
        self.btn_search.setMinimumWidth(140)
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.clicked.connect(self._apply_filters)

        bar.addWidget(self.btn_csv)
        bar.addWidget(self.btn_pdf)
        bar.addWidget(self.btn_clear)
        bar.addWidget(self.btn_search)
        bar.addStretch(1)
        return bar

    def _results_group(self):
        gb = QGroupBox("📊 نتایج")
        gb.setLayoutDirection(Qt.RightToLeft)
        gl = QVBoxLayout(gb)
        gl.setContentsMargins(10, 20, 10, 10)
        gl.setSpacing(8)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "کد", "نام", "تاریخ", "ورود", "خروج",
            "مدت حضور", "وضعیت", "توضیح"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        gl.addWidget(self.table, 1)

        self.lbl_summary = QLabel("جمع کل مدت حضور: 00:00")
        self.lbl_summary.setStyleSheet(
            "color: #FF6B35; font-size: 14px; font-weight: 700; padding: 10px 4px;"
        )
        self.lbl_summary.setAlignment(Qt.AlignCenter)
        gl.addWidget(self.lbl_summary)

        return gb

    # ==================== Preset Logic ====================
    def _on_preset_clicked(self, preset_key, apply=False):
        try:
            today = jdatetime.date.today()

            if preset_key == "today":
                self.inp_from_date.set_value(self._jalali_str(today))
                self.inp_to_date.set_value(self._jalali_str(today))
            elif preset_key == "week":
                days_since_saturday = today.weekday()
                from_date = today - jdatetime.timedelta(days=days_since_saturday)
                self.inp_from_date.set_value(self._jalali_str(from_date))
                self.inp_to_date.set_value(self._jalali_str(today))
            elif preset_key == "month":
                from_date = jdatetime.date(today.year, today.month, 1)
                self.inp_from_date.set_value(self._jalali_str(from_date))
                self.inp_to_date.set_value(self._jalali_str(today))
            elif preset_key == "all":
                self.inp_from_date.clear()
                self.inp_to_date.clear()
        except Exception:
            self.inp_from_date.clear()
            self.inp_to_date.clear()

        for key, card in self._preset_cards.items():
            card.set_active(key == preset_key)
        self._active_preset = preset_key

        if apply:
            self._apply_filters()

    @staticmethod
    def _jalali_str(jdate):
        return "%04d/%02d/%02d" % (jdate.year, jdate.month, jdate.day)

    # ==================== Filters ====================
    def _load_filters(self):
        self.cmb_employee.clear()
        self.cmb_employee.addItem("کلیه", None)
        for emp in self.db.get_all_active_employees():
            self.cmb_employee.addItem(
                "%s — %s" % (emp.personnel_code, emp.full_name), emp.id
            )

        self.cmb_position.clear()
        self.cmb_position.addItem("کلیه", None)
        positions = set()
        for emp in self.db.get_all_active_employees():
            if emp.position:
                positions.add(emp.position)
        for pos in sorted(positions):
            self.cmb_position.addItem(pos, pos)

    def _apply_filters(self):
        from_date = self.inp_from_date.value()
        to_date = self.inp_to_date.value()
        from_time = self.inp_from_time.value()
        to_time = self.inp_to_time.value()
        emp_id = self.cmb_employee.currentData()
        position = self.cmb_position.currentData()
        only_complete = self.chk_complete.isChecked()

        if from_date and not self.inp_from_date.is_valid():
            show_warning(self, "تاریخ شروع معتبر نیست")
            return
        if to_date and not self.inp_to_date.is_valid():
            show_warning(self, "تاریخ پایان معتبر نیست")
            return

        all_records = self.db.get_recent_attendance(limit=100000)
        employees = {e.id: e for e in self.db.get_all_active_employees()}

        results = []
        for rec in all_records:
            emp = employees.get(rec.employee_id)
            if not emp:
                continue
            if emp_id and emp.id != emp_id:
                continue
            if position and (emp.position or "") != position:
                continue
            if from_date and rec.jalali_date < from_date:
                continue
            if to_date and rec.jalali_date > to_date:
                continue
            if from_time and rec.entry_time and rec.entry_time < from_time:
                continue
            if to_time and rec.entry_time and rec.entry_time > to_time:
                continue
            if only_complete and not rec.is_complete:
                continue
            results.append({"record": rec, "employee": emp})

        results.sort(
            key=lambda r: (r["record"].jalali_date,
                           r["record"].entry_time or "")
        )
        self._results = results

        self._update_preset_counts()
        self._fill_table()
        self._update_summary()

    def _update_preset_counts(self):
        try:
            today = jdatetime.date.today()
            today_str = self._jalali_str(today)
            all_recs = self.db.get_recent_attendance(limit=100000)

            count_today = sum(1 for r in all_recs if r.jalali_date == today_str)

            days = today.weekday()
            week_start = today - jdatetime.timedelta(days=days)
            week_start_str = self._jalali_str(week_start)
            count_week = sum(
                1 for r in all_recs
                if week_start_str <= r.jalali_date <= today_str
            )

            month_start = jdatetime.date(today.year, today.month, 1)
            month_start_str = self._jalali_str(month_start)
            count_month = sum(
                1 for r in all_recs
                if month_start_str <= r.jalali_date <= today_str
            )

            count_all = len(all_recs)

            self._preset_cards["today"].set_sub("%d رکورد" % count_today)
            self._preset_cards["week"].set_sub("%d رکورد" % count_week)
            self._preset_cards["month"].set_sub("%d رکورد" % count_month)
            self._preset_cards["all"].set_sub("{:,} رکورد".format(count_all))
        except Exception:
            pass

    def _clear_filters(self):
        self.inp_from_date.clear()
        self.inp_to_date.clear()
        self.inp_from_time.clear()
        self.inp_to_time.clear()
        self.cmb_employee.setCurrentIndex(0)
        self.cmb_position.setCurrentIndex(0)
        self.chk_complete.setChecked(False)

        for key, card in self._preset_cards.items():
            card.set_active(key == "all")
        self._active_preset = "all"

        self._results = []
        self.table.setRowCount(0)
        self.lbl_summary.setText("جمع کل مدت حضور: 00:00")

    # ==================== Table ====================
    def _fill_table(self):
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(self._results))
            for i, item in enumerate(self._results):
                rec = item["record"]
                emp = item["employee"]

                duration = calculate_duration(
                    rec.entry_time or "", rec.exit_time or ""
                )
                is_complete = rec.is_complete
                status = "✓ کامل" if is_complete else "⚠ ناقص"

                cells = [
                    emp.personnel_code,
                    emp.full_name,
                    rec.jalali_date,
                    rec.entry_time or "—",
                    rec.exit_time or "—",
                    duration or "—",
                    status,
                    rec.description or "—",
                ]
                for j, text in enumerate(cells):
                    table_item = QTableWidgetItem(text)
                    table_item.setTextAlignment(Qt.AlignCenter)
                    if not is_complete:
                        table_item.setForeground(Qt.red)
                    self.table.setItem(i, j, table_item)
        finally:
            self.table.setUpdatesEnabled(True)

    def _update_summary(self):
        total_minutes = 0
        for item in self._results:
            rec = item["record"]
            if not rec.is_complete:
                continue
            d = calculate_duration(rec.entry_time or "", rec.exit_time or "")
            total_minutes += duration_to_minutes(d)

        self.lbl_summary.setText(
            "جمع کل مدت حضور: %s   |   تعداد: %d رکورد"
            % (minutes_to_duration(total_minutes), len(self._results))
        )

    # ==================== Exports ====================
    def _export_csv(self):
        if not self._results:
            show_warning(self, "نتیجه‌ای برای خروجی وجود ندارد")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره CSV", "attendance_report.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        headers = ["کد", "نام", "تاریخ", "ورود", "خروج",
                   "مدت حضور", "وضعیت", "توضیح"]
        rows = []
        for item in self._results:
            rec = item["record"]
            emp = item["employee"]
            duration = calculate_duration(rec.entry_time or "", rec.exit_time or "")
            rows.append([
                emp.personnel_code, emp.full_name, rec.jalali_date,
                rec.entry_time or "", rec.exit_time or "",
                duration or "", "کامل" if rec.is_complete else "ناقص",
                rec.description or "",
            ])

        try:
            export_to_csv(path, headers, rows)
            show_success(self, "فایل CSV ذخیره شد")
        except Exception as e:
            show_error(self, "خطا در ذخیره: %s" % e)

    def _export_pdf(self):
        if not self._results:
            show_warning(self, "نتیجه‌ای برای خروجی وجود ندارد")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره PDF", "attendance_report.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        headers = ["کد", "نام", "تاریخ", "ورود", "خروج",
                   "مدت حضور", "وضعیت", "توضیح"]
        rows = []
        for item in self._results:
            rec = item["record"]
            emp = item["employee"]
            duration = calculate_duration(rec.entry_time or "", rec.exit_time or "")
            rows.append([
                emp.personnel_code, emp.full_name, rec.jalali_date,
                rec.entry_time or "—", rec.exit_time or "—",
                duration or "—", "کامل" if rec.is_complete else "ناقص",
                rec.description or "—",
            ])

        try:
            export_to_pdf(
                path, "گزارش تردد پرسنل", headers, rows,
                summary_text=self.lbl_summary.text()
            )
            show_success(self, "فایل PDF ذخیره شد")
        except Exception as e:
            show_error(self, "خطا در ذخیره: %s" % e)