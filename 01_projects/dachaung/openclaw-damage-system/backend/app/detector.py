from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.runtime_settings import get_settings

# BGR colors for annotation overlays
COLOR_CRACK = (0, 0, 255)  # red
COLOR_SPALLING = (0, 140, 255)  # orange
COLOR_STAIN = (220, 120, 20)  # blue-ish for wet/stain
COLOR_OK = (70, 120, 70)

LABELS = {
    "crack": "裂缝疑似",
    "spalling": "剥落疑似",
    "stain": "渗水/色差疑似",
}

DRAW_COLORS = {
    "crack": COLOR_CRACK,
    "spalling": COLOR_SPALLING,
    "stain": COLOR_STAIN,
}

MAX_DETECTIONS = 16


def _quality(gray: np.ndarray) -> dict:
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    h, w = gray.shape[:2]
    # simple exposure flags
    dark_ratio = float(np.mean(gray < 30))
    bright_ratio = float(np.mean(gray > 225))
    underexposed = dark_ratio > 0.35 or brightness < 55
    overexposed = bright_ratio > 0.25 or brightness > 210
    low_contrast = contrast < 12
    blurry = blur_score < 45
    too_small = h < 80 or w < 80

    issues: list[str] = []
    if too_small:
        issues.append("分辨率偏低")
    if underexposed:
        issues.append("偏暗/欠曝")
    if overexposed:
        issues.append("偏亮/过曝")
    if low_contrast:
        issues.append("对比度不足")
    if blurry:
        issues.append("清晰度偏低")

    readable = not too_small and contrast >= 8 and not (underexposed and overexposed)
    if readable and not issues:
        message = "图像满足基础识别条件"
        grade = "A"
    elif readable and issues:
        message = "可识别，但" + "、".join(issues) + "，建议关注"
        grade = "B"
    else:
        message = "图像质量偏低（" + ("、".join(issues) if issues else "条件不足") + "），建议补拍或人工复核"
        grade = "C"

    # 0-100 composite score for UI
    score = 100.0
    score -= 25 if too_small else 0
    score -= min(25, max(0, (12 - contrast) * 2)) if low_contrast else 0
    score -= min(20, max(0, (45 - blur_score) * 0.35)) if blurry else 0
    score -= 15 if underexposed else 0
    score -= 12 if overexposed else 0
    score = max(0.0, min(100.0, score))

    return {
        "width": int(w),
        "height": int(h),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_score": round(blur_score, 2),
        "dark_ratio": round(dark_ratio, 4),
        "bright_ratio": round(bright_ratio, 4),
        "underexposed": underexposed,
        "overexposed": overexposed,
        "low_contrast": low_contrast,
        "blurry": blurry,
        "issues": issues,
        "quality_grade": grade,
        "quality_score": round(score, 1),
        "readable": readable,
        "message": message,
    }


def _contour_geometry(contour: np.ndarray) -> dict:
    x, y, bw, bh = cv2.boundingRect(contour)
    area = float(cv2.contourArea(contour))
    box_area = float(max(1, bw * bh))
    perimeter = float(cv2.arcLength(contour, False))
    aspect = max(bw, bh) / max(1, min(bw, bh))
    fill_ratio = area / box_area
    length_estimate = max(perimeter / 2.0, math.hypot(bw, bh))
    return {
        "bbox": [int(x), int(y), int(bw), int(bh)],
        "box_area": box_area,
        "area": area,
        "perimeter": perimeter,
        "aspect": aspect,
        "fill_ratio": fill_ratio,
        "length_estimate": length_estimate,
    }


def _bbox_iou(a: list[int], b: list[int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return float(inter / max(1, union))


def _kind_rank(item: dict) -> float:
    """Geometry-aware ranking for NMS: linear -> crack, compact bright -> spalling, dark patch -> stain."""
    base = {"crack": 0.15, "spalling": 0.1, "stain": 0.05}.get(item["kind"], 0.0)
    return float(item["confidence"]) + base


def _suppress_overlaps(detections: list[dict], iou_thresh: float = 0.4) -> list[dict]:
    ordered = sorted(detections, key=_kind_rank, reverse=True)
    kept: list[dict] = []
    for item in ordered:
        if any(_bbox_iou(item["bbox"], other["bbox"]) >= iou_thresh for other in kept):
            continue
        kept.append(item)
    return kept


def _crack_mask(gray: np.ndarray) -> np.ndarray:
    mean = float(np.mean(gray))
    std = float(np.std(gray))
    threshold = int(max(35, min(125, mean - 1.65 * std)))
    dark = cv2.inRange(gray, 0, threshold)

    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    edges = cv2.Canny(cv2.GaussianBlur(enhanced, (5, 5), 0), 55, 150)

    mask = cv2.bitwise_or(dark, cv2.bitwise_and(edges, dark))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), iterations=1)
    return mask


