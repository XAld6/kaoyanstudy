"""业务逻辑：图片处理、检测、记录管理。"""
from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.database import (
    InspectionRecord,
    InspectionTask,
    RepairOrder,
    get_session,
    to_web_path,
)
from app.serializers import record_to_dict, task_to_dict, work_order_to_dict
from models.detector import WallDefectDetector
from models.risk import RISK_LABELS
from utils.config import load_settings, project_path
from utils.image import is_allowed_image, verify_image

settings = load_settings()


async def process_upload(file: UploadFile, detector: WallDefectDetector) -> dict:
    if not file.filename or not is_allowed_image(file.filename):
        raise HTTPException(status_code=400, detail="请上传 jpg、png、bmp 或 webp 图片。")

    upload_dir = project_path(settings["paths"]["uploads_dir"])
    suffix = Path(file.filename).suffix.lower()
    image_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    with image_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    return _process_saved_image(file.filename, image_path, detector)


async def process_uploads(files: list[UploadFile], detector: WallDefectDetector) -> list[dict]:
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片。")
    return [await process_upload(file, detector) for file in files]


def process_sample(sample: str, detector: WallDefectDetector) -> dict:
    sample_path = project_path(settings["paths"]["samples_dir"]) / Path(sample).name
    if not sample_path.exists() or not sample_path.is_file() or not is_allowed_image(sample_path.name):
        raise HTTPException(status_code=404, detail="样例图片不存在。")
    copied_path = project_path(settings["paths"]["uploads_dir"]) / f"{uuid.uuid4().hex}{sample_path.suffix.lower()}"
    shutil.copyfile(sample_path, copied_path)
    return _process_saved_image(sample_path.name, copied_path, detector)


def _process_saved_image(original_filename: str, image_path: Path, detector: WallDefectDetector) -> dict:
    result_path = project_path(settings["paths"]["results_dir"]) / f"{image_path.stem}_result.jpg"
    try:
        verify_image(image_path)
    except Exception as exc:
        image_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="文件不是有效图片。") from exc

    result = detector.predict(image_path, result_path)
    return _save_record(original_filename, image_path, result.result_image_path, result)


def _save_record(original_filename: str, image_path: Path, result_path: Path, result) -> dict:
    with get_session() as session:
        record = InspectionRecord(
            original_filename=original_filename,
            image_path=str(image_path),
            result_path=str(result_path),
            detections_json=json.dumps(result.detections, ensure_ascii=False),
            risk_level=result.overall_risk,
            engine=result.engine,
        )
        session.add(record)
        session.flush()
        record_dict = record_to_dict(record)
        if record.risk_level in {"high", "urgent"}:
            _create_repair_order(session, record, result.detections)
        return record_dict


def _create_repair_order(session, record: InspectionRecord, detections: list[dict]) -> None:
    existing = session.query(RepairOrder).filter(RepairOrder.record_id == record.id).first()
    if existing is not None:
        return
    primary = max(detections, key=lambda item: item.get("area_ratio", 0), default={})
    defect_type = primary.get("type", "unknown")
    defect_label = primary.get("label", defect_type)
    session.add(
        RepairOrder(
            record_id=record.id,
            title=f"{RISK_LABELS.get(record.risk_level, record.risk_level)}外墙隐患维修：{defect_label}",
            defect_type=defect_type,
            risk_level=record.risk_level,
            status="pending",
            handler="维修班组",
            deadline="24小时内处理" if record.risk_level == "urgent" else "48小时内处理",
            before_image_path=record.result_path,
        )
    )


def update_work_order_status(order_id: int, status: str) -> None:
    allowed_statuses = {"pending", "processing", "completed"}
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="工单状态不合法。")
    with get_session() as session:
        order = session.query(RepairOrder).filter(RepairOrder.id == order_id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="工单不存在。")
        order.status = status
        order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)


def latest_records(limit: int) -> list[dict]:
    with get_session() as session:
        records = (
            session.query(InspectionRecord)
            .order_by(InspectionRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [record_to_dict(record) for record in records]


def risk_stats() -> dict[str, int]:
    stats = {key: 0 for key in RISK_LABELS}
    with get_session() as session:
        records = session.query(InspectionRecord).all()
        for record in records:
            stats[record.risk_level] = stats.get(record.risk_level, 0) + 1
    return stats


def sample_images() -> list[dict]:
    samples = []
    for path in sorted(project_path(settings["paths"]["samples_dir"]).glob("*")):
        if is_allowed_image(path.name):
            samples.append({"filename": path.name, "path": to_web_path(path)})
    return samples


def latest_tasks() -> list[dict]:
    with get_session() as session:
        tasks = (
            session.query(InspectionTask)
            .order_by(InspectionTask.created_at.desc())
            .limit(100)
            .all()
        )
        return [task_to_dict(task) for task in tasks]


def latest_work_orders() -> list[dict]:
    with get_session() as session:
        orders = (
            session.query(RepairOrder)
            .order_by(RepairOrder.created_at.desc())
            .limit(100)
            .all()
        )
        return [work_order_to_dict(order) for order in orders]
