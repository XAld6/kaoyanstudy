from app import backend_config as cfg
from app.detector import analyze_image


def test_default_detector_is_opencv(monkeypatch):
    monkeypatch.delenv("OPENCLAW_DETECTOR", raising=False)
    status = cfg.detector_status()
    assert status["requested"] == "opencv"
    assert status["active"] == "opencv"


def test_yolo_request_falls_back_without_weights(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_DETECTOR", "yolo")
    monkeypatch.delenv("OPENCLAW_YOLO_WEIGHTS", raising=False)
    status = cfg.detector_status()
    assert status["requested"] == "yolo"
    assert status["active"] == "opencv"
    assert "回退" in status["label"] or "未配置" in status["note"] or "未安装" in status["note"]


def test_analyze_image_marks_opencv_detector(tmp_path):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (420, 260), "#d8d1c5")
    draw = ImageDraw.Draw(image)
    draw.line([(40, 40), (110, 92), (180, 88), (270, 150), (370, 210)], fill="#101010", width=4)
    path = tmp_path / "crack.png"
    image.save(path)

    result = analyze_image(path, tmp_path / "ann.png")
    assert result["quality"]["detector"] == "opencv"
    assert "OpenCV" in str(result["quality"].get("detector_label", "OpenCV"))
