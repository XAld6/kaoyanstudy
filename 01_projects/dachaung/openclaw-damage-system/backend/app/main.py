from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.backend_config import APP_VERSION, SERVICE_NAME, detector_status
from app.compare import compare_records
from app.exporting import records_to_csv, records_to_pdf_zip
from app.reporting import build_pdf
from app.runtime_settings import get_settings, reset_settings, settings_schema, update_settings
from app.schemas import DetectionRecord, RecordSummary, ReviewRequest
from app.storage import (
    OUTPUT_DIR,
    UPLOAD_DIR,
    batch_update_review,
    cleanup_orphans,
    delete_record,
    delete_records,
    get_record,
    init_db,
    insert_record,
    list_records,
    list_records_page,
    neighbor_ids,
    replace_detection_result,
    stats_summary,
    storage_health,
    update_review,
)
from app.workflow import run_damage_workflow

app = FastAPI(title="智爪识损 OpenClaw Damage System", version=APP_VERSION)
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_BATCH_FILES = 12
MAX_BATCH_REDETECT = 20
ALLOWED_IMAGE_SUFFIX = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    response.headers["X-App-Version"] = APP_VERSION
    return response


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


def _validate_image_upload(file: UploadFile) -> str:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件。")
    suffix = Path(file.filename or "image.png").suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIX:
        suffix = ".png"
    return suffix


def _run_detect_to_record(file: UploadFile) -> dict:
    suffix = _validate_image_upload(file)
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


def _resolve_original_path(existing: dict) -> Path:
    original_path = Path(existing.get("original_path") or "")
    if original_path.exists():
        return original_path
    url = str(existing.get("original_url") or "")
    name = Path(url).name
    candidate = UPLOAD_DIR / name
    if candidate.exists():
        return candidate
    raise HTTPException(status_code=400, detail="原图文件已丢失，无法重新检测。")


def _redetect_one(record_id: int) -> dict:
    existing = get_record(record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="未找到检测记录。")

    original_path = _resolve_original_path(existing)
    token = uuid.uuid4().hex
    annotated_path = OUTPUT_DIR / f"{token}_annotated.png"
    try:
        workflow_result = run_damage_workflow(original_path, annotated_path)
    except ValueError as exc:
        annotated_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        annotated_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"重新检测失败：{exc}") from exc

    old_ann = Path(str(existing.get("annotated_path") or ""))
    if old_ann.exists() and old_ann.resolve() != annotated_path.resolve():
        try:
            old_ann.unlink(missing_ok=True)
        except OSError:
            pass

    updated = replace_detection_result(
        record_id,
        risk_level=workflow_result["risk_level"],
        risk_reason=workflow_result["risk_reason"],
        review_status=workflow_result["review_status"],
        confidence=workflow_result["confidence"],
        detection_count=workflow_result["metrics"]["detection_count"],
        quality=workflow_result["quality"],
        detections=workflow_result["detections"],
        workflow=workflow_result["workflow"],
        metrics=workflow_result["metrics"],
        annotated_path=str(annotated_path),
        keep_review_note=True,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="重新检测结果保存失败。")
    return updated


@app.get("/api/health")
def health() -> dict:
    status = detector_status()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "detector": status,
        "storage": storage_health(),
        "settings_loaded": True,
    }


class SettingsUpdateRequest(BaseModel):
    sensitivity: float | None = None
    min_confidence: float | None = None
    max_detections: int | None = None
    crack_min_length: float | None = None
    spalling_min_area_ratio: float | None = None
    stain_min_area_ratio: float | None = None
    risk_high_area: float | None = None
    risk_medium_area: float | None = None
    risk_high_count: int | None = None
    risk_medium_count: int | None = None


class CompareRequest(BaseModel):
    left_id: int = Field(..., ge=1)
    right_id: int = Field(..., ge=1)


class IdsRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=200)


class BatchReviewRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=200)
    status: str = Field(default="已复核", min_length=1, max_length=40)
    risk_level: str | None = Field(default=None, pattern="^(低|中|高)$")
    review_note: str = Field(default="批量复核通过", max_length=800)
    keep_risk: bool = True


class CleanupRequest(BaseModel):
    delete: bool = False


