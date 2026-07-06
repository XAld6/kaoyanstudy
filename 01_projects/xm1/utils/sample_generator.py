from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from utils.config import load_settings, project_path


def generate_samples(output_dir: str | Path | None = None, count: int = 8) -> list[Path]:
    settings = load_settings()
    target_dir = project_path(output_dir or settings["paths"]["samples_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)

    random.seed(42)
    paths = []
    defect_modes = ["crack", "peeling", "seepage", "hollowing", "mixed", "normal"]
    for index in range(count):
        mode = defect_modes[index % len(defect_modes)]
        image = _base_wall()
        draw = ImageDraw.Draw(image)
        if mode == "crack":
            _draw_crack(draw)
        elif mode == "peeling":
            _draw_peeling(draw)
        elif mode == "seepage":
            _draw_seepage(draw)
        elif mode == "hollowing":
            _draw_hollowing(draw)
        elif mode == "mixed":
            _draw_crack(draw)
            _draw_peeling(draw)
            _draw_seepage(draw)
        _draw_window_hints(draw)
        path = target_dir / f"sample_{index + 1:02d}_{mode}.jpg"
        image.save(path, quality=92)
        paths.append(path)
    return paths


def _base_wall(width: int = 960, height: int = 640) -> Image.Image:
    image = Image.new("RGB", (width, height), (218, 216, 207))
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 120):
        draw.line([(x, 0), (x, height)], fill=(198, 197, 190), width=1)
    for y in range(0, height, 80):
        draw.line([(0, y), (width, y)], fill=(199, 198, 191), width=1)
    for _ in range(900):
        x = random.randrange(width)
        y = random.randrange(height)
        shade = random.randint(190, 230)
        draw.point((x, y), fill=(shade, shade, max(180, shade - 10)))
    return image


def _draw_window_hints(draw: ImageDraw.ImageDraw) -> None:
    for x in (90, 620):
        draw.rectangle([x, 70, x + 150, 180], fill=(95, 116, 95), outline=(72, 86, 70), width=4)
        draw.line([(x + 75, 70), (x + 75, 180)], fill=(72, 86, 70), width=3)
        draw.line([(x, 125), (x + 150, 125)], fill=(72, 86, 70), width=3)


def _draw_crack(draw: ImageDraw.ImageDraw) -> None:
    points = [(420, 80), (405, 150), (435, 230), (410, 310), (455, 410), (430, 540)]
    draw.line(points, fill=(23, 24, 22), width=7, joint="curve")
    branches = [[(432, 235), (505, 270), (540, 330)], [(420, 330), (360, 370), (330, 445)]]
    for branch in branches:
        draw.line(branch, fill=(31, 31, 29), width=4)


def _draw_peeling(draw: ImageDraw.ImageDraw) -> None:
    polygon = [(160, 320), (245, 275), (340, 305), (370, 420), (285, 510), (170, 480)]
    draw.polygon(polygon, fill=(214, 167, 95), outline=(105, 78, 52))
    draw.polygon([(205, 350), (285, 330), (320, 390), (275, 455), (205, 435)], fill=(236, 194, 128))


def _draw_seepage(draw: ImageDraw.ImageDraw) -> None:
    for x in range(610, 750, 18):
        bottom = random.randint(430, 560)
        draw.line([(x, 230), (x + random.randint(-14, 14), bottom)], fill=(79, 117, 139), width=random.randint(7, 12))
    draw.ellipse([590, 205, 770, 295], fill=(93, 131, 150), outline=(66, 99, 121), width=3)


def _draw_hollowing(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse([240, 210, 470, 390], fill=(151, 135, 118), outline=(96, 83, 73), width=5)
    draw.ellipse([285, 250, 430, 355], fill=(169, 153, 135))
