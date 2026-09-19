"""
صفحه ۱: ثبت تردد (خودکار)
- کاربر فقط کد پرسنلی را وارد می‌کند
- سیستم خودش ورود یا خروج را تشخیص می‌دهد
- کارت اطلاعات با آواتار + Badge
- جدول با Badge وضعیت
"""
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QStackedWidget
)

from app.core.database import Database
from app.core.models import Employee, AttendanceRecord
from app.core.time_service import TimeService
from app.utils.jalali_utils import jalali_from_datetime
from app.utils.validators import normalize_digits
from app.ui.icons import icon as svg_icon
from app.ui.widgets.empty_state import EmptyState, Avatar
from app.ui.widgets.toast import show_success, show_error, show_warning
from app.ui.widgets.animations import apply_card_shadows


class AttendancePage(QWidget):
    """صفحه ثبت تردد خودکار"""

    dataChanged = Signal()

    def __init__(self, db: Database, time_service: TimeService, parent=None):
        super().__init__(parent)
        self.db = db
        self.time_service = time_service

        self._build_ui()
        apply_card_shadows(self)
        self.reload_today_table()
        self._clear_info_card()
        QTimer.singleShot(100, lambda: self.code_input.setFocus())

    # ==================== ساخت UI ====================
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ---------- کارت ورودی ----------
        input_card = QFrame()
        input_card.setObjectName("Card")
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(28, 22, 28, 22)
        input_layout.setSpacing(14)
        input_layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel("کد پرسنلی:")
        lbl.setObjectName("FieldLabel")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("کد پرسنلی را وارد کنید...")
        self.code_input.setLayoutDirection(Qt.LeftToRight)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setMaxLength(20)
        self.code_input.setFixedWidth(260)
        self.code_input.setMinimumHeight(46)
        self.code_input.returnPressed.connect(self._register_attendance)
        self.code_input.textChanged.connect(self._on_code_changed)

        self.btn_submit = QPushButton("  ثبت تردد")
        self.btn_submit.setObjectName("Primary")
        self.btn_submit.setIcon(svg_icon("check-circle", "#FFFFFF", 18))
        self.btn_submit.setIconSize(QSize(18, 18))
        self.btn_submit.setMinimumHeight(46)
        self.btn_submit.setMinimumWidth(180)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._register_attendance)

        input_layout.addStretch(1)
        input_layout.addWidget(lbl)
        input_layout.addWidget(self.code_input)
        input_layout.addWidget(self.btn_submit)
        input_layout.addStretch(1)

        root.addWidget(input_card)

        # ---------- کارت اطلاعات پرسنل ----------
        # چیدمان: آواتار | نام+سمت | وضعیت | تردد بعدی
        self.info_frame = QFrame()
        self.info_frame.setObjectName("Card")

        info_layout = QHBoxLayout(self.info_frame)
        info_layout.setContentsMargins(28, 20, 28, 20)
        info_layout.setSpacing(22)

        # آواتار
        self.avatar = Avatar("", size=64)
        info_layout.addWidget(self.avatar, 0, Qt.AlignVCenter)

        # بلوک ۱: نام + سمت
        name_box = QVBoxLayout()
        name_box.setSpacing(4)
        name_box.setAlignment(Qt.AlignVCenter)

        lbl_name_title = QLabel("نام و نام خانوادگی")
        lbl_name_title.setStyleSheet("color: #9099A5; font-size: 11px;")
        lbl_name_title.setAlignment(Qt.AlignRight)

        self.lbl_name = QLabel("—")
        self.lbl_name.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #1A1D21;"
        )
        self.lbl_name.setAlignment(Qt.AlignRight)

        lbl_pos_title = QLabel("سمت")
        lbl_pos_title.setStyleSheet("color: #9099A5; font-size: 11px;")
        lbl_pos_title.setAlignment(Qt.AlignRight)

        self.lbl_position = QLabel("—")
        self.lbl_position.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1A1D21;"
        )
        self.lbl_position.setAlignment(Qt.AlignRight)

        name_box.addWidget(lbl_name_title)
        name_box.addWidget(self.lbl_name)
        name_box.addSpacing(4)
        name_box.addWidget(lbl_pos_title)
        name_box.addWidget(self.lbl_position)

        info_layout.addLayout(name_box, 2)

        # جداکننده ۱
        sep1 = QFrame()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: #E8EAED;")
        info_layout.addWidget(sep1)

        # بلوک ۲: وضعیت امروز
        today_box = QVBoxLayout()
        today_box.setSpacing(6)
        today_box.setAlignment(Qt.AlignVCenter)

        lbl_today_title = QLabel("وضعیت امروز")
        lbl_today_title.setStyleSheet("color: #9099A5; font-size: 11px;")
        lbl_today_title.setAlignment(Qt.AlignRight)

        self.badge_today = QLabel("—")
        self.badge_today.setStyleSheet(
            "background: #F0F1F4; color: #6E7480; padding: 8px 14px; "
            "border-radius: 10px; font-size: 13px; font-weight: 700;"
        )
        self.badge_today.setAlignment(Qt.AlignCenter)

        today_box.addWidget(lbl_today_title)
        today_box.addWidget(self.badge_today)

        info_layout.addLayout(today_box, 1)

        # جداکننده ۲
        sep2 = QFrame()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: #E8EAED;")
        info_layout.addWidget(sep2)

        # بلوک ۳: تردد بعدی
        next_box = QVBoxLayout()
        next_box.setSpacing(6)
        next_box.setAlignment(Qt.AlignVCenter)

        lbl_next_title = QLabel("تردد بعدی")
        lbl_next_title.setStyleSheet("color: #9099A5; font-size: 11px;")
        lbl_next_title.setAlignment(Qt.AlignRight)

        self.badge_next = QLabel("—")
        self.badge_next.setStyleSheet(
            "background: #F0F1F4; color: #6E7480; padding: 8px 14px; "
            "border-radius: 10px; font-size: 13px; font-weight: 700;"
        )
        self.badge_next.setAlignment(Qt.AlignCenter)

        next_box.addWidget(lbl_next_title)
        next_box.addWidget(self.badge_next)

        info_layout.addLayout(next_box, 1)

        root.addWidget(self.info_frame)

        # ---------- جدول امروز ----------
        table_group = QGroupBox("📋 لیست ترددهای امروز")
        table_group.setLayoutDirection(Qt.RightToLeft)
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 20, 10, 10)

        self.table_stack = QStackedWidget()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "کد پرسنلی", "نام", "سمت", "ورود", "خروج", "وضعیت"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.empty_state = EmptyState(
            icon_name="clock",
            title="هنوز ترددی ثبت نشده است",
            subtitle="اولین تردد امروز را از کادر بالا ثبت کنید",
        )

        self.table_stack.addWidget(self.table)
        self.table_stack.addWidget(self.empty_state)

        table_layout.addWidget(self.table_stack)
        root.addWidget(table_group, 1)

    # ==================== نرمال‌سازی ====================
    def _on_code_changed(self, text: str) -> None:
        norm = normalize_digits(text)
        if norm != text:
            self.code_input.blockSignals(True)
            self.code_input.setText(norm)
            self.code_input.blockSignals(False)

    def _today_str(self) -> str:
        ts = self.time_service.get_tehran_now()
        return jalali_from_datetime(ts.tehran_now)

    # ==================== ثبت تردد ====================
    def _register_attendance(self) -> None:
        code = self.code_input.text().strip()
        if not code:
            show_warning(self, "کد پرسنلی را وارد کنید")
            self.code_input.setFocus()
            return

        emp = self.db.get_employee_by_code(code)
        if not emp:
            show_error(self, "پرسنلی با کد «%s» یافت نشد" % code)
            self.code_input.selectAll()
            self.code_input.setFocus()
            return

        today = self._today_str()
        now_time = self.time_service.get_tehran_now().tehran_now.strftime("%H:%M")

        records = self.db.get_attendance_by_employee_date(emp.id, today)
        last = records[-1] if records else None

        if last is None:
            action = "ورود"
            self.db.add_attendance(AttendanceRecord(
                employee_id=emp.id,
                jalali_date=today,
                entry_time=now_time,
                exit_time=None,
                description=None,
            ))
        elif last.entry_time and not last.exit_time:
            action = "خروج"
            self.db.update_attendance(AttendanceRecord(
                id=last.id,
                employee_id=last.employee_id,
                jalali_date=last.jalali_date,
                entry_time=last.entry_time,
                exit_time=now_time,
                description=last.description,
            ))
        else:
            action = "ورود (شیفت جدید)"
            self.db.add_attendance(AttendanceRecord(
                employee_id=emp.id,
                jalali_date=today,
                entry_time=now_time,
                exit_time=None,
                description=None,
            ))

        self._show_employee_info(emp, today)
        show_success(self, "✓ %s ثبت شد — %s — %s" % (action, emp.full_name, now_time))

        self.code_input.clear()
        self.code_input.setFocus()
        self.dataChanged.emit()
        self.reload_today_table()

    # ==================== نمایش اطلاعات ====================
    def _show_employee_info(self, emp: Employee, today: str) -> None:
        records = self.db.get_attendance_by_employee_date(emp.id, today)

        self.avatar.set_name(emp.full_name)
        self.lbl_name.setText(emp.full_name)
        self.lbl_position.setText(emp.position or "—")

        if not records:
            self.badge_today.setText("بدون تردد امروز")
            self.badge_today.setStyleSheet(
                "background: #F0F1F4; color: #6E7480; padding: 8px 14px; "
                "border-radius: 10px; font-size: 13px; font-weight: 700;"
            )
            self.badge_next.setText("ورود (شروع اولین شیفت)")
            self.badge_next.setStyleSheet(
                "background: #E8F8F2; color: #10B981; padding: 8px 14px; "
                "border-radius: 10px; font-size: 13px; font-weight: 700;"
            )
        else:
            last = records[-1]
            complete = [r for r in records if r.is_complete]

            if last.entry_time and not last.exit_time:
                self.badge_today.setText(
                    "%d شیفت کامل + ۱ باز" % len(complete)
                )
                self.badge_today.setStyleSheet(
                    "background: #FEF3C7; color: #F59E0B; padding: 8px 14px; "
                    "border-radius: 10px; font-size: 13px; font-weight: 700;"
                )
                self.badge_next.setText("خروج (بستن شیفت)")
                self.badge_next.setStyleSheet(
                    "background: #FDECEC; color: #EF4444; padding: 8px 14px; "
                    "border-radius: 10px; font-size: 13px; font-weight: 700;"
                )
            else:
                self.badge_today.setText("%d شیفت کامل" % len(complete))
                self.badge_today.setStyleSheet(
                    "background: #E8F8F2; color: #10B981; padding: 8px 14px; "
                    "border-radius: 10px; font-size: 13px; font-weight: 700;"
                )
                self.badge_next.setText("ورود (شیفت جدید)")
                self.badge_next.setStyleSheet(
                    "background: #E8F8F2; color: #10B981; padding: 8px 14px; "
                    "border-radius: 10px; font-size: 13px; font-weight: 700;"
                )

    def _clear_info_card(self) -> None:
        self.avatar.set_name("")
        self.lbl_name.setText("—")
        self.lbl_position.setText("—")

        self.badge_today.setText("منتظر ورود کد پرسنلی...")
        self.badge_today.setStyleSheet(
            "background: #F0F1F4; color: #9099A5; padding: 8px 14px; "
            "border-radius: 10px; font-size: 13px; font-weight: 700;"
        )

        self.badge_next.setText("—")
        self.badge_next.setStyleSheet(
            "background: #F0F1F4; color: #9099A5; padding: 8px 14px; "
            "border-radius: 10px; font-size: 13px; font-weight: 700;"
        )

    # ==================== جدول امروز ====================
    def reload_today_table(self) -> None:
        today = self._today_str()
        employees = self.db.get_all_active_employees()
        all_recs = self.db.get_today_attendance_for_all(today)

        recs_by_emp = {}
        for r in all_recs:
            recs_by_emp.setdefault(r.employee_id, []).append(r)

        rows = []
        for emp in employees:
            recs = recs_by_emp.get(emp.id, [])
            if not recs:
                rows.append((emp, None))
            else:
                for r in recs:
                    rows.append((emp, r))

        if not rows:
            self.table_stack.setCurrentIndex(1)
            return

        self.table_stack.setCurrentIndex(0)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(rows))
            for i, (emp, rec) in enumerate(rows):
                entry = rec.entry_time if rec and rec.entry_time else "—"
                exit_ = rec.exit_time if rec and rec.exit_time else "—"

                if rec and rec.is_complete:
                    badge_text, badge_obj = "✓ کامل", "BadgeSuccess"
                elif rec and (rec.entry_time or rec.exit_time):
                    badge_text, badge_obj = "⚠ ناقص", "BadgeDanger"
                else:
                    badge_text, badge_obj = "—", "Caption"

                cells = [
                    emp.personnel_code,
                    emp.full_name,
                    emp.position or "—",
                    entry,
                    exit_,
                ]
                for j, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    if j in (0, 3, 4):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(i, j, item)

                badge_widget = QWidget()
                badge_layout = QHBoxLayout(badge_widget)
                badge_layout.setContentsMargins(6, 4, 6, 4)
                badge_layout.setAlignment(Qt.AlignCenter)
                badge_label = QLabel(badge_text)
                badge_label.setObjectName(badge_obj)
                badge_label.setAlignment(Qt.AlignCenter)
                badge_layout.addWidget(badge_label)
                self.table.setCellWidget(i, 5, badge_widget)
        finally:
            self.table.setUpdatesEnabled(True)