@app.get("/api/system")
def system_info() -> dict:
    status = detector_status()
    return {
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "capabilities": {
            "multi_type_detection": True,
            "damage_kinds": ["crack", "spalling", "stain"],
            "agent_workflow": True,
            "pdf_report": True,
            "manual_review": True,
            "history_sqlite": True,
            "pluggable_detector": True,
            "batch_detect": True,
            "record_filter": True,
            "record_delete": True,
            "batch_delete": True,
            "batch_review": True,
            "batch_redetect": True,
            "redetect": True,
            "stats": True,
            "stats_timeline": True,
            "export_csv": True,
            "export_pdf_zip": True,
            "record_compare": True,
            "runtime_settings": True,
            "settings_persist": True,
            "pagination": True,
            "sorting": True,
            "orphan_cleanup": True,
            "neighbors": True,
        },
        "detector": status,
        "limits": {
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
            "max_batch_files": MAX_BATCH_FILES,
            "max_batch_redetect": MAX_BATCH_REDETECT,
        },
        "settings": get_settings(),
        "storage": storage_health(),
    }


@app.get("/api/stats")
def stats() -> dict:
    return stats_summary()


@app.post("/api/detect", response_model=DetectionRecord)
async def detect(file: UploadFile = File(...)) -> dict:
    try:
        return _run_detect_to_record(file)
    finally:
        await file.close()


@app.post("/api/detect/batch")
async def detect_batch(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片。")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"单次批量最多 {MAX_BATCH_FILES} 张图片，请分批上传。",
        )

    records: list[dict] = []
    errors: list[dict] = []
    try:
        for file in files:
            try:
                records.append(_run_detect_to_record(file))
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                errors.append({"filename": file.filename or "unknown", "error": detail})
            except Exception as exc:  # pragma: no cover - defensive
                errors.append({"filename": file.filename or "unknown", "error": str(exc)})
    finally:
        for file in files:
            await file.close()

    return {
        "ok_count": len(records),
        "error_count": len(errors),
        "records": records,
        "errors": errors,
    }


