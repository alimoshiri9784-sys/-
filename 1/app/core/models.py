"""
مدل‌های داده (Dataclass)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    """مدل پرسنل"""
    id: Optional[int] = None
    personnel_code: str = ""
    first_name: str = ""
    last_name: str = ""
    national_code: Optional[str] = None
    birth_date: Optional[str] = None      # 1403/05/12
    hire_date: Optional[str] = None       # 1403/05/12
    position: Optional[str] = None
    photo_path: Optional[str] = None
    is_active: int = 1

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class AttendanceRecord:
    """مدل رکورد تردد"""
    id: Optional[int] = None
    employee_id: int = 0
    personnel_code: str = ""       # برای نمایش
    jalali_date: str = ""          # 1403/05/12
    entry_time: Optional[str] = None   # 08:15
    exit_time: Optional[str] = None    # 17:30
    description: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        return bool(self.entry_time) and bool(self.exit_time)