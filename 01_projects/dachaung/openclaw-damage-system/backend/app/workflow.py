from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from app.detector import analyze_image
from app.runtime_settings import get_settings


class LocalOpenClawAdapter:
    mode = "local-compatible"

    def run(self, agent: str, label: str, fn: Callable[[], dict | str]) -> tuple[dict, dict | str]:
        start = time.perf_counter()
        output = fn()
        duration = int((time.perf_counter() - start) * 1000)
        if isinstance(output, dict):
            summary = output.get("summary") or output.get("message") or f"{label}完成"
        else:
            summary = str(output)
        step = {
            "agent": agent,
            "label": label,
            "status": "completed",
            "duration_ms": max(1, duration),
            "summary": summary,
        }
        return step, output


def assess_risk(
    metrics: dict,
    quality: dict,
    params: dict[str, Any] | None = None,
) -> tuple[str, str]:
    settings = params or get_settings()
    high_area = float(settings.get("risk_high_area", 0.055))
    medium_area = float(settings.get("risk_medium_area", 0.012))
    high_count = int(settings.get("risk_high_count", 8))
    medium_count = int(settings.get("risk_medium_count", 1))

    count = metrics["detection_count"]
    area = metrics["total_area_ratio"]
    cracks = metrics["crack_count"]
    spalling = metrics.get("spalling_count", 0)
    stain = metrics.get("stain_count", 0)
    avg_conf = metrics["avg_confidence"]
    multi_type = sum(1 for n in (cracks, spalling, stain) if n > 0)

    if not quality["readable"]:
        return "中", "图像质量偏低，识别结果需要人工复核。"

    # High: dense findings, large coverage, multi-crack high-confidence, or multi-type + area
    if (
        count >= high_count
        or area >= high_area
        or (cracks >= 3 and avg_conf >= 0.68)
        or (spalling >= 2 and area >= high_area * 0.55)
        or (spalling >= 1 and area >= high_area * 0.72)
        or (stain >= 1 and area >= high_area * 0.9)
        or (multi_type >= 2 and area >= high_area * 0.45)
        or (multi_type >= 2 and count >= max(3, medium_count + 2))
    ):
        return "高", "疑似病害数量较多或范围较大，建议优先复核。"

    if count >= medium_count or area >= medium_area or avg_conf >= 0.58:
        return "中", "检测到较明显疑似病害，建议结合现场情况确认。"

    return "低", "未发现明显高风险病害，建议纳入常规巡检记录。"


def _quality_summary(quality: dict) -> str:
    readable = "可识别" if quality.get("readable") else "质量偏低"
    width = quality.get("width", "?")
    height = quality.get("height", "?")
    brightness = quality.get("brightness", 0)
    contrast = quality.get("contrast", 0)
    blur = quality.get("blur_score", 0)
    detector = quality.get("detector_label") or quality.get("detector") or "OpenCV"
    grade = quality.get("quality_grade")
    score = quality.get("quality_score")
    grade_text = f" · 等级{grade}" if grade else ""
    score_text = f" · 评分{float(score):.0f}" if isinstance(score, (int, float)) else ""
    issues = quality.get("issues") if isinstance(quality.get("issues"), list) else []
    issue_text = f" · 问题:{'、'.join(str(x) for x in issues)}" if issues else ""
    return (
        f"{readable} · {width}×{height} · "
        f"亮度{float(brightness):.0f} · 对比度{float(contrast):.1f} · 清晰度{float(blur):.0f} · "
        f"后端{detector}{grade_text}{score_text}{issue_text}"
    )


def _detection_summary(metrics: dict, detections: list[dict]) -> str:
    count = metrics.get("detection_count", 0)
    if count <= 0:
        return "未检出明显病害候选区域"
    top = sorted(detections, key=lambda d: float(d.get("confidence") or 0), reverse=True)[:2]
    top_text = "、".join(
        f"{item.get('label') or item.get('kind')} {float(item.get('confidence') or 0) * 100:.0f}%"
        for item in top
    )
    return f"识别到 {count} 个疑似病害候选；高置信：{top_text}"


def _quant_summary(metrics: dict) -> str:
    return (
        f"裂缝{metrics.get('crack_count', 0)}处 · "
        f"剥落{metrics.get('spalling_count', 0)}处 · "
        f"渗水/色差{metrics.get('stain_count', 0)}处 · "
        f"面积占比{float(metrics.get('total_area_ratio', 0)) * 100:.2f}% · "
        f"均置信{float(metrics.get('avg_confidence', 0)):.2f}"
    )


def _risk_summary(level: str, reason: str, metrics: dict) -> str:
    return (
        f"风险={level}；{reason}"
        f"（候选{metrics.get('detection_count', 0)}，"
        f"裂{metrics.get('crack_count', 0)}/"
        f"剥{metrics.get('spalling_count', 0)}/"
        f"渗{metrics.get('stain_count', 0)}）"
    )


def run_damage_workflow(image_path: Path, annotated_path: Path) -> dict:
    adapter = LocalOpenClawAdapter()
    workflow = []

    # Quality step summary is filled after detection provides quality metrics.
    step, detection_result = adapter.run(
        "DamageDetectionAgent",
        "病害候选识别",
        lambda: analyze_image(image_path, annotated_path),
    )
    metrics = detection_result["metrics"]
    quality = detection_result["quality"]
    detections = detection_result["detections"]

    quality_step, _ = adapter.run(
        "ImageQualityAgent",
        "图像质量检查",
        lambda: {"summary": _quality_summary(quality)},
    )
    # Keep logical order: quality -> detection -> ...
    workflow.append(quality_step)
    workflow.append(
        {
            **step,
            "summary": _detection_summary(metrics, detections),
        }
    )

    step, _ = adapter.run(
        "QuantificationAgent",
        "病害量化分析",
        lambda: {"summary": _quant_summary(metrics)},
    )
    workflow.append(step)

    risk_params = get_settings()

    def risk_agent_output() -> dict:
        level, reason = assess_risk(metrics, quality, risk_params)
        return {"summary": _risk_summary(level, reason, metrics), "risk": level, "reason": reason}

    step, risk_output = adapter.run(
        "RiskAssessmentAgent",
        "风险等级判断",
        risk_agent_output,
    )
    risk_level = risk_output["risk"]
    risk_reason = risk_output.get("reason") or assess_risk(metrics, quality, risk_params)[1]
    workflow.append(step)

    review_status = "待复核" if risk_level in {"中", "高"} or not quality["readable"] else "自动通过"
    review_hint = (
        "自动通过，可直接归档"
        if review_status == "自动通过"
        else "进入人工复核队列，建议结合现场确认"
    )
    step, _ = adapter.run(
        "ReviewRoutingAgent",
        "复核路由",
        lambda: {"summary": f"状态“{review_status}” · {review_hint}"},
    )
    workflow.append(step)

    step, _ = adapter.run(
        "ReportArchiveAgent",
        "报告归档输出",
        lambda: {
            "summary": (
                f"已归档原图/标注图/结构化结果/工作流日志；"
                f"可导出PDF（候选{metrics.get('detection_count', 0)}，风险{risk_level}）"
            )
        },
    )
    workflow.append(step)

    return {
        "quality": quality,
        "detections": detections,
        "metrics": metrics,
        "workflow": workflow,
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "review_status": review_status,
        "confidence": metrics["avg_confidence"],
    }
