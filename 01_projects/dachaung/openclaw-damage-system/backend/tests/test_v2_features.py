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
    draw = ImageDraw.Draw(image)
    for i in range(0, 420, 20):
        draw.point((i, (i * 3) % 260), fill="#c4bdb1")
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_records_page_pagination(client: TestClient):
    for i in range(3):
        client.post(
            "/api/detect",
            files={"file": (f"page-{i}.png", make_plain_image(), "image/png")},
        )
    res = client.get("/api/records/page", params={"page": 1, "page_size": 2})
    assert res.status_code == 200
    body = res.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["has_next"] is True


def test_records_sort_and_offset(client: TestClient):
    client.post("/api/detect", files={"file": ("sort-a.png", make_crack_image(), "image/png")})
    client.post("/api/detect", files={"file": ("sort-b.png", make_plain_image(), "image/png")})
    res = client.get("/api/records", params={"sort": "filename", "order": "asc", "limit": 50})
    assert res.status_code == 200
    names = [item["filename"] for item in res.json()]
    assert names == sorted(names)


def test_stats_has_timeline_and_buckets(client: TestClient):
    client.post("/api/detect", files={"file": ("tl.png", make_crack_image(), "image/png")})
    res = client.get("/api/stats")
    assert res.status_code == 200
    body = res.json()
    assert "timeline" in body
    assert "confidence_buckets" in body
    assert "by_review" in body
    assert set(body["by_risk"]) == {"低", "中", "高"}


def test_batch_redetect(client: TestClient):
    a = client.post("/api/detect", files={"file": ("br-a.png", make_crack_image(), "image/png")}).json()
    b = client.post("/api/detect", files={"file": ("br-b.png", make_plain_image(), "image/png")}).json()
    res = client.post("/api/records/batch-redetect", json={"ids": [a["id"], b["id"]]})
    assert res.status_code == 200
    body = res.json()
    assert body["ok_count"] + body["error_count"] == 2
    assert body["ok_count"] >= 1


def test_neighbors_endpoint(client: TestClient):
    first = client.post("/api/detect", files={"file": ("n1.png", make_crack_image(), "image/png")}).json()
    second = client.post("/api/detect", files={"file": ("n2.png", make_plain_image(), "image/png")}).json()
    # list is DESC by id, so second is first in list
    res = client.get(f"/api/records/{second['id']}/neighbors")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == second["id"]
    assert body["next_id"] == first["id"] or body["prev_id"] is not None


def test_export_json(client: TestClient):
    client.post("/api/detect", files={"file": ("ej.png", make_plain_image(), "image/png")})
    res = client.get("/api/export/json")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 1
    assert "records" in body
    assert "original_path" not in body["records"][0]


def test_health_includes_storage(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "storage" in body
    assert body["version"].startswith("2.")


def test_orphans_scan(client: TestClient):
    res = client.get("/api/maintenance/orphans")
    assert res.status_code == 200
    body = res.json()
    assert "orphan_count" in body
    assert "orphan_uploads" in body
