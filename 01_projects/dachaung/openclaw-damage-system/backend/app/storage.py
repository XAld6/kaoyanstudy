import json
import os
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("OPENCLAW_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = Path(os.getenv("OPENCLAW_UPLOAD_DIR", BASE_DIR / "uploads"))
OUTPUT_DIR = Path(os.getenv("OPENCLAW_OUTPUT_DIR", BASE_DIR / "outputs"))
DB_PATH = Path(os.getenv("OPENCLAW_DB_PATH", DATA_DIR / "records.db"))


def ensure_dirs() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                original_path TEXT NOT NULL,
                annotated_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_reason TEXT NOT NULL,
                review_status TEXT NOT NULL,
                review_note TEXT NOT NULL DEFAULT '',
                confidence REAL NOT NULL,
                detection_count INTEGER NOT NULL,
                quality_json TEXT NOT NULL,
                detections_json TEXT NOT NULL,
                workflow_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL
            )
            """
        )


def insert_record(payload: dict[str, Any]) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO records (
                filename, stored_filename, original_path, annotated_path, created_at,
                risk_level, risk_reason, review_status, review_note, confidence,
                detection_count, quality_json, detections_json, workflow_json, metrics_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["filename"],
                payload["stored_filename"],
                payload["original_path"],
                payload["annotated_path"],
                payload["created_at"],
                payload["risk_level"],
                payload["risk_reason"],
                payload["review_status"],
                payload.get("review_note", ""),
                payload["confidence"],
                payload["detection_count"],
                json.dumps(payload["quality"], ensure_ascii=False),
                json.dumps(payload["detections"], ensure_ascii=False),
                json.dumps(payload["workflow"], ensure_ascii=False),
                json.dumps(payload["metrics"], ensure_ascii=False),
            ),
        )
        return int(cur.lastrowid)


def row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    record = row_to_summary(row)
    record.update(
        {
            "risk_reason": row["risk_reason"],
            "review_note": row["review_note"],
            "quality": json.loads(row["quality_json"]),
            "detections": json.loads(row["detections_json"]),
            "workflow": json.loads(row["workflow_json"]),
            "metrics": json.loads(row["metrics_json"]),
        }
    )
    return record


def row_to_summary(row: sqlite3.Row) -> dict[str, Any]:
    original_name = Path(row["original_path"]).name
    annotated_name = Path(row["annotated_path"]).name
    return {
        "id": row["id"],
        "filename": row["filename"],
        "created_at": row["created_at"],
        "risk_level": row["risk_level"],
        "review_status": row["review_status"],
        "confidence": row["confidence"],
        "detection_count": row["detection_count"],
        "original_url": f"/uploads/{original_name}",
        "annotated_url": f"/outputs/{annotated_name}",
    }


def list_records() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                id, filename, original_path, annotated_path, created_at,
                risk_level, review_status, confidence, detection_count
            FROM records
            ORDER BY id DESC
            """
        ).fetchall()
    return [row_to_summary(row) for row in rows]


def get_record(record_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    return row_to_record(row) if row else None


def update_review(record_id: int, status: str, risk_level: str, note: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            "UPDATE records SET review_status = ?, risk_level = ?, review_note = ? WHERE id = ?",
            (status, risk_level, note, record_id),
        )
    return get_record(record_id)
