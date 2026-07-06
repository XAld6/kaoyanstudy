"""ORM 对象到字典的序列化转换。"""
from __future__ import annotations

import json

from app.database import InspectionRecord, InspectionTask, RepairOrder, to_web_path
from models.risk import RISK_LABELS


def record_to_dict(record: InspectionRecord) -> dict:
    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "image_path": to_web_path(record.image_path),
        "result_path": to_web_path(record.result_path),
        "detections": json.loads(record.detections_json),
        "risk_level": record.risk_level,
        "risk_label": RISK_LABELS.get(record.risk_level, record.risk_level),
        "engine": record.engine,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def task_to_dict(task: InspectionTask) -> dict:
    return {
        "id": task.id,
        "task_name": task.task_name,
        "building_name": task.building_name,
        "area": task.area,
        "inspector": task.inspector,
        "status": task.status,
        "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def work_order_to_dict(order: RepairOrder) -> dict:
    return {
        "id": order.id,
        "record_id": order.record_id,
        "title": order.title,
        "defect_type": order.defect_type,
        "risk_level": order.risk_level,
        "risk_label": RISK_LABELS.get(order.risk_level, order.risk_level),
        "status": order.status,
        "handler": order.handler,
        "deadline": order.deadline,
        "before_image_path": to_web_path(order.before_image_path),
        "after_image_path": to_web_path(order.after_image_path) if order.after_image_path else "",
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
