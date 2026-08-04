from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from app.detector import analyze_image


def _save_pil(image: Image.Image, path: Path) -> Path:
    image.save(path, format="PNG")
    return path


def make_crack_image() -> Image.Image:
    image = Image.new("RGB", (420, 260), "#d8d1c5")
    draw = ImageDraw.Draw(image)
    draw.line([(40, 40), (110, 92), (180, 88), (270, 150), (370, 210)], fill="#101010", width=4)
    draw.line([(210, 35), (230, 80), (224, 145)], fill="#303030", width=2)
    return image


def make_spalling_image() -> Image.Image:
    image = Image.new("RGB", (420, 260), "#c9c2b6")
    draw = ImageDraw.Draw(image)
    # large bright irregular patch
    draw.ellipse((100, 60, 250, 190), fill="#f4f0e8")
    draw.ellipse((125, 85, 225, 165), fill="#faf8f3")
    draw.polygon([(110, 100), (140, 50), (200, 55), (235, 95)], fill="#efe9df")
    return image


def make_stain_image() -> Image.Image:
    image = Image.new("RGB", (420, 260), "#d6cfc3")
    draw = ImageDraw.Draw(image)
    # large dark wet / discoloration patch
    draw.ellipse((70, 50, 280, 210), fill="#5a4a38")
    draw.ellipse((100, 80, 250, 180), fill="#4a3c2c")
    return image


def make_plain_image() -> Image.Image:
    return Image.new("RGB", (420, 260), "#d8d1c5")


def test_detects_crack_candidates(tmp_path: Path):
    path = _save_pil(make_crack_image(), tmp_path / "crack.png")
    result = analyze_image(path, tmp_path / "crack_ann.png")

    assert result["metrics"]["crack_count"] >= 1
    assert any(d["kind"] == "crack" for d in result["detections"])
    assert (tmp_path / "crack_ann.png").exists()


def test_detects_spalling_candidates(tmp_path: Path):
    path = _save_pil(make_spalling_image(), tmp_path / "spall.png")
    result = analyze_image(path, tmp_path / "spall_ann.png")

    assert result["metrics"]["spalling_count"] >= 1
    assert any(d["kind"] == "spalling" for d in result["detections"])
    assert result["metrics"]["detection_count"] == (
        result["metrics"]["crack_count"]
        + result["metrics"]["spalling_count"]
        + result["metrics"]["stain_count"]
    )


def test_detects_stain_candidates(tmp_path: Path):
    path = _save_pil(make_stain_image(), tmp_path / "stain.png")
    result = analyze_image(path, tmp_path / "stain_ann.png")

    assert result["metrics"]["stain_count"] >= 1
    assert any(d["kind"] == "stain" for d in result["detections"])


def test_plain_image_has_no_high_confidence_false_alarm_flood(tmp_path: Path):
    path = _save_pil(make_plain_image(), tmp_path / "plain.png")
    result = analyze_image(path, tmp_path / "plain_ann.png")

    # Uniform surface should stay clean or nearly clean
    assert result["metrics"]["detection_count"] <= 1
    assert result["metrics"]["avg_confidence"] < 0.7 or result["metrics"]["detection_count"] == 0


def test_detection_payload_fields(tmp_path: Path):
    path = _save_pil(make_crack_image(), tmp_path / "fields.png")
    result = analyze_image(path, tmp_path / "fields_ann.png")

    assert set(result["metrics"]) >= {
        "detection_count",
        "avg_confidence",
        "total_area_ratio",
        "crack_count",
        "spalling_count",
        "stain_count",
    }
    for item in result["detections"]:
        assert {
            "kind",
            "label",
            "bbox",
            "confidence",
            "area_ratio",
            "length_estimate",
        }.issubset(set(item))
        assert item["kind"] in {"crack", "spalling", "stain"}
        assert len(item["bbox"]) == 4
        if "explanation" in item:
            assert isinstance(item["explanation"], str)
