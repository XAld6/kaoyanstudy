"""Detector backend selection via environment variables.

OPENCLAW_DETECTOR:
  - opencv (default): rule-based OpenCV screening
  - yolo: Ultralytics YOLO weights if available; otherwise falls back to opencv

OPENCLAW_YOLO_WEIGHTS:
  path to .pt / .onnx weights (optional until a trained model is ready)

OPENCLAW_YOLO_CONF:
  confidence threshold (default 0.25)
"""

from __future__ import annotations

import os
from pathlib import Path

APP_VERSION = "2.0.0"
SERVICE_NAME = "openclaw-damage-system"

DETECTOR_OPENCV = "opencv"
DETECTOR_YOLO = "yolo"
SUPPORTED_DETECTORS = {DETECTOR_OPENCV, DETECTOR_YOLO}


def configured_detector() -> str:
    raw = os.getenv("OPENCLAW_DETECTOR", DETECTOR_OPENCV).strip().lower()
    if raw not in SUPPORTED_DETECTORS:
        return DETECTOR_OPENCV
    return raw


def yolo_weights_path() -> Path | None:
    raw = os.getenv("OPENCLAW_YOLO_WEIGHTS", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.exists() else path  # may not exist yet; caller checks


def yolo_conf_threshold() -> float:
    raw = os.getenv("OPENCLAW_YOLO_CONF", "0.25").strip()
    try:
        value = float(raw)
    except ValueError:
        return 0.25
    return min(0.95, max(0.05, value))


def ultralytics_available() -> bool:
    try:
        import ultralytics  # noqa: F401

        return True
    except Exception:
        return False


def yolo_ready() -> bool:
    weights = yolo_weights_path()
    return ultralytics_available() and weights is not None and weights.exists()


def detector_status() -> dict:
    """Runtime status for health checks and UI."""
    requested = configured_detector()
    weights = yolo_weights_path()
    yolo_ok = yolo_ready()

    if requested == DETECTOR_YOLO and yolo_ok:
        active = DETECTOR_YOLO
        label = "YOLO 深度模型"
        note = f"权重: {weights}"
    elif requested == DETECTOR_YOLO and not yolo_ok:
        active = DETECTOR_OPENCV
        label = "OpenCV 规则初筛（YOLO 未就绪，已回退）"
        missing = []
        if not ultralytics_available():
            missing.append("未安装 ultralytics")
        if weights is None or not weights.exists():
            missing.append("未配置有效 OPENCLAW_YOLO_WEIGHTS")
        note = "；".join(missing) if missing else "YOLO 不可用"
    else:
        active = DETECTOR_OPENCV
        label = "OpenCV 规则初筛"
        note = "默认本地演示后端，可切换 OPENCLAW_DETECTOR=yolo"

    return {
        "requested": requested,
        "active": active,
        "label": label,
        "note": note,
        "yolo_available": ultralytics_available(),
        "yolo_ready": yolo_ok,
        "yolo_weights": str(weights) if weights else "",
        "version": APP_VERSION,
    }
