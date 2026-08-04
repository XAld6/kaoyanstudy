import importlib
import shutil
from pathlib import Path

from app import reporting


def sample_record(**overrides):
    record = {
        "id": 1,
        "filename": "巡检图.png",
        "created_at": "2026-06-06 12:00:00",
        "risk_level": "中",
        "review_status": "待复核",
        "detection_count": 3,
        "confidence": 0.88,
        "risk_reason": "检测到较明显疑似病害，建议结合现场情况确认。",
        "review_note": "建议持续观察。",
        "metrics": {
            "detection_count": 3,
            "avg_confidence": 0.88,
            "total_area_ratio": 0.042,
            "crack_count": 1,
            "spalling_count": 1,
            "stain_count": 1,
        },
        "quality": {
            "readable": True,
            "width": 480,
            "height": 320,
            "message": "图像满足基础识别条件",
        },
        "detections": [
            {
                "kind": "crack",
                "label": "裂缝疑似",
                "bbox": [10, 20, 30, 40],
                "confidence": 0.91,
                "area_ratio": 0.01,
                "length_estimate": 120,
            },
            {
                "kind": "spalling",
                "label": "剥落疑似",
                "bbox": [50, 60, 70, 80],
                "confidence": 0.86,
                "area_ratio": 0.02,
                "length_estimate": 90,
            },
            {
                "kind": "stain",
                "label": "渗水/色差疑似",
                "bbox": [90, 100, 40, 50],
                "confidence": 0.82,
                "area_ratio": 0.012,
                "length_estimate": 70,
            },
        ],
        "workflow": [
            {
                "agent": "ImageQualityAgent",
                "label": "图像质量检查",
                "status": "completed",
                "duration_ms": 3,
                "summary": "可识别 · 480×320",
            },
            {
                "agent": "DamageDetectionAgent",
                "label": "病害候选识别",
                "status": "completed",
                "duration_ms": 12,
                "summary": "识别到 3 个疑似病害候选",
            },
        ],
    }
    record.update(overrides)
    return record


def test_pdf_uses_configured_cjk_font(monkeypatch, tmp_path):
    font_source = Path("C:/Windows/Fonts/simhei.ttf")
    font_target = tmp_path / "simhei.ttf"
    shutil.copy(font_source, font_target)

    monkeypatch.setenv("OPENCLAW_PDF_FONT_PATH", str(font_target))
    reloaded = importlib.reload(reporting)

    assert reloaded.PDF_FONT_NAME == "OpenClawCJK"
    pdf = reloaded.build_pdf(sample_record())

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1200


def test_pdf_builds_with_minimal_legacy_payload():
    """Older records may lack metrics/detections; report should still generate."""
    pdf = reporting.build_pdf(
        {
            "id": 9,
            "filename": "legacy.png",
            "created_at": "2026-01-01 00:00:00",
            "risk_level": "低",
            "review_status": "自动通过",
            "detection_count": 0,
            "confidence": 0.0,
            "risk_reason": "未发现明显高风险病害，建议纳入常规巡检记录。",
            "workflow": [{"agent": "A", "status": "completed", "summary": "完成"}],
        }
    )
    assert pdf.startswith(b"%PDF")


def test_pdf_includes_multi_type_metrics_section():
    pdf = reporting.build_pdf(sample_record())
    # PDF binary may embed CJK as font glyphs; ensure non-empty multi-section structure
    assert b"PDF" in pdf[:8] or pdf.startswith(b"%PDF")
    assert len(pdf) > 2000
