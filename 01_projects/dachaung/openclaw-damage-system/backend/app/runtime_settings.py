"""Runtime detection parameters with optional JSON persistence."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from threading import Lock

DEFAULT_SETTINGS: dict = {
    "sensitivity": 0.55,  # 0.2–0.9: higher = more candidates
    "min_confidence": 0.50,  # drop candidates below this
    "max_detections": 16,
    "crack_min_length": 38.0,
    "spalling_min_area_ratio": 0.005,
    "stain_min_area_ratio": 0.006,
    "risk_high_area": 0.055,
    "risk_medium_area": 0.012,
    "risk_high_count": 8,
    "risk_medium_count": 1,
}

_lock = Lock()
_settings: dict = deepcopy(DEFAULT_SETTINGS)
_loaded_from_disk = False


def settings_path() -> Path:
    raw = os.getenv("OPENCLAW_SETTINGS_PATH", "").strip()
    if raw:
        return Path(raw)
    data_dir = Path(os.getenv("OPENCLAW_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
    return data_dir / "runtime_settings.json"


def get_settings() -> dict:
    global _loaded_from_disk
    with _lock:
        if not _loaded_from_disk:
            _load_unlocked()
            _loaded_from_disk = True
        return deepcopy(_settings)


def reset_settings() -> dict:
    global _settings, _loaded_from_disk
    with _lock:
        _settings = deepcopy(DEFAULT_SETTINGS)
        _loaded_from_disk = True
        _save_unlocked()
        return deepcopy(_settings)


def update_settings(payload: dict) -> dict:
    global _settings, _loaded_from_disk
    with _lock:
        if not _loaded_from_disk:
            _load_unlocked()
            _loaded_from_disk = True
        next_settings = deepcopy(_settings)

        if "sensitivity" in payload:
            next_settings["sensitivity"] = _clamp(float(payload["sensitivity"]), 0.2, 0.9)
        if "min_confidence" in payload:
            next_settings["min_confidence"] = _clamp(float(payload["min_confidence"]), 0.1, 0.95)
        if "max_detections" in payload:
            next_settings["max_detections"] = int(_clamp(float(payload["max_detections"]), 1, 40))
        if "crack_min_length" in payload:
            next_settings["crack_min_length"] = _clamp(float(payload["crack_min_length"]), 10.0, 120.0)
        if "spalling_min_area_ratio" in payload:
            next_settings["spalling_min_area_ratio"] = _clamp(
                float(payload["spalling_min_area_ratio"]), 0.001, 0.05
            )
        if "stain_min_area_ratio" in payload:
            next_settings["stain_min_area_ratio"] = _clamp(
                float(payload["stain_min_area_ratio"]), 0.001, 0.05
            )
        if "risk_high_area" in payload:
            next_settings["risk_high_area"] = _clamp(float(payload["risk_high_area"]), 0.01, 0.3)
        if "risk_medium_area" in payload:
            next_settings["risk_medium_area"] = _clamp(float(payload["risk_medium_area"]), 0.001, 0.1)
        if "risk_high_count" in payload:
            next_settings["risk_high_count"] = int(_clamp(float(payload["risk_high_count"]), 2, 30))
        if "risk_medium_count" in payload:
            next_settings["risk_medium_count"] = int(_clamp(float(payload["risk_medium_count"]), 1, 10))

        # keep medium area below high area
        if next_settings["risk_medium_area"] >= next_settings["risk_high_area"]:
            next_settings["risk_medium_area"] = max(0.001, next_settings["risk_high_area"] * 0.35)

        _settings = next_settings
        _save_unlocked()
        return deepcopy(_settings)


def settings_schema() -> list[dict]:
    return [
        {"key": "sensitivity", "label": "识别灵敏度", "min": 0.2, "max": 0.9, "step": 0.05, "type": "float"},
        {"key": "min_confidence", "label": "最低置信度", "min": 0.1, "max": 0.95, "step": 0.05, "type": "float"},
        {"key": "max_detections", "label": "最大候选数", "min": 1, "max": 40, "step": 1, "type": "int"},
        {"key": "crack_min_length", "label": "裂缝最小长度(px)", "min": 10, "max": 120, "step": 2, "type": "float"},
        {
            "key": "spalling_min_area_ratio",
            "label": "剥落最小面积比",
            "min": 0.001,
            "max": 0.05,
            "step": 0.001,
            "type": "float",
        },
        {
            "key": "stain_min_area_ratio",
            "label": "渗水最小面积比",
            "min": 0.001,
            "max": 0.05,
            "step": 0.001,
            "type": "float",
        },
        {"key": "risk_high_area", "label": "高风险面积阈值", "min": 0.01, "max": 0.3, "step": 0.005, "type": "float"},
        {
            "key": "risk_medium_area",
            "label": "中风险面积阈值",
            "min": 0.001,
            "max": 0.1,
            "step": 0.001,
            "type": "float",
        },
        {"key": "risk_high_count", "label": "高风险候选数阈值", "min": 2, "max": 30, "step": 1, "type": "int"},
        {"key": "risk_medium_count", "label": "中风险候选数阈值", "min": 1, "max": 10, "step": 1, "type": "int"},
    ]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _load_unlocked() -> None:
    global _settings
    path = settings_path()
    if not path.exists():
        _settings = deepcopy(DEFAULT_SETTINGS)
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            _settings = deepcopy(DEFAULT_SETTINGS)
            return
        # reuse validation path without nested lock
        merged = deepcopy(DEFAULT_SETTINGS)
        for key in DEFAULT_SETTINGS:
            if key in raw:
                merged[key] = raw[key]
        # apply clamps via temporary update logic
        _settings = deepcopy(DEFAULT_SETTINGS)
        for key, value in merged.items():
            if key == "sensitivity":
                _settings[key] = _clamp(float(value), 0.2, 0.9)
            elif key == "min_confidence":
                _settings[key] = _clamp(float(value), 0.1, 0.95)
            elif key == "max_detections":
                _settings[key] = int(_clamp(float(value), 1, 40))
            elif key == "crack_min_length":
                _settings[key] = _clamp(float(value), 10.0, 120.0)
            elif key == "spalling_min_area_ratio":
                _settings[key] = _clamp(float(value), 0.001, 0.05)
            elif key == "stain_min_area_ratio":
                _settings[key] = _clamp(float(value), 0.001, 0.05)
            elif key == "risk_high_area":
                _settings[key] = _clamp(float(value), 0.01, 0.3)
            elif key == "risk_medium_area":
                _settings[key] = _clamp(float(value), 0.001, 0.1)
            elif key == "risk_high_count":
                _settings[key] = int(_clamp(float(value), 2, 30))
            elif key == "risk_medium_count":
                _settings[key] = int(_clamp(float(value), 1, 10))
        if _settings["risk_medium_area"] >= _settings["risk_high_area"]:
            _settings["risk_medium_area"] = max(0.001, _settings["risk_high_area"] * 0.35)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        _settings = deepcopy(DEFAULT_SETTINGS)


def _save_unlocked() -> None:
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
