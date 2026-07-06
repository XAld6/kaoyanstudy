from io import BytesIO

from PIL import Image


def make_large_image() -> BytesIO:
    image = Image.new("RGB", (1700, 1700), "#7d7d7d")
    buf = BytesIO()
    image.save(buf, format="BMP")
    buf.seek(0)
    return buf


def test_rejects_oversized_uploads(client, tmp_path):
    response = client.post(
        "/api/detect",
        files={"file": ("big.bmp", make_large_image(), "image/bmp")},
    )

    assert response.status_code == 413
    assert "上传图片" in response.json()["detail"]
    assert not any((tmp_path / "uploads").iterdir())
