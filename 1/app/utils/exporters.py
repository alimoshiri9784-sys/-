"""
خروجی CSV و PDF
- PDF با پشتیبانی کامل از فارسی (RTL)
"""
import csv
from pathlib import Path
from typing import List

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from app.core.config import PDF_FONT_NAME, PDF_FONT_PATH

# کتابخانه‌های فارسی‌سازی
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RTL_AVAILABLE = True
except ImportError:
    _RTL_AVAILABLE = False


# ---------- ثبت فونت ----------
_FONT_REGISTERED = False


def _ensure_font_registered() -> bool:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return True
    try:
        if Path(PDF_FONT_PATH).exists():
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(PDF_FONT_PATH)))
            _FONT_REGISTERED = True
            return True
    except Exception:
        pass
    return False


def _fa(text) -> str:
    """
    تبدیل متن فارسی برای ReportLab (RTL + اتصال حروف)
    اگر کتابخانه‌ها نصب نباشند، متن اصلی برمی‌گردد.
    """
    if text is None:
        return ""
    text = str(text)
    if not text:
        return ""
    if not _RTL_AVAILABLE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


# ---------- CSV ----------
def export_to_csv(file_path: str, headers: List[str],
                  rows: List[List[str]]) -> None:
    """خروجی CSV با UTF-8-sig برای Excel فارسی"""
    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


# ---------- PDF ----------
def export_to_pdf(file_path: str, title: str, headers: List[str],
                  rows: List[List[str]], summary_text: str = "") -> None:
    """خروجی PDF با فونت فارسی و RTL"""
    font_ok = _ensure_font_registered()
    font_name = PDF_FONT_NAME if font_ok else "Helvetica"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    # استایل‌ها
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName=font_name,
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=6 * mm,
    )
    cell_style = ParagraphStyle(
        name="CellStyle",
        fontName=font_name,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        leading=13,
    )
    summary_style = ParagraphStyle(
        name="SummaryStyle",
        fontName=font_name,
        fontSize=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#FF6B35"),
        spaceBefore=6 * mm,
    )

    story = []

    # عنوان
    story.append(Paragraph(_fa(title), title_style))

    # جدول: هدر + داده‌ها
    table_data = []

    # هدر (فارسی‌سازی‌شده)
    header_row = [
        Paragraph(f"<b>{_fa(h)}</b>", cell_style) for h in headers
    ]
    table_data.append(header_row)

    # داده‌ها
    for row in rows:
        table_data.append([
            Paragraph(_fa(str(c)) if c is not None else "", cell_style)
            for c in row
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        # هدر
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF1EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FF6B35")),
        ("FONTNAME", (0, 0), (-1, 0), font_name),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # بدنه
        ("FONTNAME", (0, 1), (-1, -1), font_name),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        # خطوط
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E8EAED")),

        # رنگ‌های متناوب
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#FAFBFC")]),

        # Padding
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]))

    story.append(table)

    # جمع کل
    if summary_text:
        story.append(Paragraph(_fa(summary_text), summary_style))

    doc.build(story)