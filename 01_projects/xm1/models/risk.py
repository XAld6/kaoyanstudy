from __future__ import annotations

from typing import Iterable


RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "urgent": 4}
RISK_LABELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "urgent": "紧急风险",
}


def max_risk(*levels: str) -> str:
    valid_levels = [level for level in levels if level in RISK_ORDER]
    if not valid_levels:
        return "low"
    return max(valid_levels, key=lambda level: RISK_ORDER[level])


def assess_detection_risk(
    defect_type: str,
    confidence: float,
    area_ratio: float,
    config: dict,
) -> str:
    risk_config = config.get("risk", {})
    urgent_area = float(risk_config.get("urgent_area_ratio", 0.18))
    high_area = float(risk_config.get("high_area_ratio", 0.08))
    medium_area = float(risk_config.get("medium_area_ratio", 0.03))
    high_conf = float(risk_config.get("high_confidence", 0.7))

    if defect_type == "peeling" and area_ratio >= urgent_area:
        return "urgent"
    if defect_type == "crack" and confidence >= high_conf and area_ratio >= high_area:
        return "high"
    if area_ratio >= high_area or confidence >= 0.85:
        return "high"
    if area_ratio >= medium_area or confidence >= high_conf:
        return "medium"
    return "low"


def assess_overall_risk(detections: Iterable[dict]) -> str:
    detections = list(detections)
    if not detections:
        return "low"

    overall = max_risk(*(item.get("risk_level", "low") for item in detections))
    if len(detections) >= 3 and overall == "medium":
        return "high"
    if len(detections) >= 4 and overall == "high":
        return "urgent"
    return overall
