import sqlite3
import importlib

from app import storage


def test_storage_paths_can_be_configured_with_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("OPENCLAW_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("OPENCLAW_OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("OPENCLAW_DB_PATH", str(tmp_path / "custom.db"))

    reloaded = importlib.reload(storage)

    assert reloaded.DATA_DIR == tmp_path / "data"
    assert reloaded.UPLOAD_DIR == tmp_path / "uploads"
    assert reloaded.OUTPUT_DIR == tmp_path / "outputs"
    assert reloaded.DB_PATH == tmp_path / "custom.db"

    monkeypatch.delenv("OPENCLAW_DATA_DIR", raising=False)
    monkeypatch.delenv("OPENCLAW_UPLOAD_DIR", raising=False)
    monkeypatch.delenv("OPENCLAW_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("OPENCLAW_DB_PATH", raising=False)
    importlib.reload(storage)


def test_list_records_reads_only_summary_columns(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(storage, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "records.db")
    storage.init_db()

    with sqlite3.connect(storage.DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO records (
                filename, stored_filename, original_path, annotated_path, created_at,
                risk_level, risk_reason, review_status, review_note, confidence,
                detection_count, quality_json, detections_json, workflow_json, metrics_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "bridge.png",
                "stored.png",
                str(storage.UPLOAD_DIR / "stored.png"),
                str(storage.OUTPUT_DIR / "stored_annotated.png"),
                "2026-06-01 12:00:00",
                "中",
                "summary list should not need this",
                "待复核",
                "",
                0.82,
                3,
                "{invalid-json",
                "{invalid-json",
                "{invalid-json",
                "{invalid-json",
            ),
        )

    summaries = storage.list_records()

    assert summaries == [
        {
            "id": 1,
            "filename": "bridge.png",
            "created_at": "2026-06-01 12:00:00",
            "risk_level": "中",
            "review_status": "待复核",
            "confidence": 0.82,
            "detection_count": 3,
            "original_url": "/uploads/stored.png",
            "annotated_url": "/outputs/stored_annotated.png",
        }
    ]
