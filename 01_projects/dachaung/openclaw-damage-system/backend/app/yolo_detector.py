"""Optional YOLO backend (Ultralytics). Falls back is handled by detector.analyze_image."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.backend_config import yolo_conf_threshold, yolo_weights_path
from app.detector import (
    DRAW_COLORS,
    LABELS,
    MAX_DETECTIONS,
    _public_detection,
    _quality,
    _suppress_overlaps,
)

# Accept common class name variants from custom-trained weights
CLASS_ALIASES = {
    "crack": "crack",
    "cracks": "crack",
    "裂缝": "crack",
    "spalling": "spalling",
    "spall": "spalling",
    "剥落": "spalling",
    "stain": "stain",
    "seepage": "stain",
    "wet": "stain",
    "discoloration": "stain",
    "渗水": "stain",
    "色差": "stain",
}


_model = None
_model_path: str | None = None


def _load_model():
    global _model, _model_path
    weights = yolo_weights_path()
    if weights is None or not weights.exists():
        raise FileNotFoundError("YOLO 权重文件不存在，请设置 OPENCLAW_YOLO_WEIGHTS")
    key = str(weights.resolve())
    if _model is not None and _model_path == key:
        return _model
    from ultralytics import YOLO

    _model = YOLO(key)
    _model_path = key
    return _model


def _map_kind(name: str, class_id: int) -> str | None:
    key = str(name or "").strip().lower()
    if key in CLASS_ALIASES:
        return CLASS_ALIASES[key]
    # fallback: map first three class ids if names unknown
    if class_id == 0:
        return "crack"
    if class_id == 1:
        return "spalling"
    if class_id == 2:
        return "stain"
    return None


def analyze_image_yolo(image_path: Path, annotated_path: Path) -> dict:
    image = cv2.imdecode(np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法读取图片，请上传有效的巡检图片。")

    h, w = image.shape[:2]
    if h < 40 or w < 40:
        raise ValueError("图片尺寸过小，无法进行有效识别。")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    quality = _quality(gray)
    image_area = float(w * h)

    model = _load_model()
    conf = yolo_conf_threshold()
    results = model.predict(source=str(image_path), conf=conf, verbose=False)

    raw: list[dict] = []
    if results:
        result = results[0]
        names = getattr(result, "names", None) or getattr(model, "names", {}) or {}
        boxes = getattr(result, "boxes", None)
        if boxes is not None:
            for box in boxes:
                cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                score = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
                xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy, "tolist") else list(box.xyxy[0])
                x1, y1, x2, y2 = [int(v) for v in xyxy]
                bw = max(1, x2 - x1)
                bh = max(1, y2 - y1)
                name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(cls_id)
                kind = _map_kind(str(name), cls_id)
                if kind is None:
                    continue
                box_area = float(bw * bh)
                raw.append(
                    {
                        "kind": kind,
                        "label": LABELS[kind],
                        "bbox": [x1, y1, bw, bh],
                        "confidence": round(min(0.99, max(0.05, score)), 3),
                        "area_ratio": round(box_area / image_area, 5),
                        "length_estimate": round(float(max(bw, bh)), 2),
                    }
                )

    detections = _suppress_overlaps(raw, iou_thresh=0.45)
    detections = sorted(detections, key=lambda item: item["confidence"], reverse=True)[:MAX_DETECTIONS]

    annotated = image.copy()
    for item in detections:
        x, y, bw, bh = item["bbox"]
        color = DRAW_COLORS.get(item["kind"], (0, 0, 255))
        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), color, 2, lineType=cv2.LINE_AA)
        tag = f"{item['label']} {item['confidence']:.2f}"
        cv2.putText(
            annotated,
            tag,
            (x, max(18, y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            lineType=cv2.LINE_AA,
        )

    if not detections:
        cv2.putText(
            annotated,
            "No YOLO damage candidate",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.78,
            (70, 120, 70),
            2,
            lineType=cv2.LINE_AA,
        )

    legend_y = h - 16
    for idx, (kind, label) in enumerate((("crack", "裂缝"), ("spalling", "剥落"), ("stain", "渗水/色差"))):
        lx = 16 + idx * 120
        cv2.rectangle(annotated, (lx, legend_y - 12), (lx + 14, legend_y + 2), DRAW_COLORS[kind], -1)
        cv2.putText(
            annotated,
            label,
            (lx + 20, legend_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            DRAW_COLORS[kind],
            1,
            lineType=cv2.LINE_AA,
        )

    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".png", annotated)
    if not ok:
        raise ValueError("标注图生成失败。")
    encoded.tofile(str(annotated_path))

    public = [_public_detection(d) for d in detections]
    avg_conf = round(float(np.mean([d["confidence"] for d in public])) if public else 0.0, 3)
    total_area_ratio = round(float(sum(d["area_ratio"] for d in public)), 5)
    metrics = {
        "detection_count": len(public),
        "avg_confidence": avg_conf,
        "total_area_ratio": total_area_ratio,
        "crack_count": sum(1 for d in public if d["kind"] == "crack"),
        "spalling_count": sum(1 for d in public if d["kind"] == "spalling"),
        "stain_count": sum(1 for d in public if d["kind"] == "stain"),
    }
    quality = {
        **quality,
        "detector": "yolo",
        "detector_label": "YOLO 深度模型",
    }
    return {"quality": quality, "detections": public, "metrics": metrics}