@app.get("/api/records", response_model=list[RecordSummary])
def records(
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int | None = Query(default=None, ge=0, le=10000),
    sort: str | None = Query(default=None, max_length=40),
    order: str | None = Query(default=None, pattern="^(asc|desc|ASC|DESC)$"),
) -> list[dict]:
    return list_records(
        risk_level=risk_level,
        review_status=review_status,
        q=q,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@app.get("/api/records/page")
def records_page(
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1, le=10000),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str | None = Query(default=None, max_length=40),
    order: str | None = Query(default=None, pattern="^(asc|desc|ASC|DESC)$"),
) -> dict:
    return list_records_page(
        risk_level=risk_level,
        review_status=review_status,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@app.get("/api/records/{record_id}", response_model=DetectionRecord)
def record_detail(record_id: int) -> dict:
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return record


@app.get("/api/records/{record_id}/neighbors")
def record_neighbors(
    record_id: int,
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
) -> dict:
    if not get_record(record_id):
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return {"id": record_id, **neighbor_ids(record_id, risk_level, review_status, q)}


@app.post("/api/records/{record_id}/review", response_model=DetectionRecord)
def review(record_id: int, payload: ReviewRequest) -> dict:
    record = update_review(record_id, payload.status, payload.risk_level, payload.review_note)
    if not record:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return record


@app.delete("/api/records/{record_id}")
def remove_record(record_id: int) -> dict:
    ok = delete_record(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未找到检测记录。")
    return {"ok": True, "id": record_id}


@app.post("/api/records/batch-delete")
def batch_delete(payload: IdsRequest) -> dict:
    unique_ids = list(dict.fromkeys(int(i) for i in payload.ids if int(i) > 0))
    if not unique_ids:
        raise HTTPException(status_code=400, detail="请提供有效的记录 ID。")
    result = delete_records(unique_ids)
    return {"ok": True, **result}


@app.post("/api/records/batch-review")
def batch_review(payload: BatchReviewRequest) -> dict:
    unique_ids = list(dict.fromkeys(int(i) for i in payload.ids if int(i) > 0))
    if not unique_ids:
        raise HTTPException(status_code=400, detail="请提供有效的记录 ID。")
    result = batch_update_review(
        unique_ids,
        status=payload.status,
        risk_level=payload.risk_level,
        note=payload.review_note,
        keep_risk=payload.keep_risk,
        append_note=True,
    )
    return {"ok": True, **result}


@app.post("/api/records/{record_id}/redetect", response_model=DetectionRecord)
def redetect(record_id: int) -> dict:
    """Re-run detection on the stored original image with current runtime settings."""
    return _redetect_one(record_id)


@app.post("/api/records/batch-redetect")
def batch_redetect(payload: IdsRequest) -> dict:
    unique_ids = list(dict.fromkeys(int(i) for i in payload.ids if int(i) > 0))
    if not unique_ids:
        raise HTTPException(status_code=400, detail="请提供有效的记录 ID。")
    if len(unique_ids) > MAX_BATCH_REDETECT:
        raise HTTPException(
            status_code=400,
            detail=f"单次批量重检最多 {MAX_BATCH_REDETECT} 条，请分批处理。",
        )
    records: list[dict] = []
    errors: list[dict] = []
    for rid in unique_ids:
        try:
            records.append(_redetect_one(rid))
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            errors.append({"id": rid, "error": detail})
        except Exception as exc:  # pragma: no cover
            errors.append({"id": rid, "error": str(exc)})
    return {
        "ok_count": len(records),
        "error_count": len(errors),
        "records": records,
        "errors": errors,
    }


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


def _parse_ids_param(ids: str | None) -> list[int] | None:
    if not ids or not ids.strip():
        return None
    parsed: list[int] = []
    for part in ids.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            continue
        if value > 0:
            parsed.append(value)
    return parsed or None


def _filtered_records(
    risk_level: str | None,
    review_status: str | None,
    q: str | None,
    limit: int | None,
    ids: list[int] | None = None,
) -> list[dict]:
    records = list_records(
        risk_level=risk_level,
        review_status=review_status,
        q=q,
        limit=limit,
        ids=ids,
    )
    detailed: list[dict] = []
    for item in records:
        full = get_record(int(item["id"]))
        if full:
            detailed.append(full)
    return detailed


@app.get("/api/export/csv")
def export_csv(
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
    limit: int | None = Query(default=None, ge=1, le=500),
    ids: str | None = Query(default=None, max_length=2000, description="comma-separated record ids"),
) -> Response:
    records = _filtered_records(risk_level, review_status, q, limit, _parse_ids_param(ids))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(
        records_to_csv(records),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="damage-export-{stamp}.csv"'},
    )


@app.get("/api/export/pdf-zip")
def export_pdf_zip(
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
    limit: int | None = Query(default=None, ge=1, le=100),
    ids: str | None = Query(default=None, max_length=2000, description="comma-separated record ids"),
) -> Response:
    records = _filtered_records(risk_level, review_status, q, limit, _parse_ids_param(ids))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(
        records_to_pdf_zip(records),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="damage-reports-{stamp}.zip"'},
    )


@app.get("/api/export/json")
def export_json(
    risk_level: str | None = Query(default=None, pattern="^(低|中|高)$"),
    review_status: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=120),
    limit: int | None = Query(default=None, ge=1, le=500),
    ids: str | None = Query(default=None, max_length=2000),
) -> JSONResponse:
    records = _filtered_records(risk_level, review_status, q, limit, _parse_ids_param(ids))
    # strip internal paths for safer export
    public = []
    for item in records:
        public.append(
            {
                k: v
                for k, v in item.items()
                if k not in {"original_path", "annotated_path", "stored_filename"}
            }
        )
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return JSONResponse(
        content={"exported_at": stamp, "count": len(public), "records": public},
        headers={"Content-Disposition": f'attachment; filename="damage-export-{stamp}.json"'},
    )


@app.get("/api/compare")
def compare_get(
    left_id: int = Query(..., ge=1),
    right_id: int = Query(..., ge=1),
) -> dict:
    left = get_record(left_id)
    right = get_record(right_id)
    if not left or not right:
        missing = []
        if not left:
            missing.append(f"left_id={left_id}")
        if not right:
            missing.append(f"right_id={right_id}")
        raise HTTPException(status_code=404, detail=f"未找到对比记录：{', '.join(missing)}")
    return compare_records(left, right)


@app.post("/api/compare")
def compare_post(payload: CompareRequest) -> dict:
    left = get_record(payload.left_id)
    right = get_record(payload.right_id)
    if not left or not right:
        missing = []
        if not left:
            missing.append(f"left_id={payload.left_id}")
        if not right:
            missing.append(f"right_id={payload.right_id}")
        raise HTTPException(status_code=404, detail=f"未找到对比记录：{', '.join(missing)}")
    return compare_records(left, right)


@app.get("/api/settings")
def settings_get() -> dict:
    return {
        "settings": get_settings(),
        "schema": settings_schema(),
        "defaults": True,
    }


@app.put("/api/settings")
def settings_put(payload: SettingsUpdateRequest) -> dict:
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="请至少提供一个可调参数。")
    updated = update_settings(data)
    return {"settings": updated, "schema": settings_schema()}


@app.post("/api/settings/reset")
def settings_reset() -> dict:
    return {"settings": reset_settings(), "schema": settings_schema()}


@app.get("/api/maintenance/orphans")
def maintenance_orphans() -> dict:
    return cleanup_orphans(delete=False)


@app.post("/api/maintenance/orphans")
def maintenance_cleanup(payload: CleanupRequest) -> dict:
    return cleanup_orphans(delete=payload.delete)
