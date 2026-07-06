from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from models.risk import assess_detection_risk, assess_overall_risk
from utils.config import load_settings, project_path
from utils.image import draw_detections


@dataclass
class DetectionResult:
    detections: list[dict[str, Any]]
    overall_risk: str
    result_image_path: Path
    engine: str


class WallDefectDetector:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or load_settings()
        self.class_labels = self.config["model"]["classes"]
        self.confidence_threshold = float(self.config["model"].get("confidence_threshold", 0.25))
        self.image_size = int(self.config["model"].get("image_size", 960))
        self.weights_path = project_path(self.config["paths"]["yolo_weights"])
        self.yolo_model = None
        self.engine = "rule-demo"
        self._try_load_yolo()

    def _try_load_yolo(self) -> None:
        if not self.config["model"].get("use_yolo_when_available", True):
            return
        if not self.weights_path.exists():
            return
        try:
            from ultralytics import YOLO

            self.yolo_model = YOLO(str(self.weights_path))
            self.engine = "yolo"
        except Exception:
            self.yolo_model = None
            self.engine = "rule-demo"

    def predict(self, image_path: str | Path, output_path: str | Path) -> DetectionResult:
        image_path = Path(image_path)
        output_path = Path(output_path)
        if self.yolo_model is not None:
            detections = self._predict_yolo(image_path)
        else:
            detections = self._predict_rules(image_path)

        overall_risk = assess_overall_risk(detections)
        draw_detections(image_path, detections, output_path, self.class_labels)
        return DetectionResult(detections, overall_risk, output_path, self.engine)

    def _predict_yolo(self, image_path: Path) -> list[dict[str, Any]]:
        with Image.open(image_path) as image:
            width, height = image.size
        results = self.yolo_model.predict(
            source=str(image_path),
            imgsz=self.image_size,
            conf=self.confidence_threshold,
            verbose=False,
        )
        detections: list[dict[str, Any]] = []
        if not results:
            return detections

        names = results[0].names
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls.item())
            defect_type = names.get(cls_id, str(cls_id))
            if defect_type not in self.class_labels:
                continue
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            area_ratio = max(0.0, (x2 - x1) * (y2 - y1) / (width * height))
            risk_level = assess_detection_risk(defect_type, confidence, area_ratio, self.config)
            detections.append(
                {
                    "type": defect_type,
                    "label": self.class_labels[defect_type],
                    "confidence": round(confidence, 4),
                    "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "area_ratio": round(area_ratio, 4),
                    "risk_level": risk_level,
                }
            )
        return detections

    def _predict_rules(self, image_path: Path) -> list[dict[str, Any]]:
        with Image.open(image_path).convert("RGB") as image:
            width, height = image.size
            array = np.asarray(image).astype(np.int16)

        detections = []
        detections.extend(self._find_dark_cracks(array, width, height))
        detections.extend(self._find_peeling_regions(array, width, height))
        detections.extend(self._find_seepage_regions(array, width, height))
        detections.extend(self._find_hollowing_regions(array, width, height))
        return self._dedupe_and_score(detections, width, height)

    def _find_dark_cracks(self, array: np.ndarray, width: int, height: int) -> list[dict[str, Any]]:
        gray = array.mean(axis=2)
        mask = gray < 70
        return self._components_to_detections(mask, "crack", width, height, min_area=25, confidence=0.78)

    def _find_peeling_regions(self, array: np.ndarray, width: int, height: int) -> list[dict[str, Any]]:
        red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
        mask = (red > 185) & (green > 150) & (blue < 135)
        return self._components_to_detections(mask, "peeling", width, height, min_area=300, confidence=0.82)

    def _find_seepage_regions(self, array: np.ndarray, width: int, height: int) -> list[dict[str, Any]]:
        red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
        mask = (blue > red + 18) & (green > red + 5) & (blue > 95)
        return self._components_to_detections(mask, "seepage", width, height, min_area=400, confidence=0.74)

    def _find_hollowing_regions(self, array: np.ndarray, width: int, height: int) -> list[dict[str, Any]]:
        red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
        mask = (red > 120) & (red < 180) & (green > 105) & (green < 165) & (blue > 95) & (blue < 150)
        return self._components_to_detections(mask, "hollowing", width, height, min_area=800, confidence=0.68)

    def _components_to_detections(
        self,
        mask: np.ndarray,
        defect_type: str,
        width: int,
        height: int,
        min_area: int,
        confidence: float,
    ) -> list[dict[str, Any]]:
        cv2_detections = self._components_to_detections_cv2(mask, defect_type, width, height, min_area, confidence)
        if cv2_detections is not None:
            return cv2_detections
        return self._components_to_detections_numpy(mask, defect_type, width, height, min_area, confidence)

    def _components_to_detections_cv2(
        self,
        mask: np.ndarray,
        defect_type: str,
        width: int,
        height: int,
        min_area: int,
        confidence: float,
    ) -> list[dict[str, Any]] | None:
        try:
            import cv2
        except ImportError:
            return None

        component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8),
            connectivity=4,
        )
        del labels

        detections = []
        for component_id in range(1, component_count):
            x, y, component_width, component_height, area = stats[component_id]
            if int(area) < min_area:
                continue
            bbox = [
                int(x),
                int(y),
                int(x + component_width - 1),
                int(y + component_height - 1),
            ]
            detections.append(self._build_detection(defect_type, confidence, bbox, int(area), width, height))
        return detections

    def _components_to_detections_numpy(
        self,
        mask: np.ndarray,
        defect_type: str,
        width: int,
        height: int,
        min_area: int,
        confidence: float,
    ) -> list[dict[str, Any]]:
        visited = np.zeros(mask.shape, dtype=bool)
        detections = []
        rows, cols = mask.shape
        true_points = np.argwhere(mask)
        for y, x in true_points:
            if visited[y, x]:
                continue
            stack = [(int(y), int(x))]
            visited[y, x] = True
            area = 0
            min_x = max_x = int(x)
            min_y = max_y = int(y)
            while stack:
                current_y, current_x = stack.pop()
                area += 1
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x)
                min_y = min(min_y, current_y)
                max_y = max(max_y, current_y)
                for next_y, next_x in (
                    (current_y - 1, current_x),
                    (current_y + 1, current_x),
                    (current_y, current_x - 1),
                    (current_y, current_x + 1),
                ):
                    if 0 <= next_y < rows and 0 <= next_x < cols and mask[next_y, next_x] and not visited[next_y, next_x]:
                        visited[next_y, next_x] = True
                        stack.append((next_y, next_x))
            if area < min_area:
                continue
            bbox = [min_x, min_y, max_x, max_y]
            detections.append(self._build_detection(defect_type, confidence, bbox, area, width, height))
        return detections

    def _build_detection(
        self,
        defect_type: str,
        confidence: float,
        bbox: list[int],
        area: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        area_ratio = area / (width * height)
        risk_level = assess_detection_risk(defect_type, confidence, area_ratio, self.config)
        return {
            "type": defect_type,
            "label": self.class_labels[defect_type],
            "confidence": confidence,
            "bbox": bbox,
            "area_ratio": round(area_ratio, 4),
            "risk_level": risk_level,
        }

    def _dedupe_and_score(self, detections: list[dict[str, Any]], width: int, height: int) -> list[dict[str, Any]]:
        detections = sorted(detections, key=lambda item: item["area_ratio"], reverse=True)
        kept: list[dict[str, Any]] = []
        for item in detections:
            if len(kept) >= 12:
                break
            if any(self._iou(item["bbox"], other["bbox"]) > 0.55 for other in kept):
                continue
            x1, y1, x2, y2 = item["bbox"]
            area_ratio = max(0.0, (x2 - x1 + 1) * (y2 - y1 + 1) / (width * height))
            item["area_ratio"] = round(area_ratio, 4)
            item["risk_level"] = assess_detection_risk(item["type"], item["confidence"], area_ratio, self.config)
            item["confidence"] = round(float(item["confidence"]), 4)
            kept.append(item)
        return kept

    @staticmethod
    def _iou(box_a: list[float], box_b: list[float]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = area_a + area_b - inter_area
        return inter_area / union if union else 0.0
