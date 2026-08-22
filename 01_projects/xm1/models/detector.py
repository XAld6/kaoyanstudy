from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
from PIL import Image

from models.risk import assess_detection_risk, assess_overall_risk
from utils.config import load_settings, project_path
from utils.image import draw_detections

logger = logging.getLogger(__name__)

DEFAULT_RULE_MAX_SIDE = 1280


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
        self.device = str(self.config["model"].get("device", "auto")).lower()
        self.half = bool(self.config["model"].get("half", False))
        self.rule_max_side = int(
            self.config.get("rules", {}).get("max_side", DEFAULT_RULE_MAX_SIDE)
        )
        self.weights_path = project_path(self.config["paths"]["yolo_weights"])
        self.yolo_model = None
        self.engine = "rule-demo"
        self._infer_lock = threading.Lock()
        self._yolo_extra_args: dict[str, Any] | None = None
        self._try_load_yolo()

    def _try_load_yolo(self) -> None:
        if not self.config["model"].get("use_yolo_when_available", True):
            return
        if not self.weights_path.exists():
            logger.info("YOLO weights not found at %s, using rule-demo engine.", self.weights_path)
            return
        try:
            from ultralytics import YOLO

            self.yolo_model = YOLO(str(self.weights_path))
            self.engine = "yolo"
            logger.info("YOLO engine loaded from %s.", self.weights_path)
        except Exception:
            self.yolo_model = None
            self.engine = "rule-demo"
            logger.warning(
                "Failed to load YOLO weights at %s, falling back to rule-demo engine.",
                self.weights_path,
                exc_info=True,
            )

    def _resolve_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _yolo_args(self) -> dict[str, Any]:
        if self._yolo_extra_args is None:
            args: dict[str, Any] = {}
            device = self._resolve_device()
            if device != "auto":
                args["device"] = device
                if self.half and device.startswith("cuda"):
                    args["half"] = True
            self._yolo_extra_args = args
        return self._yolo_extra_args

    def predict(self, image_path: str | Path, output_path: str | Path) -> DetectionResult:
        return self.predict_batch([(Path(image_path), Path(output_path))])[0]

    def predict_batch(self, pairs: Sequence[tuple[Path, Path]]) -> list[DetectionResult]:
        if not pairs:
            return []
        with self._infer_lock:
            if self.yolo_model is not None:
                detections_list = self._predict_yolo_batch([image_path for image_path, _ in pairs])
            else:
                detections_list = [self._predict_rules(image_path) for image_path, _ in pairs]
        results = []
        for detections, (image_path, output_path) in zip(detections_list, pairs):
            overall_risk = assess_overall_risk(detections)
            draw_detections(image_path, detections, output_path, self.class_labels)
            results.append(DetectionResult(detections, overall_risk, output_path, self.engine))
        return results

    def _predict_yolo_batch(self, image_paths: list[Path]) -> list[list[dict[str, Any]]]:
        sources = [str(path) for path in image_paths]
        results = self.yolo_model.predict(
            source=sources,
            imgsz=self.image_size,
            conf=self.confidence_threshold,
            verbose=False,
            **self._yolo_args(),
        )
        if results is None or len(results) != len(sources):
            logger.warning(
                "YOLO batch result count mismatch (%s != %s), retrying per image.",
                0 if results is None else len(results),
                len(sources),
            )
            results = [
                self.yolo_model.predict(source=source, imgsz=self.image_size, conf=self.confidence_threshold, verbose=False, **self._yolo_args())[0]
                for source in sources
            ]

        detections_list: list[list[dict[str, Any]]] = []
        for result in results:
            height, width = (int(v) for v in result.orig_shape)
            detections: list[dict[str, Any]] = []
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                detections_list.append(detections)
                continue
            names = result.names
            for box in boxes:
                cls_id = int(box.cls.item())
                defect_type = names.get(cls_id, str(cls_id))
                if defect_type not in self.class_labels:
                    continue
                confidence = float(box.conf.item())
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                area_ratio = max(0.0, (x2 - x1) * (y2 - y1) / max(1, width * height))
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
            detections_list.append(detections)
        return detections_list

    def _predict_rules(self, image_path: Path) -> list[dict[str, Any]]:
        with Image.open(image_path) as source:
            source.load()
            width, height = source.size
            scale = min(1.0, self.rule_max_side / max(width, height))
            if scale < 1.0:
                working = source.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.BILINEAR)
            else:
                working = source
            array = np.asarray(working.convert("RGB")).astype(np.int16)

        work_width, work_height = array.shape[1], array.shape[0]
        detections: list[dict[str, Any]] = []
        detections.extend(self._find_dark_cracks(array, work_width, work_height))
        detections.extend(self._find_peeling_regions(array, work_width, work_height))
        detections.extend(self._find_seepage_regions(array, work_width, work_height))
        detections.extend(self._find_hollowing_regions(array, work_width, work_height))
        detections = self._dedupe_and_score(detections)

        inverse = 1.0 / scale
        for item in detections:
            item["bbox"] = [int(round(value * inverse)) for value in item["bbox"]]
        return detections

    def _find_dark_cracks(self, array: np.ndarray, width: int, height: int) -> list[dict[str, Any]]:
        gray = array.mean(axis=2)
        mask = self._close_mask(gray < 70)
        return self._components_to_detections(
            mask, "crack", width, height, min_area=25, confidence=0.78, accept=self._is_crack_shape
        )

    @staticmethod
    def _is_crack_shape(area: int, bbox_width: int, bbox_height: int) -> bool:
        long_side = max(bbox_width, bbox_height)
        short_side = max(1, min(bbox_width, bbox_height))
        elongation = long_side / short_side
        fill_ratio = area / max(1, long_side * short_side)
        return long_side >= 12 and (elongation >= 3.0 or fill_ratio <= 0.25)

    @staticmethod
    def _close_mask(mask: np.ndarray) -> np.ndarray:
        try:
            import cv2
        except ImportError:
            return mask
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
        return closed.astype(bool)

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
        accept: Callable[[int, int, int], bool] | None = None,
    ) -> list[dict[str, Any]]:
        cv2_detections = self._components_to_detections_cv2(
            mask, defect_type, width, height, min_area, confidence, accept
        )
        if cv2_detections is not None:
            return cv2_detections
        return self._components_to_detections_numpy(
            mask, defect_type, width, height, min_area, confidence, accept
        )

    def _components_to_detections_cv2(
        self,
        mask: np.ndarray,
        defect_type: str,
        width: int,
        height: int,
        min_area: int,
        confidence: float,
        accept: Callable[[int, int, int], bool] | None,
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
            area = int(area)
            if area < min_area:
                continue
            if accept is not None and not accept(area, int(component_width), int(component_height)):
                continue
            bbox = [
                int(x),
                int(y),
                int(x + component_width - 1),
                int(y + component_height - 1),
            ]
            detections.append(self._build_detection(defect_type, confidence, bbox, area, width, height))
        return detections

    def _components_to_detections_numpy(
        self,
        mask: np.ndarray,
        defect_type: str,
        width: int,
        height: int,
        min_area: int,
        confidence: float,
        accept: Callable[[int, int, int], bool] | None,
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
            bbox_width = max_x - min_x + 1
            bbox_height = max_y - min_y + 1
            if accept is not None and not accept(area, bbox_width, bbox_height):
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
        area_ratio = area / max(1, width * height)
        risk_level = assess_detection_risk(defect_type, confidence, area_ratio, self.config)
        return {
            "type": defect_type,
            "label": self.class_labels[defect_type],
            "confidence": round(float(confidence), 4),
            "bbox": bbox,
            "area_ratio": round(area_ratio, 4),
            "risk_level": risk_level,
        }

    def _dedupe_and_score(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        detections = sorted(detections, key=lambda item: item["area_ratio"], reverse=True)
        kept: list[dict[str, Any]] = []
        for item in detections:
            if len(kept) >= 12:
                break
            if any(self._iou(item["bbox"], other["bbox"]) > 0.55 for other in kept):
                continue
            kept.append(item)
        return kept

    @staticmethod
    def _iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = area_a + area_b - inter_area
        return inter_area / union if union else 0.0
