from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
RISK_COLORS = {
    "low": (52, 168, 83),
    "medium": (251, 188, 5),
    "high": (234, 103, 30),
    "urgent": (217, 48, 37),
}


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def verify_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def draw_detections(
    image_path: Path,
    detections: Iterable[dict],
    output_path: Path,
    class_labels: dict[str, str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for item in detections:
            x1, y1, x2, y2 = [int(value) for value in item["bbox"]]
            risk = item.get("risk_level", "low")
            color = RISK_COLORS.get(risk, (52, 168, 83))
            text = f"{item['type']} {item['confidence']:.2f}"
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
            text_bbox = draw.textbbox((x1, y1), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            label_y = max(0, y1 - text_height - 8)
            draw.rectangle(
                [x1, label_y, x1 + text_width + 8, label_y + text_height + 6],
                fill=color,
            )
            draw.text((x1 + 4, label_y + 3), text, fill=(255, 255, 255), font=font)
        image.save(output_path)
