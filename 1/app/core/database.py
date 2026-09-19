"""
مدیریت اتصال و اسکیمای SQLite
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional, List

from app.core.config import DB_PATH
from app.core.models import Employee, AttendanceRecord


class Database:
    """کلاس مدیریت دیتابیس"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path) if db_path else str(DB_PATH)
        self._init_schema()

    # ---------- اتصال ----------
    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------- ساخت اسکیما ----------
    def _init_schema(self) -> None:
        with self.connection() as conn:
            cur = conn.cursor()

            # جدول پرسنل
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    personnel_code  TEXT    NOT NULL UNIQUE,
                    first_name      TEXT    NOT NULL,
                    last_name       TEXT    NOT NULL,
                    national_code   TEXT    UNIQUE,
                    birth_date      TEXT,
                    hire_date       TEXT,
                    position        TEXT,
                    photo_path      TEXT,
                    is_active       INTEGER NOT NULL DEFAULT 1,
                    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migration: اگر ستون photo_path در نسخه قدیمی نبود، اضافه کن
            cur.execute("PRAGMA table_info(employees)")
            cols = [row["name"] for row in cur.fetchall()]
            if "photo_path" not in cols:
                cur.execute("ALTER TABLE employees ADD COLUMN photo_path TEXT")

            # جدول تردد
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id     INTEGER NOT NULL,
                    jalali_date     TEXT    NOT NULL,
                    entry_time      TEXT,
                    exit_time       TEXT,
                    description     TEXT,
                    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            """)

            # جدول تنظیمات
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key     TEXT PRIMARY KEY,
                    value   TEXT
                )
            """)

    # ---------- تنظیمات ----------
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO settings(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))

    # ---------- پرسنل ----------
    def count_active_employees(self) -> int:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM employees WHERE is_active = 1"
            ).fetchone()
            return row["c"]

    def get_employee_by_code(self, code: str) -> Optional[Employee]:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE personnel_code = ? AND is_active = 1",
                (code,)
            ).fetchone()
            return self._row_to_employee(row) if row else None

    def get_employee_by_id(self, emp_id: int) -> Optional[Employee]:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE id = ?", (emp_id,)
            ).fetchone()
            return self._row_to_employee(row) if row else None

    def get_all_active_employees(self) -> List[Employee]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM employees WHERE is_active = 1 "
                "ORDER BY personnel_code"
            ).fetchall()
            return [self._row_to_employee(r) for r in rows]

    def is_personnel_code_taken(self, code: str,
                                 exclude_id: Optional[int] = None) -> bool:
        with self.connection() as conn:
            if exclude_id:
                row = conn.execute(
                    "SELECT 1 FROM employees WHERE personnel_code = ? AND id != ?",
                    (code, exclude_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM employees WHERE personnel_code = ?", (code,)
                ).fetchone()
            return row is not None

    def is_national_code_taken(self, national_code: str,
                                exclude_id: Optional[int] = None) -> bool:
        if not national_code:
            return False
        with self.connection() as conn:
            if exclude_id:
                row = conn.execute(
                    "SELECT 1 FROM employees WHERE national_code = ? AND id != ?",
                    (national_code, exclude_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM employees WHERE national_code = ?",
                    (national_code,)
                ).fetchone()
            return row is not None

    def add_employee(self, emp: Employee) -> int:
        with self.connection() as conn:
            cur = conn.execute("""
                INSERT INTO employees
                    (personnel_code, first_name, last_name, national_code,
                     birth_date, hire_date, position, photo_path, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp.personnel_code, emp.first_name, emp.last_name,
                emp.national_code or None, emp.birth_date, emp.hire_date,
                emp.position, emp.photo_path, 1
            ))
            return cur.lastrowid

    def update_employee(self, emp: Employee) -> None:
        with self.connection() as conn:
            conn.execute("""
                UPDATE employees SET
                    personnel_code = ?, first_name = ?, last_name = ?,
                    national_code = ?, birth_date = ?, hire_date = ?,
                    position = ?, photo_path = ?
                WHERE id = ?
            """, (
                emp.personnel_code, emp.first_name, emp.last_name,
                emp.national_code or None, emp.birth_date, emp.hire_date,
                emp.position, emp.photo_path, emp.id
            ))

    def deactivate_employee(self, emp_id: int) -> None:
        with self.connection() as conn:
            conn.execute(
                "UPDATE employees SET is_active = 0 WHERE id = ?", (emp_id,)
            )

    # ---------- تردد ----------
    def get_attendance_by_employee_date(self, employee_id: int,
                                         jalali_date: str) -> List[AttendanceRecord]:
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT a.*, e.personnel_code
                FROM attendance a
                JOIN employees e ON e.id = a.employee_id
                WHERE a.employee_id = ? AND a.jalali_date = ?
                ORDER BY a.id
            """, (employee_id, jalali_date)).fetchall()
            return [self._row_to_attendance(r) for r in rows]

    def add_attendance(self, rec: AttendanceRecord) -> int:
        with self.connection() as conn:
            cur = conn.execute("""
                INSERT INTO attendance
                    (employee_id, jalali_date, entry_time, exit_time, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rec.employee_id, rec.jalali_date,
                rec.entry_time, rec.exit_time, rec.description
            ))
            return cur.lastrowid

    def update_attendance(self, rec: AttendanceRecord) -> None:
        with self.connection() as conn:
            conn.execute("""
                UPDATE attendance SET
                    employee_id = ?, jalali_date = ?,
                    entry_time = ?, exit_time = ?, description = ?
                WHERE id = ?
            """, (
                rec.employee_id, rec.jalali_date,
                rec.entry_time, rec.exit_time, rec.description, rec.id
            ))

    def delete_attendance(self, rec_id: int) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM attendance WHERE id = ?", (rec_id,))

    def get_attendance_by_id(self, rec_id: int) -> Optional[AttendanceRecord]:
        with self.connection() as conn:
            row = conn.execute("""
                SELECT a.*, e.personnel_code
                FROM attendance a
                JOIN employees e ON e.id = a.employee_id
                WHERE a.id = ?
            """, (rec_id,)).fetchone()
            return self._row_to_attendance(row) if row else None

    def get_recent_attendance(self, limit: int = 500) -> List[AttendanceRecord]:
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT a.*, e.personnel_code
                FROM attendance a
                JOIN employees e ON e.id = a.employee_id
                ORDER BY a.id DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [self._row_to_attendance(r) for r in rows]

    def get_today_attendance_for_all(self, jalali_date: str) -> list:
        """همه رکوردهای امروز در یک کوئری (بهینه)"""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT a.*, e.personnel_code
                FROM attendance a
                JOIN employees e ON e.id = a.employee_id
                WHERE a.jalali_date = ?
                ORDER BY a.employee_id, a.id
            """, (jalali_date,)).fetchall()
            return [self._row_to_attendance(r) for r in rows]

    # ---------- تبدیل Row → Dataclass ----------
    @staticmethod
    def _row_to_employee(row: sqlite3.Row) -> Employee:
        keys = row.keys()
        return Employee(
            id=row["id"],
            personnel_code=row["personnel_code"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            national_code=row["national_code"],
            birth_date=row["birth_date"],
            hire_date=row["hire_date"],
            position=row["position"],
            photo_path=row["photo_path"] if "photo_path" in keys else None,
            is_active=row["is_active"],
        )

    @staticmethod
    def _row_to_attendance(row: sqlite3.Row) -> AttendanceRecord:
        keys = row.keys()
        return AttendanceRecord(
            id=row["id"],
            employee_id=row["employee_id"],
            personnel_code=row["personnel_code"] if "personnel_code" in keys else "",
            jalali_date=row["jalali_date"],
            entry_time=row["entry_time"],
            exit_time=row["exit_time"],
            description=row["description"],
        )