from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw


def make_crack_image() -> BytesIO:
    image = Image.new("RGB", (420, 260), "#d8d1c5")
    draw = ImageDraw.Draw(image)
    draw.line([(40, 40), (110, 92), (180, 88), (270, 150), (370, 210)], fill="#101010", width=4)
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def make_plain_image() -> BytesIO:
    image = Image.new("RGB", (420, 260), "#d0c9bd")
    # mild noise-like dots for quality pass without damage
    draw = ImageDraw.Draw(image)
    for i in range(0, 420, 20):
        draw.point((i, (i * 3) % 260), fill="#c4bdb1")
        draw.point((i + 3, (i * 5) % 260), fill="#ddd6ca")
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_batch_detect_processes_multiple_files(client: TestClient):
    response = client.post(
        "/api/detect/batch",
        files=[
            ("files", ("a.png", make_crack_image(), "image/png")),
            ("files", ("b.png", make_plain_image(), "image/png")),
        ],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok_count"] + body["error_count"] == 2
    assert body["ok_count"] >= 1
    assert len(body["records"]) == body["ok_count"]


def test_stats_endpoint_aggregates_records(client: TestClient):
    client.post("/api/detect", files={"file": ("s1.png", make_crack_image(), "image/png")})
    client.post("/api/detect", files={"file": ("s2.png", make_plain_image(), "image/png")})

    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert "by_risk" in body
    assert set(body["by_risk"]) == {"低", "中", "高"}
    assert "avg_confidence" in body


def test_records_filter_by_risk_and_query(client: TestClient):
    crack = client.post(
        "/api/detect",
        files={"file": ("bridge-crack.png", make_crack_image(), "image/png")},
    ).json()
    client.post(
        "/api/detect",
        files={"file": ("wall-plain.png", make_plain_image(), "image/png")},
    )

    by_name = client.get("/api/records", params={"q": "bridge"})
    assert by_name.status_code == 200
    names = [item["filename"] for item in by_name.json()]
    assert any("bridge" in name for name in names)

    by_risk = client.get("/api/records", params={"risk_level": crack["risk_level"]})
    assert by_risk.status_code == 200
    assert all(item["risk_level"] == crack["risk_level"] for item in by_risk.json())


def test_delete_record_removes_from_list(client: TestClient):
    created = client.post(
        "/api/detect",
        files={"file": ("to-delete.png", make_crack_image(), "image/png")},
    ).json()
    record_id = created["id"]

    deleted = client.delete(f"/api/records/{record_id}")
    assert deleted.status_code == 200
    assert deleted.json()["ok"] is True

    missing = client.get(f"/api/records/{record_id}")
    assert missing.status_code == 404

    again = client.delete(f"/api/records/{record_id}")
    assert again.status_code == 404
