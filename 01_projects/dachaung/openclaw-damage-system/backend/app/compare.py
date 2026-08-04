"""Compare two detection records for demo / review."""

from __future__ import annotations

from typing import Any


def _kind_counts(record: dict[str, Any]) -> dict[str, int]:
    metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
    return {
        "crack": int(metrics.get("crack_count") or 0),
        "spalling": int(metrics.get("spalling_count") or 0),
        "stain": int(metrics.get("stain_count") or 0),
        "total": int(metrics.get("detection_count") or record.get("detection_count") or 0),
    }


def _summary(record: dict[str, Any]) -> dict[str, Any]:
    metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
    quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
    return {
        "id": record.get("id"),
        "filename": record.get("filename"),
        "created_at": record.get("created_at"),
        "risk_level": record.get("risk_level"),
        "review_status": record.get("review_status"),
        "confidence": record.get("confidence"),
        "detection_count": record.get("detection_count"),
        "risk_reason": record.get("risk_reason"),
        "original_url": record.get("original_url"),
        "annotated_url": record.get("annotated_url"),
        "metrics": {
            "crack_count": metrics.get("crack_count", 0),
            "spalling_count": metrics.get("spalling_count", 0),
            "stain_count": metrics.get("stain_count", 0),
            "total_area_ratio": metrics.get("total_area_ratio", 0),
            "avg_confidence": metrics.get("avg_confidence", record.get("confidence", 0)),
        },
        "quality": {
            "grade": quality.get("quality_grade") or "",
            "score": quality.get("quality_score"),
            "readable": quality.get("readable", True),
            "issues": quality.get("issues") if isinstance(quality.get("issues"), list) else [],
        },
        "detector": quality.get("detector_label") or quality.get("detector") or "",
        "readable": quality.get("readable", True),
    }


def compare_records(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_counts = _kind_counts(left)
    right_counts = _kind_counts(right)
    left_metrics = left.get("metrics") if isinstance(left.get("metrics"), dict) else {}
    right_metrics = right.get("metrics") if isinstance(right.get("metrics"), dict) else {}

    risk_order = {"低": 1, "中": 2, "高": 3}
    left_risk = str(left.get("risk_level") or "低")
    right_risk = str(right.get("risk_level") or "低")
    risk_delta = risk_order.get(right_risk, 0) - risk_order.get(left_risk, 0)

    conf_left = float(left.get("confidence") or 0)
    conf_right = float(right.get("confidence") or 0)
    area_left = float(left_metrics.get("total_area_ratio") or 0)
    area_right = float(right_metrics.get("total_area_ratio") or 0)

    notes: list[str] = []
    if risk_delta > 0:
        notes.append(f"风险上升：{left_risk} → {right_risk}")
    elif risk_delta < 0:
        notes.append(f"风险下降：{left_risk} → {right_risk}")
    else:
        notes.append(f"风险等级相同：{left_risk}")

    for kind in ("crack", "spalling", "stain"):
        delta = right_counts[kind] - left_counts[kind]
        if delta:
            label = {"crack": "裂缝", "spalling": "剥落", "stain": "渗水"}[kind]
            notes.append(f"{label}候选变化 {delta:+d}")

    if abs(area_right - area_left) >= 0.005:
        notes.append(f"面积占比变化 {(area_right - area_left) * 100:+.2f}%")
    if abs(conf_right - conf_left) >= 0.05:
        notes.append(f"平均置信度变化 {(conf_right - conf_left) * 100:+.1f}%")

    left_q = left.get("quality") if isinstance(left.get("quality"), dict) else {}
    right_q = right.get("quality") if isinstance(right.get("quality"), dict) else {}
    left_score = left_q.get("quality_score")
    right_score = right_q.get("quality_score")
    if isinstance(left_score, (int, float)) and isinstance(right_score, (int, float)):
        if abs(float(right_score) - float(left_score)) >= 5:
            notes.append(f"图像质量评分变化 {float(right_score) - float(left_score):+.1f}")

    left_grade = str(left_q.get("quality_grade") or "")
    right_grade = str(right_q.get("quality_grade") or "")
    if left_grade and right_grade and left_grade != right_grade:
        notes.append(f"质量等级变化：{left_grade} → {right_grade}")

    # verdict for demo
    if risk_delta > 0 or right_counts["total"] > left_counts["total"]:
        verdict = "右侧病害迹象更显著或风险更高"
    elif risk_delta < 0 or right_counts["total"] < left_counts["total"]:
        verdict = "右侧病害迹象更轻或风险更低"
    else:
        verdict = "两侧整体风险与候选规模接近"

    return {
        "left": _summary(left),
        "right": _summary(right),
        "delta": {
            "risk_delta": risk_delta,
            "confidence_delta": round(conf_right - conf_left, 4),
            "area_ratio_delta": round(area_right - area_left, 5),
            "count_delta": {
                "crack": right_counts["crack"] - left_counts["crack"],
                "spalling": right_counts["spalling"] - left_counts["spalling"],
                "stain": right_counts["stain"] - left_counts["stain"],
                "total": right_counts["total"] - left_counts["total"],
            },
            "quality_score_delta": (
                round(float(right_score) - float(left_score), 1)
                if isinstance(left_score, (int, float)) and isinstance(right_score, (int, float))
                else None
            ),
        },
        "notes": notes,
        "verdict": verdict,
    }
