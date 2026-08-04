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

SORT_FIELDS = {
    "id": "id",
    "created_at": "created_at",
    "confidence": "confidence",
    "detection_count": "detection_count",
    "risk_level": "risk_level",
    "filename": "filename",
    "review_status": "review_status",
}


def ensure_dirs() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
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
        # indexes for filter / sort / review queue
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_risk ON records(risk_level)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_review ON records(review_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_created ON records(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_conf ON records(confidence)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_filename ON records(filename)")


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
            "original_path": row["original_path"],
            "annotated_path": row["annotated_path"],
            "stored_filename": row["stored_filename"] if "stored_filename" in row.keys() else "",
            "quality": json.loads(row["quality_json"]),
            "detections": json.loads(row["detections_json"]),
            "workflow": json.loads(row["workflow_json"]),
            "metrics": json.loads(row["metrics_json"]),
        }
    )
    return record


def _metrics_kind_counts(metrics_json: str | None) -> dict[str, int]:
    try:
        metrics = json.loads(metrics_json or "{}")
    except (TypeError, json.JSONDecodeError):
        metrics = {}
    if not isinstance(metrics, dict):
        metrics = {}
    return {
        "crack_count": int(metrics.get("crack_count") or 0),
        "spalling_count": int(metrics.get("spalling_count") or 0),
        "stain_count": int(metrics.get("stain_count") or 0),
    }


def row_to_summary(row: sqlite3.Row) -> dict[str, Any]:
    original_name = Path(row["original_path"]).name
    annotated_name = Path(row["annotated_path"]).name
    keys = set(row.keys())
    kind_counts = (
        _metrics_kind_counts(row["metrics_json"])
        if "metrics_json" in keys
        else {"crack_count": 0, "spalling_count": 0, "stain_count": 0}
    )
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
        **kind_counts,
    }


def _filter_clause(
    risk_level: str | None = None,
    review_status: str | None = None,
    q: str | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if risk_level:
        clauses.append("risk_level = ?")
        params.append(risk_level)
    if review_status:
        clauses.append("review_status = ?")
        params.append(review_status)
    if q:
        clauses.append("filename LIKE ?")
        params.append(f"%{q}%")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def _order_clause(sort: str | None = None, order: str | None = None) -> str:
    field = SORT_FIELDS.get((sort or "id").strip().lower(), "id")
    direction = "ASC" if (order or "desc").strip().lower() == "asc" else "DESC"
    # stable secondary key
    if field == "id":
        return f"ORDER BY id {direction}"
    return f"ORDER BY {field} {direction}, id DESC"


def list_records(
    risk_level: str | None = None,
    review_status: str | None = None,
    q: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    ids: list[int] | None = None,
    sort: str | None = None,
    order: str | None = None,
) -> list[dict[str, Any]]:
    where, params = _filter_clause(risk_level, review_status, q)
    if ids:
        placeholders = ",".join("?" for _ in ids)
        id_clause = f"id IN ({placeholders})"
        if where:
            where = f"{where} AND {id_clause}"
        else:
            where = f" WHERE {id_clause}"
        params.extend(int(i) for i in ids)

    sql = f"""
        SELECT
            id, filename, original_path, annotated_path, created_at,
            risk_level, review_status, confidence, detection_count, metrics_json
        FROM records
        {where}
        {_order_clause(sort, order)}
    """
    if limit is not None and limit > 0:
        sql += " LIMIT ?"
        params.append(int(limit))
        if offset is not None and offset > 0:
            sql += " OFFSET ?"
            params.append(int(offset))

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_summary(row) for row in rows]


def count_records(
    risk_level: str | None = None,
    review_status: str | None = None,
    q: str | None = None,
    ids: list[int] | None = None,
) -> int:
    where, params = _filter_clause(risk_level, review_status, q)
    if ids:
        placeholders = ",".join("?" for _ in ids)
        id_clause = f"id IN ({placeholders})"
        if where:
            where = f"{where} AND {id_clause}"
        else:
            where = f" WHERE {id_clause}"
        params.extend(int(i) for i in ids)
    with connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS c FROM records{where}", params).fetchone()
    return int(row["c"] if row else 0)


