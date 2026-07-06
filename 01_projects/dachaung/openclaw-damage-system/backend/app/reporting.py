from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _font_candidates() -> list[Path]:
    env_font = os.getenv("OPENCLAW_PDF_FONT_PATH", "").strip()
    candidates = []
    if env_font:
        candidates.append(Path(env_font))
    candidates.extend(
        [
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
        ]
    )
    return candidates


def _select_font() -> str:
    for font_path in _font_candidates():
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("OpenClawCJK", str(font_path)))
            return "OpenClawCJK"
        except Exception:
            continue
    return "Helvetica"


PDF_FONT_NAME = _select_font()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("ReportTitle", parent=base["Title"], fontName=PDF_FONT_NAME),
        "heading": ParagraphStyle("ReportHeading", parent=base["Heading2"], fontName=PDF_FONT_NAME),
        "body": ParagraphStyle("ReportBody", parent=base["BodyText"], fontName=PDF_FONT_NAME),
    }


def build_pdf(record: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = _styles()

    story = [
        Paragraph("智爪识损巡检报告", styles["title"]),
        Spacer(1, 12),
        Paragraph("OpenClaw-compatible Agent Workflow Result", styles["heading"]),
    ]

    rows = [
        ["记录编号", str(record["id"])],
        ["文件名", record["filename"]],
        ["创建时间", record["created_at"]],
        ["风险等级", record["risk_level"]],
        ["复核状态", record["review_status"]],
        ["候选数量", str(record["detection_count"])],
        ["置信度", f"{record['confidence']:.2f}"],
        ["风险原因", record["risk_reason"]],
    ]
    table = Table(rows, colWidths=[110, 360])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8c2cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    story.extend([table, Spacer(1, 16), Paragraph("工作流", styles["heading"])])
    workflow_rows = [["Agent", "Status", "Summary"]]
    for step in record["workflow"]:
        workflow_rows.append([step["agent"], step["status"], step["summary"]])
    workflow_table = Table(workflow_rows, colWidths=[130, 70, 270])
    workflow_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263241")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5df")),
                ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(workflow_table)
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "This prototype is an intelligent auxiliary screening system, not a substitute for formal engineering inspection conclusions.",
            styles["body"],
        )
    )
    doc.build(story)
    return buffer.getvalue()
