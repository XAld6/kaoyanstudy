from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from app.detector import analyze_image


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


def assess_risk(metrics: dict, quality: dict) -> tuple[str, str]:
    count = metrics["detection_count"]
    area = metrics["total_area_ratio"]
    cracks = metrics["crack_count"]
    avg_conf = metrics["avg_confidence"]
    if not quality["readable"]:
        return "中", "图像质量偏低，识别结果需要人工复核。"
    if count >= 8 or area >= 0.055 or (cracks >= 3 and avg_conf >= 0.68):
        return "高", "疑似病害数量较多或范围较大，建议优先复核。"
    if count >= 2 or area >= 0.012 or avg_conf >= 0.58:
        return "中", "检测到较明显疑似病害，建议结合现场情况确认。"
    return "低", "未发现明显高风险病害，建议纳入常规巡检记录。"


def run_damage_workflow(image_path: Path, annotated_path: Path) -> dict:
    adapter = LocalOpenClawAdapter()
    workflow = []

    step, _ = adapter.run(
        "ImageQualityAgent",
        "图像质量检查",
        lambda: {"summary": "读取巡检图片并评估尺寸、亮度、对比度与清晰度"},
    )
    workflow.append(step)

    step, detection_result = adapter.run(
        "DamageDetectionAgent",
        "病害候选识别",
        lambda: analyze_image(image_path, annotated_path),
    )
    workflow.append(
        {
            **step,
            "summary": f"识别到 {detection_result['metrics']['detection_count']} 个疑似病害候选区域",
        }
    )

    metrics = detection_result["metrics"]
    quality = detection_result["quality"]
    detections = detection_result["detections"]

    step, _ = adapter.run(
        "QuantificationAgent",
        "病害量化分析",
        lambda: {
            "summary": (
                f"裂缝{metrics['crack_count']}处，"
                f"剥落{metrics['spalling_count']}处，"
                f"色差/渗水{metrics['stain_count']}处"
            ),
        },
    )
    workflow.append(step)

    def risk_agent_output() -> dict:
        level, reason = assess_risk(metrics, quality)
        return {"summary": reason, "risk": level}

    step, risk_output = adapter.run(
        "RiskAssessmentAgent",
        "风险等级判断",
        risk_agent_output,
    )
    risk_level = risk_output["risk"]
    risk_reason = risk_output["summary"]
    workflow.append(step)

    review_status = "待复核" if risk_level in {"中", "高"} or not quality["readable"] else "自动通过"
    step, _ = adapter.run(
        "ReviewRoutingAgent",
        "复核路由",
        lambda: {"summary": f"结果进入“{review_status}”状态"},
    )
    workflow.append(step)

    step, _ = adapter.run(
        "ReportArchiveAgent",
        "报告归档输出",
        lambda: {"summary": "原图、标注图、结构化结果、工作流日志和PDF报告素材已归档"},
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