def _spalling_mask(gray: np.ndarray) -> np.ndarray:
    """Bright / high-response blob regions that look like surface spalling."""
    mean = float(np.mean(gray))
    std = float(np.std(gray))
    bright_thr = int(min(245, max(mean + 1.15 * std, mean + 18)))
    bright = cv2.inRange(gray, bright_thr, 255)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    tophat = cv2.morphologyEx(enhanced, cv2.MORPH_TOPHAT, np.ones((15, 15), np.uint8))
    _, tophat_bin = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    mask = cv2.bitwise_or(bright, tophat_bin)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    return mask


def _stain_mask(image_bgr: np.ndarray, gray: np.ndarray) -> np.ndarray:
    """Darker / color-shifted wet or discoloration patches."""
    mean = float(np.mean(gray))
    std = float(np.std(gray))
    dark_thr = int(max(20, min(mean - 0.85 * std, mean - 12)))
    dark = cv2.inRange(gray, 0, dark_thr)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    # low-saturation brown/gray wet patches and mild yellow-brown stains
    lower_stain = np.array([0, 0, 20], dtype=np.uint8)
    upper_stain = np.array([40, 90, int(max(40, mean - 5))], dtype=np.uint8)
    color_mask = cv2.inRange(hsv, lower_stain, upper_stain)

    # also catch bluish/greenish damp discoloration
    lower_damp = np.array([80, 15, 25], dtype=np.uint8)
    upper_damp = np.array([140, 110, int(max(45, mean))], dtype=np.uint8)
    damp_mask = cv2.inRange(hsv, lower_damp, upper_damp)

    mask = cv2.bitwise_or(dark, cv2.bitwise_or(color_mask, damp_mask))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)
    return mask


def _is_crack_candidate(info: dict, image_area: float, params: dict[str, Any] | None = None) -> bool:
    settings = params or get_settings()
    # Higher sensitivity lowers the minimum crack length threshold.
    sensitivity = float(settings.get("sensitivity", 0.55))
    base_len = float(settings.get("crack_min_length", 38.0))
    min_len = base_len * (1.25 - 0.5 * sensitivity)  # sens 0.2→1.15x, 0.9→0.8x
    too_small = info["box_area"] < image_area * 0.00008 or info["length_estimate"] < min_len
    too_large_blob = info["box_area"] > image_area * 0.42 and info["fill_ratio"] > 0.12
    aspect_gate = 1.6 - 0.3 * (sensitivity - 0.55)  # easier when more sensitive
    crack_like = (info["aspect"] >= aspect_gate and info["fill_ratio"] < 0.34) or (
        info["fill_ratio"] < 0.10 and info["perimeter"] > 110
    )
    return not too_small and not too_large_blob and crack_like


def _is_spalling_candidate(info: dict, image_area: float, params: dict[str, Any] | None = None) -> bool:
    settings = params or get_settings()
    sensitivity = float(settings.get("sensitivity", 0.55))
    min_area_ratio = float(settings.get("spalling_min_area_ratio", 0.005))
    # Sensitivity scales area gate: higher → accept smaller patches.
    area_gate = min_area_ratio * (1.35 - 0.7 * sensitivity)
    too_small = info["area"] < image_area * (area_gate * 0.5) or info["box_area"] < image_area * (area_gate * 0.6)
    too_large = info["box_area"] > image_area * 0.45
    fill_gate = 0.40 - 0.08 * max(0.0, sensitivity - 0.55)
    blob_like = info["fill_ratio"] >= fill_gate and info["aspect"] <= 3.2
    sizable = info["area"] >= image_area * area_gate
    min_span = min(info["bbox"][2], info["bbox"][3]) >= max(24, int(36 - 12 * (sensitivity - 0.55)))
    return not too_small and not too_large and blob_like and sizable and min_span


def _is_stain_candidate(info: dict, image_area: float, params: dict[str, Any] | None = None) -> bool:
    settings = params or get_settings()
    sensitivity = float(settings.get("sensitivity", 0.55))
    min_area_ratio = float(settings.get("stain_min_area_ratio", 0.006))
    area_gate = min_area_ratio * (1.35 - 0.7 * sensitivity)
    too_small = info["area"] < image_area * (area_gate * 0.4) or info["box_area"] < image_area * (area_gate * 0.5)
    too_large = info["box_area"] > image_area * 0.55
    fill_gate = 0.30 - 0.06 * max(0.0, sensitivity - 0.55)
    patch_like = info["fill_ratio"] >= fill_gate and info["aspect"] <= 4.0
    not_hairline = info["perimeter"] > 90 and min(info["bbox"][2], info["bbox"][3]) >= max(20, int(28 - 10 * (sensitivity - 0.55)))
    sizable = info["area"] >= image_area * area_gate
    return not too_small and not too_large and patch_like and not_hairline and sizable


