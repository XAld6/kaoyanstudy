"""CSV and multi-PDF ZIP export helpers."""

from __future__ import annotations

import csv
import io
import zipfile
from typing import Any

from app.reporting import build_pdf


def records_to_csv(records: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "filename",
            "created_at",
            "risk_level",
            "review_status",
            "confidence",
            "detection_count",
            "crack_count",
            "spalling_count",
            "stain_count",
            "total_area_ratio",
            "avg_confidence",
            "detector",
            "quality_grade",
            "quality_score",
            "readable",
            "risk_reason",
            "review_note",
        ]
    )
    for record in records:
        metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
        quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
        writer.writerow(
            [
                record.get("id", ""),
                record.get("filename", ""),
                record.get("created_at", ""),
                record.get("risk_level", ""),
                record.get("review_status", ""),
                f"{float(record.get('confidence') or 0):.4f}",
                record.get("detection_count", 0),
                metrics.get("crack_count", 0),
                metrics.get("spalling_count", 0),
                metrics.get("stain_count", 0),
                f"{float(metrics.get('total_area_ratio') or 0):.5f}",
                f"{float(metrics.get('avg_confidence') or record.get('confidence') or 0):.4f}",
                quality.get("detector_label") or quality.get("detector") or "",
                quality.get("quality_grade", ""),
                quality.get("quality_score", ""),
                quality.get("readable", ""),
                (record.get("risk_reason") or "").replace("\n", " "),
                (record.get("review_note") or "").replace("\n", " "),
            ]
        )
    # UTF-8 BOM for Excel
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def records_to_pdf_zip(records: list[dict[str, Any]]) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for record in records:
            record_id = record.get("id", "x")
            filename = str(record.get("filename") or f"record-{record_id}")
            safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in filename)
            pdf_name = f"damage-report-{record_id}-{safe[:40]}.pdf"
            zf.writestr(pdf_name, build_pdf(record))
        if not records:
            zf.writestr("README.txt", "No records matched the export filter.\n")
    return mem.getvalue()
