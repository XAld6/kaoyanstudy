import importlib
import shutil
from pathlib import Path

from app import reporting


def test_pdf_uses_configured_cjk_font(monkeypatch, tmp_path):
    font_source = Path("C:/Windows/Fonts/simhei.ttf")
    font_target = tmp_path / "simhei.ttf"
    shutil.copy(font_source, font_target)

    monkeypatch.setenv("OPENCLAW_PDF_FONT_PATH", str(font_target))
    reloaded = importlib.reload(reporting)

    assert reloaded.PDF_FONT_NAME == "OpenClawCJK"
    pdf = reloaded.build_pdf(
        {
            "id": 1,
            "filename": "巡检图.png",
            "created_at": "2026-06-06 12:00:00",
            "risk_level": "中",
            "review_status": "待复核",
            "detection_count": 3,
            "confidence": 0.88,
            "risk_reason": "裂缝疑似区域较集中，建议人工复核。",
            "workflow": [{"agent": "A", "status": "completed", "summary": "完成"}],
        }
    )

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
