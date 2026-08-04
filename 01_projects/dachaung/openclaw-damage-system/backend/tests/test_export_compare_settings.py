from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.runtime_settings import reset_settings


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
        draw.point((i + 3, (i * 5) % 260), fill="#ddd6ca")
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_settings_get_put_reset(client: TestClient):
    reset_settings()
    got = client.get("/api/settings")
    assert got.status_code == 200
    body = got.json()
    assert "settings" in body
    assert "schema" in body
    assert body["settings"]["sensitivity"] == 0.55

    updated = client.put("/api/settings", json={"sensitivity": 0.8, "max_detections": 10})
    assert updated.status_code == 200
    settings = updated.json()["settings"]
    assert settings["sensitivity"] == 0.8
    assert settings["max_detections"] == 10

    # clamp out-of-range
    clamped = client.put("/api/settings", json={"sensitivity": 0.05, "min_confidence": 0.99})
    assert clamped.status_code == 200
    assert clamped.json()["settings"]["sensitivity"] == 0.2
    assert clamped.json()["settings"]["min_confidence"] == 0.95

    reset = client.post("/api/settings/reset")
    assert reset.status_code == 200
    assert reset.json()["settings"]["sensitivity"] == 0.55


def test_export_csv_and_pdf_zip(client: TestClient):
    client.post("/api/detect", files={"file": ("export-a.png", make_crack_image(), "image/png")})
    client.post("/api/detect", files={"file": ("export-b.png", make_plain_image(), "image/png")})

    csv_res = client.get("/api/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    text = csv_res.content.decode("utf-8-sig")
    assert "filename" in text
    assert "export-a.png" in text or "export-b.png" in text

    zip_res = client.get("/api/export/pdf-zip", params={"limit": 10})
    assert zip_res.status_code == 200
    assert "application/zip" in zip_res.headers.get("content-type", "")
    with ZipFile(BytesIO(zip_res.content)) as zf:
        names = zf.namelist()
        assert names
        assert any(name.endswith(".pdf") for name in names)


def test_compare_records(client: TestClient):
    left = client.post(
        "/api/detect",
        files={"file": ("cmp-left.png", make_crack_image(), "image/png")},
    ).json()
    right = client.post(
        "/api/detect",
        files={"file": ("cmp-right.png", make_plain_image(), "image/png")},
    ).json()

    res = client.get("/api/compare", params={"left_id": left["id"], "right_id": right["id"]})
    assert res.status_code == 200
    body = res.json()
    assert body["left"]["id"] == left["id"]
    assert body["right"]["id"] == right["id"]
    assert "delta" in body
    assert "notes" in body
    assert isinstance(body["notes"], list)

    post = client.post("/api/compare", json={"left_id": left["id"], "right_id": right["id"]})
    assert post.status_code == 200
    assert post.json()["left"]["id"] == left["id"]


def test_system_lists_new_capabilities(client: TestClient):
    res = client.get("/api/system")
    assert res.status_code == 200
    caps = res.json()["capabilities"]
    assert caps["export_csv"] is True
    assert caps["export_pdf_zip"] is True
    assert caps["record_compare"] is True
    assert caps["runtime_settings"] is True
    assert caps["redetect"] is True
    assert caps["batch_delete"] is True


def test_settings_persist_to_disk(client: TestClient, tmp_path, monkeypatch):
    from pathlib import Path

    path = Path(tmp_path / "data" / "runtime_settings.json")
    client.put("/api/settings", json={"sensitivity": 0.75})
    assert path.exists()
    raw = path.read_text(encoding="utf-8")
    assert "0.75" in raw


def test_redetect_and_batch_delete(client: TestClient):
    created = client.post(
        "/api/detect",
        files={"file": ("recheck.png", make_crack_image(), "image/png")},
    ).json()
    record_id = created["id"]

    again = client.post(f"/api/records/{record_id}/redetect")
    assert again.status_code == 200
    body = again.json()
    assert body["id"] == record_id
    assert "risk_level" in body
    assert body["annotated_url"]

    other = client.post(
        "/api/detect",
        files={"file": ("batch-del.png", make_plain_image(), "image/png")},
    ).json()

    deleted = client.post("/api/records/batch-delete", json={"ids": [record_id, other["id"]]})
    assert deleted.status_code == 200
    assert deleted.json()["deleted_count"] == 2
    assert client.get(f"/api/records/{record_id}").status_code == 404


def test_batch_review(client: TestClient):
    a = client.post(
        "/api/detect",
        files={"file": ("rev-a.png", make_crack_image(), "image/png")},
    ).json()
    b = client.post(
        "/api/detect",
        files={"file": ("rev-b.png", make_plain_image(), "image/png")},
    ).json()

    res = client.post(
        "/api/records/batch-review",
        json={
            "ids": [a["id"], b["id"]],
            "status": "已复核",
            "review_note": "批量通过",
            "keep_risk": True,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["updated_count"] == 2

    for rid in (a["id"], b["id"]):
        detail = client.get(f"/api/records/{rid}").json()
        assert detail["review_status"] == "已复核"
        assert "批量通过" in (detail.get("review_note") or "")


def test_export_by_ids(client: TestClient):
    a = client.post(
        "/api/detect",
        files={"file": ("id-a.png", make_crack_image(), "image/png")},
    ).json()
    b = client.post(
        "/api/detect",
        files={"file": ("id-b.png", make_plain_image(), "image/png")},
    ).json()

    res = client.get("/api/export/csv", params={"ids": f"{a['id']}"})
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    assert "id-a.png" in text
    assert "id-b.png" not in text

    # ensure b still exists and export can take multiple
    multi = client.get("/api/export/csv", params={"ids": f"{a['id']},{b['id']}"})
    assert multi.status_code == 200
    multi_text = multi.content.decode("utf-8-sig")
    assert "id-a.png" in multi_text and "id-b.png" in multi_text
