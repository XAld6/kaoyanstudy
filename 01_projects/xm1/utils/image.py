from __future__ import annotations

import os
from functools import lru_cache
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
FONT_CANDIDATES = (
    "msyh.ttc",
    "msyh.ttf",
    "simhei.ttf",
    "simsun.ttc",
    "NotoSansCJK-Regular.ttc",
    "NotoSansSC-Regular.otf",
    "wqy-microhei.ttc",
    "SourceHanSansSC-Regular.otf",
)
FONT_SEARCH_DIRS = (
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".fonts",
)


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def verify_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


@lru_cache(maxsize=8)
def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for search_dir in FONT_SEARCH_DIRS:
        if not search_dir.is_dir():
            continue
        for candidate in FONT_CANDIDATES:
            matches = sorted(search_dir.rglob(candidate))[:1] if search_dir == Path("/usr/share/fonts") else [search_dir / candidate]
            for path in matches:
                try:
                    if path.exists():
                        return ImageFont.truetype(str(path), size)
                except OSError:
                    continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_detections(
    image_path: Path,
    detections: Iterable[dict],
    output_path: Path,
    class_labels: dict[str, str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        image_width = image.size[0]
        font_size = max(14, min(32, image_width // 50))
        font = _load_font(font_size)
        for item in detections:
            x1, y1, x2, y2 = [int(value) for value in item["bbox"]]
            risk = item.get("risk_level", "low")
            color = RISK_COLORS.get(risk, (52, 168, 83))
            label = item.get("label") or class_labels.get(item["type"], item["type"])
            text = f"{label} {item['confidence']:.2f}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            line_width = max(3, round(font_size / 6))
            draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)
            label_y = max(0, y1 - text_height - 10)
            draw.rectangle(
                [x1, label_y, x1 + text_width + 10, label_y + text_height + 8],
                fill=color,
            )
            draw.text((x1 + 5, label_y + 4), text, fill=(255, 255, 255), font=font)
        image.save(output_path)
