from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np


def _quality(gray: np.ndarray) -> dict:
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    readable = gray.shape[0] >= 80 and gray.shape[1] >= 80 and contrast >= 8
    return {
        "width": int(gray.shape[1]),
        "height": int(gray.shape[0]),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_score": round(blur_score, 2),
        "readable": readable,
        "message": "图像满足基础识别条件" if readable else "图像质量偏低，建议补拍或人工复核",
    }


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


def _candidate_is_crack(contour: np.ndarray, image_area: float) -> tuple[bool, dict]:
    x, y, bw, bh = cv2.boundingRect(contour)
    area = float(cv2.contourArea(contour))
    box_area = float(bw * bh)
    perimeter = float(cv2.arcLength(contour, False))
    aspect = max(bw, bh) / max(1, min(bw, bh))
    fill_ratio = area / max(1.0, box_area)
    length_estimate = max(perimeter / 2.0, math.hypot(bw, bh))

    too_small = box_area < image_area * 0.00008 or length_estimate < 38
    too_large_blob = box_area > image_area * 0.42 and fill_ratio > 0.12
    crack_like = (aspect >= 1.6 and fill_ratio < 0.34) or (fill_ratio < 0.10 and perimeter > 110)
    return (not too_small and not too_large_blob and crack_like), {
        "bbox": [int(x), int(y), int(bw), int(bh)],
        "box_area": box_area,
        "area": area,
        "perimeter": perimeter,
        "aspect": aspect,
        "fill_ratio": fill_ratio,
        "length_estimate": length_estimate,
    }


def analyze_image(image_path: Path, annotated_path: Path) -> dict:
    image = cv2.imdecode(np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法读取图片，请上传有效的巡检图片。")

    h, w = image.shape[:2]
    if h < 40 or w < 40:
        raise ValueError("图片尺寸过小，无法进行有效识别。")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    quality = _quality(gray)
    mask = _crack_mask(gray)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    annotated = image.copy()
    image_area = float(w * h)
    detections = []

    for contour in contours:
        is_crack, info = _candidate_is_crack(contour, image_area)
        if not is_crack:
            continue

        x, y, bw, bh = info["bbox"]
        confidence = min(
            0.96,
            0.56
            + min(info["aspect"] / 16.0, 0.22)
            + min(info["perimeter"] / max(w, h) * 0.18, 0.16)
            + (0.08 if info["fill_ratio"] < 0.08 else 0),
        )
        detections.append(
            {
                "kind": "crack",
                "label": "裂缝疑似",
                "bbox": info["bbox"],
                "confidence": round(float(confidence), 3),
                "area_ratio": round(float(info["box_area"] / image_area), 5),
                "length_estimate": round(float(info["length_estimate"]), 2),
            }
        )

        roi = mask[y : y + bh, x : x + bw]
        roi_contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for roi_contour in roi_contours:
            if cv2.arcLength(roi_contour, False) < 22:
                continue
            shifted = roi_contour + np.array([[[x, y]]])
            cv2.drawContours(annotated, [shifted], -1, (0, 0, 255), 2, lineType=cv2.LINE_AA)

    detections = sorted(detections, key=lambda item: item["confidence"], reverse=True)[:12]
    if not detections:
        cv2.putText(
            annotated,
            "No obvious crack candidate",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.78,
            (70, 120, 70),
            2,
        )

    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".png", annotated)
    if not ok:
        raise ValueError("标注图生成失败。")
    encoded.tofile(str(annotated_path))

    avg_conf = round(float(np.mean([d["confidence"] for d in detections])) if detections else 0.0, 3)
    total_area_ratio = round(float(sum(d["area_ratio"] for d in detections)), 5)
    metrics = {
        "detection_count": len(detections),
        "avg_confidence": avg_conf,
        "total_area_ratio": total_area_ratio,
        "crack_count": len(detections),
        "spalling_count": 0,
        "stain_count": 0,
    }
    return {"quality": quality, "detections": detections, "metrics": metrics}
