from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.reporting import build_pdf
from app.schemas import DetectionRecord, RecordSummary, ReviewRequest
from app.storage import OUTPUT_DIR, UPLOAD_DIR, get_record, init_db, insert_record, list_records, update_review
from app.workflow import run_damage_workflow

app = FastAPI(title="智爪识损 OpenClaw Damage System", version="1.0.0")
MAX_UPLOAD_BYTES = 8 * 1024 * 1024

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


def _save_upload(file: UploadFile, destination: Path) -> None:
    written = 0
    oversized = False

    with destination.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            if written + len(chunk) > MAX_UPLOAD_BYTES:
                oversized = True
                break
            out.write(chunk)
            written += len(chunk)

    if oversized:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="上传图片不能超过 8MB，请压缩后再试。")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "openclaw-damage-system"}


@app.post("/api/detect", response_model=DetectionRecord)
async def detect(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件。")

    suffix = Path(file.filename or "image.png").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
        suffix = ".png"

    token = uuid.uuid4().hex
    stored_name = f"{token}{suffix}"
    original_path = UPLOAD_DIR / stored_name
    annotated_path = OUTPUT_DIR / f"{token}_annotated.png"

    try:
        _save_upload(file, original_path)
        workflow_result = run_damage_workflow(original_path, annotated_path)
    except ValueError as exc:
        original_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        original_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        original_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"检测流程执行失败：{exc}") from exc
    finally:
        await file.close()

    payload = {
        "filename": file.filename or stored_name,
        "stored_filename": stored_name,
        "original_path": str(original_path),
        "annotated_path": str(annotated_path),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "risk_level": workflow_result["risk_level"],
        "risk_reason": workflow_result["risk_reason"],
        "review_status": workflow_result["review_status"],
        "review_note": "",
        "confidence": workflow_result["confidence"],
        "detection_count": workflow_result["metrics"]["detection_count"],
        "quality": workflow_result["quality"],
        "detections": workflow_result["detections"],
        "workflow": workflow_result["workflow"],
        "metrics": workflow_result["metrics"],
    }
    record_id = insert_record(payload)
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=500, detail="检测记录保存失败。")
    return record


@app.get("/api/records", response_model=list[RecordSummary])
def records() -> list[dict]:
    return list_records()


@app.get("/api/records/{record_id}", response_model=DetectionRecord)
def record_detail(record_id: int) -> dict:
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return record


@app.post("/api/records/{record_id}/review", response_model=DetectionRecord)
def review(record_id: int, payload: ReviewRequest) -> dict:
    record = update_review(record_id, payload.status, payload.risk_level, payload.review_note)
    if not record:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return record


@app.get("/api/records/{record_id}/report")
def report(record_id: int) -> Response:
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return Response(
        build_pdf(record),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="damage-report-{record_id}.pdf"'},
    )