def list_records_page(
    risk_level: str | None = None,
    review_status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort: str | None = None,
    order: str | None = None,
    ids: list[int] | None = None,
) -> dict[str, Any]:
    page = max(1, int(page))
    page_size = max(1, min(100, int(page_size)))
    total = count_records(risk_level=risk_level, review_status=review_status, q=q, ids=ids)
    offset = (page - 1) * page_size
    items = list_records(
        risk_level=risk_level,
        review_status=review_status,
        q=q,
        limit=page_size,
        offset=offset,
        ids=ids,
        sort=sort,
        order=order,
    )
    pages = max(1, (total + page_size - 1) // page_size) if total else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def get_record(record_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    return row_to_record(row) if row else None


def neighbor_ids(record_id: int, risk_level: str | None = None, review_status: str | None = None, q: str | None = None) -> dict[str, int | None]:
    """Return previous/next record ids within the same filter (id DESC list order)."""
    items = list_records(risk_level=risk_level, review_status=review_status, q=q, sort="id", order="desc")
    ids = [int(item["id"]) for item in items]
    if record_id not in ids:
        return {"prev_id": None, "next_id": None}
    idx = ids.index(record_id)
    # list is newest first: prev = older index-1? For UI "上一条"=previous in list = smaller index
    prev_id = ids[idx - 1] if idx > 0 else None
    next_id = ids[idx + 1] if idx + 1 < len(ids) else None
    return {"prev_id": prev_id, "next_id": next_id}


def update_review(record_id: int, status: str, risk_level: str, note: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            "UPDATE records SET review_status = ?, risk_level = ?, review_note = ? WHERE id = ?",
            (status, risk_level, note, record_id),
        )
    return get_record(record_id)


def batch_update_review(
    record_ids: list[int],
    *,
    status: str,
    risk_level: str | None = None,
    note: str | None = None,
    keep_risk: bool = True,
    append_note: bool = True,
) -> dict[str, Any]:
    """Batch-review multiple records."""
    updated: list[int] = []
    missing: list[int] = []
    for rid in record_ids:
        existing = get_record(int(rid))
        if not existing:
            missing.append(int(rid))
            continue
        next_risk = risk_level if risk_level is not None else str(existing.get("risk_level") or "低")
        if keep_risk and risk_level is None:
            next_risk = str(existing.get("risk_level") or "低")
        base_note = str(existing.get("review_note") or "")
        if note is None:
            next_note = base_note
        elif append_note and base_note and note and note not in base_note:
            next_note = f"{base_note}\n{note}".strip()
        else:
            next_note = note if note is not None else base_note
        result = update_review(int(rid), status, next_risk, next_note)
        if result:
            updated.append(int(rid))
        else:
            missing.append(int(rid))
    return {"updated": updated, "missing": missing, "updated_count": len(updated)}


def replace_detection_result(
    record_id: int,
    *,
    risk_level: str,
    risk_reason: str,
    review_status: str,
    confidence: float,
    detection_count: int,
    quality: dict[str, Any],
    detections: list[dict[str, Any]],
    workflow: list[dict[str, Any]],
    metrics: dict[str, Any],
    annotated_path: str | None = None,
    keep_review_note: bool = True,
) -> dict[str, Any] | None:
    """Overwrite detection fields after re-analysis (same original image)."""
    with connect() as conn:
        row = conn.execute("SELECT review_note FROM records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return None
        review_note = row["review_note"] if keep_review_note else ""
        if annotated_path:
            conn.execute(
                """
                UPDATE records SET
                    annotated_path = ?,
                    risk_level = ?, risk_reason = ?, review_status = ?, review_note = ?,
                    confidence = ?, detection_count = ?,
                    quality_json = ?, detections_json = ?, workflow_json = ?, metrics_json = ?
                WHERE id = ?
                """,
                (
                    annotated_path,
                    risk_level,
                    risk_reason,
                    review_status,
                    review_note,
                    confidence,
                    detection_count,
                    json.dumps(quality, ensure_ascii=False),
                    json.dumps(detections, ensure_ascii=False),
                    json.dumps(workflow, ensure_ascii=False),
                    json.dumps(metrics, ensure_ascii=False),
                    record_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE records SET
                    risk_level = ?, risk_reason = ?, review_status = ?, review_note = ?,
                    confidence = ?, detection_count = ?,
                    quality_json = ?, detections_json = ?, workflow_json = ?, metrics_json = ?
                WHERE id = ?
                """,
                (
                    risk_level,
                    risk_reason,
                    review_status,
                    review_note,
                    confidence,
                    detection_count,
                    json.dumps(quality, ensure_ascii=False),
                    json.dumps(detections, ensure_ascii=False),
                    json.dumps(workflow, ensure_ascii=False),
                    json.dumps(metrics, ensure_ascii=False),
                    record_id,
                ),
            )
    return get_record(record_id)


def delete_record(record_id: int) -> bool:
    """Delete DB row and best-effort remove image files."""
    with connect() as conn:
        row = conn.execute(
            "SELECT original_path, annotated_path FROM records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))

    for key in ("original_path", "annotated_path"):
        path = Path(row[key])
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return True


def delete_records(record_ids: list[int]) -> dict[str, Any]:
    deleted: list[int] = []
    missing: list[int] = []
    for rid in record_ids:
        if delete_record(int(rid)):
            deleted.append(int(rid))
        else:
            missing.append(int(rid))
    return {"deleted": deleted, "missing": missing, "deleted_count": len(deleted)}


def orphan_files() -> dict[str, Any]:
    """Find upload/output files not referenced by any record."""
    with connect() as conn:
        rows = conn.execute("SELECT original_path, annotated_path FROM records").fetchall()
    referenced: set[str] = set()
    for row in rows:
        referenced.add(Path(row["original_path"]).name)
        referenced.add(Path(row["annotated_path"]).name)

    orphan_uploads: list[str] = []
    orphan_outputs: list[str] = []
    if UPLOAD_DIR.exists():
        for path in UPLOAD_DIR.iterdir():
            if path.is_file() and path.name not in referenced:
                orphan_uploads.append(path.name)
    if OUTPUT_DIR.exists():
        for path in OUTPUT_DIR.iterdir():
            if path.is_file() and path.name not in referenced:
                orphan_outputs.append(path.name)
    return {
        "orphan_uploads": sorted(orphan_uploads),
        "orphan_outputs": sorted(orphan_outputs),
        "orphan_count": len(orphan_uploads) + len(orphan_outputs),
    }


def cleanup_orphans(delete: bool = False) -> dict[str, Any]:
    info = orphan_files()
    removed: list[str] = []
    if delete:
        for name in info["orphan_uploads"]:
            path = UPLOAD_DIR / name
            try:
                path.unlink(missing_ok=True)
                removed.append(str(path))
            except OSError:
                pass
        for name in info["orphan_outputs"]:
            path = OUTPUT_DIR / name
            try:
                path.unlink(missing_ok=True)
                removed.append(str(path))
            except OSError:
                pass
    return {**info, "removed": removed, "removed_count": len(removed)}


def stats_summary() -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM records").fetchone()["c"]
        pending = conn.execute(
            "SELECT COUNT(*) AS c FROM records WHERE review_status = ?",
            ("待复核",),
        ).fetchone()["c"]
        auto_pass = conn.execute(
            "SELECT COUNT(*) AS c FROM records WHERE review_status = ?",
            ("自动通过",),
        ).fetchone()["c"]
        reviewed = conn.execute(
            "SELECT COUNT(*) AS c FROM records WHERE review_status = ?",
            ("已复核",),
        ).fetchone()["c"]
        avg_row = conn.execute("SELECT AVG(confidence) AS a FROM records").fetchone()
        avg_conf = float(avg_row["a"] or 0.0)
        by_risk = {"低": 0, "中": 0, "高": 0}
        for row in conn.execute(
            "SELECT risk_level, COUNT(*) AS c FROM records GROUP BY risk_level"
        ).fetchall():
            level = row["risk_level"]
            if level in by_risk:
                by_risk[level] = int(row["c"])
        total_detections = conn.execute(
            "SELECT COALESCE(SUM(detection_count), 0) AS s FROM records"
        ).fetchone()["s"]

        by_kind = {"crack": 0, "spalling": 0, "stain": 0}
        for row in conn.execute("SELECT metrics_json FROM records").fetchall():
            counts = _metrics_kind_counts(row["metrics_json"])
            by_kind["crack"] += counts["crack_count"]
            by_kind["spalling"] += counts["spalling_count"]
            by_kind["stain"] += counts["stain_count"]

        # recent timeline by day (last 14 buckets of created_at date prefix)
        timeline: list[dict[str, Any]] = []
        day_rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS c
            FROM records
            GROUP BY substr(created_at, 1, 10)
            ORDER BY day DESC
            LIMIT 14
            """
        ).fetchall()
        for row in reversed(list(day_rows)):
            timeline.append({"day": row["day"] or "", "count": int(row["c"])})

        by_review = {
            "待复核": int(pending),
            "自动通过": int(auto_pass),
            "已复核": int(reviewed),
        }

        conf_buckets = {"0-0.5": 0, "0.5-0.7": 0, "0.7-0.85": 0, "0.85-1.0": 0}
        for row in conn.execute("SELECT confidence FROM records").fetchall():
            c = float(row["confidence"] or 0)
            if c < 0.5:
                conf_buckets["0-0.5"] += 1
            elif c < 0.7:
                conf_buckets["0.5-0.7"] += 1
            elif c < 0.85:
                conf_buckets["0.7-0.85"] += 1
            else:
                conf_buckets["0.85-1.0"] += 1

    return {
        "total": int(total),
        "pending_review": int(pending),
        "auto_pass": int(auto_pass),
        "reviewed": int(reviewed),
        "high_risk": int(by_risk["高"]),
        "medium_risk": int(by_risk["中"]),
        "low_risk": int(by_risk["低"]),
        "avg_confidence": round(avg_conf, 4),
        "total_detections": int(total_detections),
        "by_risk": by_risk,
        "by_kind": by_kind,
        "by_review": by_review,
        "timeline": timeline,
        "confidence_buckets": conf_buckets,
    }


def storage_health() -> dict[str, Any]:
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0
    upload_count = len(list(UPLOAD_DIR.glob("*"))) if UPLOAD_DIR.exists() else 0
    output_count = len(list(OUTPUT_DIR.glob("*"))) if OUTPUT_DIR.exists() else 0
    orphans = orphan_files()
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM records").fetchone()["c"]
    return {
        "db_path": str(DB_PATH),
        "db_exists": db_exists,
        "db_size_bytes": db_size,
        "record_count": int(total),
        "upload_dir": str(UPLOAD_DIR),
        "output_dir": str(OUTPUT_DIR),
        "upload_file_count": upload_count,
        "output_file_count": output_count,
        "orphan_count": orphans["orphan_count"],
    }
