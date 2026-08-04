from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
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

KIND_LABELS = {
    "crack": "裂缝",
    "spalling": "剥落",
    "stain": "渗水/色差",
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName=PDF_FONT_NAME,
            fontSize=18,
            leading=24,
            spaceAfter=6,
        ),
        "heading": ParagraphStyle(
            "ReportHeading",
            parent=base["Heading2"],
            fontName=PDF_FONT_NAME,
            fontSize=12,
            leading=16,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=9,
            leading=13,
        ),
        "cell": ParagraphStyle(
            "ReportCell",
            parent=base["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=8,
            leading=11,
        ),
    }


def _metric_value(metrics: dict | None, key: str, default: float | int = 0):
    if not isinstance(metrics, dict):
        return default
    value = metrics.get(key, default)
    return value if isinstance(value, (int, float)) else default


def _kv_table(rows: list[list[str]], col_widths: list[float] | None = None) -> Table:
    table = Table(rows, colWidths=col_widths or [110, 360])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8c2cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _header_table(rows: list[list[str]], col_widths: list[float]) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263241")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5df")),
                ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
            ]
        )
    )
    return table


def build_pdf(record: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = _styles()
    metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
    quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
    detections = record.get("detections") if isinstance(record.get("detections"), list) else []
    workflow = record.get("workflow") if isinstance(record.get("workflow"), list) else []

    crack_count = int(_metric_value(metrics, "crack_count", 0))
    spalling_count = int(_metric_value(metrics, "spalling_count", 0))
    stain_count = int(_metric_value(metrics, "stain_count", 0))
    total_area = float(_metric_value(metrics, "total_area_ratio", 0.0))
    avg_conf = float(_metric_value(metrics, "avg_confidence", record.get("confidence", 0.0) or 0.0))
    detection_count = int(record.get("detection_count") or _metric_value(metrics, "detection_count", len(detections)))

    quality_msg = str(quality.get("message") or ("图像满足基础识别条件" if quality.get("readable", True) else "图像质量偏低"))
    readable_text = "可识别" if quality.get("readable", True) else "需补拍/复核"
    detector_label = str(quality.get("detector_label") or quality.get("detector") or "OpenCV 规则初筛")
    review_note = str(record.get("review_note") or "").strip() or "（无）"

    story = [
        Paragraph("智爪识损巡检报告", styles["title"]),
        Paragraph("OpenClaw 兼容多 Agent 工作流 · 智能辅助初筛结果", styles["body"]),
        Spacer(1, 10),
        Paragraph("一、基本信息", styles["heading"]),
    ]

    basic_rows = [
        ["记录编号", str(record.get("id", ""))],
        ["文件名", str(record.get("filename", ""))],
        ["创建时间", str(record.get("created_at", ""))],
        ["风险等级", str(record.get("risk_level", ""))],
        ["复核状态", str(record.get("review_status", ""))],
        ["风险原因", str(record.get("risk_reason", ""))],
        ["复核意见", review_note],
    ]
    story.extend([_kv_table(basic_rows), Spacer(1, 12)])

    story.append(Paragraph("二、病害量化统计", styles["heading"]))
    grade = str(quality.get("quality_grade") or "-")
    qscore = quality.get("quality_score")
    qscore_text = f"{float(qscore):.1f}" if isinstance(qscore, (int, float)) else "-"
    issues = quality.get("issues") if isinstance(quality.get("issues"), list) else []
    issues_text = "、".join(str(x) for x in issues) if issues else "无"
    metric_rows = [
        ["候选总数", str(detection_count)],
        ["裂缝", f"{crack_count} 处"],
        ["剥落", f"{spalling_count} 处"],
        ["渗水/色差", f"{stain_count} 处"],
        ["平均置信度", f"{avg_conf:.2f}"],
        ["病害面积占比", f"{total_area * 100:.2f}%"],
        ["检测后端", detector_label],
        ["图像质量", f"{readable_text}（{quality_msg}）"],
        ["质量等级/评分", f"{grade} / {qscore_text}"],
        ["质量问题", issues_text],
    ]
    story.extend([_kv_table(metric_rows), Spacer(1, 12)])

    story.append(Paragraph("三、病害候选明细", styles["heading"]))
    det_rows: list[list[str]] = [["序号", "类型", "置信度", "面积占比", "长度(px)", "说明/坐标"]]
    ordered = sorted(
        [d for d in detections if isinstance(d, dict)],
        key=lambda item: float(item.get("confidence") or 0),
        reverse=True,
    )
    if ordered:
        for idx, item in enumerate(ordered, start=1):
            kind = str(item.get("kind") or "")
            label = str(item.get("label") or KIND_LABELS.get(kind, kind))
            conf = float(item.get("confidence") or 0)
            area = float(item.get("area_ratio") or 0)
            length = float(item.get("length_estimate") or 0)
            bbox = item.get("bbox") or []
            bbox_text = ", ".join(str(int(v)) for v in bbox) if isinstance(bbox, list) else str(bbox)
            explain = str(item.get("explanation") or "").strip()
            note = explain if explain else f"坐标 {bbox_text}"
            if explain and bbox_text:
                note = f"{explain}；坐标 {bbox_text}"
            det_rows.append(
                [
                    str(idx),
                    label,
                    f"{conf * 100:.0f}%",
                    f"{area * 100:.2f}%",
                    f"{length:.0f}",
                    note[:80],
                ]
            )
    else:
        det_rows.append(["-", "未发现明显病害候选", "-", "-", "-", "-"])

    story.extend(
        [
            _header_table(det_rows, [28, 58, 42, 50, 48, 244]),
            Spacer(1, 12),
            Paragraph("四、OpenClaw 工作流", styles["heading"]),
        ]
    )

    workflow_rows: list[list[str]] = [["#", "Agent", "步骤", "状态", "耗时(ms)", "摘要"]]
    if workflow:
        for idx, step in enumerate(workflow, start=1):
            if not isinstance(step, dict):
                continue
            workflow_rows.append(
                [
                    str(idx),
                    str(step.get("agent") or ""),
                    str(step.get("label") or ""),
                    str(step.get("status") or ""),
                    str(step.get("duration_ms") or ""),
                    str(step.get("summary") or ""),
                ]
            )
    else:
        workflow_rows.append(["-", "-", "-", "-", "-", "无工作流日志"])

    story.extend(
        [
            _header_table(workflow_rows, [22, 95, 70, 45, 45, 193]),
            Spacer(1, 14),
            Paragraph(
                "说明：本报告由「智爪识损」原型系统自动生成，用于智能辅助初筛与项目演示，"
                f"不替代正式工程检测结论。本次检测后端：{detector_label}。"
                "系统支持 OpenCV 规则初筛，并可配置切换 YOLO 深度模型；结果需结合现场复核。",
                styles["body"],
            ),
            Spacer(1, 4),
            Paragraph(
                "This prototype is an intelligent auxiliary screening system, not a substitute for formal engineering inspection conclusions.",
                styles["body"],
            ),
        ]
    )

    doc.build(story)
    return buffer.getvalue()