def _crack_confidence(info: dict, image_w: int, image_h: int) -> float:
    return min(
        0.96,
        0.56
        + min(info["aspect"] / 16.0, 0.22)
        + min(info["perimeter"] / max(image_w, image_h) * 0.18, 0.16)
        + (0.08 if info["fill_ratio"] < 0.08 else 0),
    )


def _spalling_confidence(info: dict, image_area: float) -> float:
    return min(
        0.93,
        0.52
        + min(info["fill_ratio"] * 0.35, 0.2)
        + min(info["area"] / image_area * 8.0, 0.16)
        + min((4.5 - min(info["aspect"], 4.5)) / 4.5 * 0.08, 0.08),
    )


def _stain_confidence(info: dict, image_area: float) -> float:
    return min(
        0.9,
        0.5
        + min(info["fill_ratio"] * 0.3, 0.18)
        + min(info["area"] / image_area * 6.0, 0.14)
        + min(info["perimeter"] / 800.0, 0.08),
    )


def _contour_mean(gray: np.ndarray, contour: np.ndarray) -> float:
    """Mean intensity inside the contour mask (more accurate than full bbox mean)."""
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, thickness=-1)
    vals = gray[mask > 0]
    if vals.size == 0:
        return 0.0
    return float(np.mean(vals))


def _collect_from_mask(
    mask: np.ndarray,
    image_area: float,
    image_w: int,
    image_h: int,
    kind: str,
    accept_fn,
    confidence_fn,
    gray: np.ndarray | None = None,
    global_mean: float | None = None,
    params: dict[str, Any] | None = None,
) -> list[dict]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    detections: list[dict] = []
    for contour in contours:
        info = _contour_geometry(contour)
        if not accept_fn(info, image_area, params):
            continue
        # Intensity gate uses contour interior, not the loose bounding box.
        if gray is not None and global_mean is not None:
            region_mean = _contour_mean(gray, contour)
            if kind == "spalling" and region_mean < global_mean + 12:
                continue
            # stains must be clearly darker than global background
            if kind == "stain" and region_mean > global_mean - 18:
                continue
        conf = confidence_fn(info, image_w, image_h) if kind == "crack" else confidence_fn(info, image_area)
        # Prefer contour area for damage ratio; bbox is only for localization.
        area_ratio = float(info["area"] / image_area) if info["area"] > 0 else float(info["box_area"] / image_area)
        detections.append(
            {
                "kind": kind,
                "label": LABELS[kind],
                "bbox": info["bbox"],
                "confidence": round(float(conf), 3),
                "area_ratio": round(area_ratio, 5),
                "length_estimate": round(float(info["length_estimate"]), 2),
                "_contour": contour,
            }
        )
    return detections


def _draw_detection(annotated: np.ndarray, item: dict) -> None:
    color = DRAW_COLORS.get(item["kind"], COLOR_CRACK)
    contour = item.get("_contour")
    x, y, bw, bh = item["bbox"]
    if contour is not None and len(contour) >= 2:
        cv2.drawContours(annotated, [contour], -1, color, 2, lineType=cv2.LINE_AA)
    else:
        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), color, 2, lineType=cv2.LINE_AA)
    tag = f"{item['label']} {item['confidence']:.2f}"
    ty = max(18, y - 6)
    cv2.putText(
        annotated,
        tag,
        (x, ty),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
        lineType=cv2.LINE_AA,
    )


def _explain_detection(item: dict) -> str:
    kind = item.get("kind")
    conf = float(item.get("confidence") or 0)
    area = float(item.get("area_ratio") or 0) * 100
    length = float(item.get("length_estimate") or 0)
    if kind == "crack":
        return f"线状暗色结构，长度约 {length:.0f}px，置信 {conf * 100:.0f}%，面积占比 {area:.2f}%"
    if kind == "spalling":
        return f"较亮紧凑斑块，疑似剥落/露骨料，置信 {conf * 100:.0f}%，面积占比 {area:.2f}%"
    if kind == "stain":
        return f"暗色/色差斑块，疑似渗水或污渍，置信 {conf * 100:.0f}%，面积占比 {area:.2f}%"
    return f"候选区域置信 {conf * 100:.0f}%，面积占比 {area:.2f}%"


def _public_detection(item: dict) -> dict:
    public = {
        "kind": item["kind"],
        "label": item["label"],
        "bbox": item["bbox"],
        "confidence": item["confidence"],
        "area_ratio": item["area_ratio"],
        "length_estimate": item["length_estimate"],
    }
    public["explanation"] = _explain_detection(public)
    return public


def analyze_image_opencv(image_path: Path, annotated_path: Path) -> dict:
    """Rule-based OpenCV screening backend (default, always available)."""
    settings = get_settings()
    min_confidence = float(settings.get("min_confidence", 0.50))
    max_detections = int(settings.get("max_detections", MAX_DETECTIONS))

    image = cv2.imdecode(np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法读取图片，请上传有效的巡检图片。")

    h, w = image.shape[:2]
    if h < 40 or w < 40:
        raise ValueError("图片尺寸过小，无法进行有效识别。")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    quality = _quality(gray)
    quality = {
        **quality,
        "detector": "opencv",
        "detector_label": "OpenCV 规则初筛",
        "runtime_params": {
            "sensitivity": settings.get("sensitivity"),
            "min_confidence": min_confidence,
            "max_detections": max_detections,
        },
    }
    image_area = float(w * h)
    global_mean = float(np.mean(gray))

    crack_mask = _crack_mask(gray)
    spalling_mask = _spalling_mask(gray)
    stain_mask = _stain_mask(image, gray)

    # Collect independently. Geometry filters separate linear cracks from dark patches;
    # intensity gates separate bright spalling from dark wet stains.
    raw: list[dict] = []
    raw.extend(
        _collect_from_mask(
            crack_mask,
            image_area,
            w,
            h,
            "crack",
            _is_crack_candidate,
            _crack_confidence,
            params=settings,
        )
    )
    raw.extend(
        _collect_from_mask(
            spalling_mask,
            image_area,
            w,
            h,
            "spalling",
            _is_spalling_candidate,
            _spalling_confidence,
            gray=gray,
            global_mean=global_mean,
            params=settings,
        )
    )
    raw.extend(
        _collect_from_mask(
            stain_mask,
            image_area,
            w,
            h,
            "stain",
            _is_stain_candidate,
            _stain_confidence,
            gray=gray,
            global_mean=global_mean,
            params=settings,
        )
    )

    detections = _suppress_overlaps(raw, iou_thresh=0.4)
    detections = [d for d in detections if float(d["confidence"]) >= min_confidence]
    detections = sorted(detections, key=lambda item: item["confidence"], reverse=True)[:max_detections]

    annotated = image.copy()
    for item in detections:
        _draw_detection(annotated, item)

    if not detections:
        cv2.putText(
            annotated,
            "No obvious damage candidate",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.78,
            COLOR_OK,
            2,
            lineType=cv2.LINE_AA,
        )

    # Legend
    legend_y = h - 16
    for idx, (kind, label) in enumerate(
        (("crack", "裂缝"), ("spalling", "剥落"), ("stain", "渗水/色差"))
    ):
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
    crack_count = sum(1 for d in public if d["kind"] == "crack")
    spalling_count = sum(1 for d in public if d["kind"] == "spalling")
    stain_count = sum(1 for d in public if d["kind"] == "stain")

    metrics = {
        "detection_count": len(public),
        "avg_confidence": avg_conf,
        "total_area_ratio": total_area_ratio,
        "crack_count": crack_count,
        "spalling_count": spalling_count,
        "stain_count": stain_count,
    }
    return {"quality": quality, "detections": public, "metrics": metrics}


def analyze_image(image_path: Path, annotated_path: Path) -> dict:
    """Dispatch to configured detector backend (opencv default, optional yolo)."""
    from app.backend_config import DETECTOR_YOLO, detector_status

    status = detector_status()
    if status["active"] == DETECTOR_YOLO:
        try:
            from app.yolo_detector import analyze_image_yolo

            return analyze_image_yolo(image_path, annotated_path)
        except Exception as exc:
            # Safe fallback keeps demos runnable without trained weights.
            result = analyze_image_opencv(image_path, annotated_path)
            result["quality"] = {
                **result["quality"],
                "detector": "opencv",
                "detector_label": "OpenCV 规则初筛（YOLO 失败回退）",
                "detector_note": str(exc),
            }
            return result

    result = analyze_image_opencv(image_path, annotated_path)
    if status["requested"] == DETECTOR_YOLO and status["active"] != DETECTOR_YOLO:
        result["quality"] = {
            **result["quality"],
            "detector_label": status["label"],
            "detector_note": status["note"],
        }
    return result
