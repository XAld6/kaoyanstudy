from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

def make_crack_image() -> BytesIO:
    image = Image.new("RGB", (420, 260), "#d8d1c5")
    draw = ImageDraw.Draw(image)
    draw.line([(40, 40), (110, 92), (180, 88), (270, 150), (370, 210)], fill="#101010", width=4)
    draw.line([(210, 35), (230, 80), (224, 145)], fill="#303030", width=2)
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_health_endpoint_reports_service_ready(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert client.app.title == "智爪识损 OpenClaw Damage System"
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "openclaw-damage-system"


def test_cors_preflight_does_not_enable_credentials(client: TestClient):
    response = client.options(
        "/api/records",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers


def test_detection_creates_record_with_workflow_and_images(client: TestClient):
    image = make_crack_image()
    response = client.post(
        "/api/detect",
        files={"file": ("crack.png", image, "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["risk_level"] in {"低", "中", "高"}
    assert len(body["workflow"]) == 6
    assert body["workflow"][-1]["agent"] == "ReportArchiveAgent"
    assert all(step["status"] == "completed" for step in body["workflow"])
    assert body["annotated_url"].startswith("/outputs/")
    assert body["detections"]

    detail = client.get(f"/api/records/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]


def test_review_endpoint_updates_status_and_note(client: TestClient):
    image = make_crack_image()
    detected = client.post(
        "/api/detect",
        files={"file": ("review.png", image, "image/png")},
    ).json()

    response = client.post(
        f"/api/records/{detected['id']}/review",
        json={"status": "已复核", "risk_level": "中", "review_note": "现场复核为中风险，建议持续观察。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "已复核"
    assert body["risk_level"] == "中"
    assert "持续观察" in body["review_note"]


def test_review_endpoint_rejects_invalid_risk_level(client: TestClient):
    response = client.post(
        "/api/records/1/review",
        json={"status": "已复核", "risk_level": "严重", "review_note": ""},
    )

    assert response.status_code == 422


def test_review_endpoint_rejects_oversized_review_note(client: TestClient):
    response = client.post(
        "/api/records/1/review",
        json={"status": "已复核", "risk_level": "中", "review_note": "x" * 801},
    )

    assert response.status_code == 422


def test_report_endpoint_returns_pdf(client: TestClient):
    image = make_crack_image()
    detected = client.post(
        "/api/detect",
        files={"file": ("report.png", image, "image/png")},
    ).json()

    response = client.get(f"/api/records/{detected['id']}/report")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_rejects_non_image_uploads(client: TestClient):
    response = client.post(
        "/api/detect",
        files={"file": ("bad.txt", BytesIO(b"not image"), "text/plain")},
    )

    assert response.status_code == 400
    assert "图片" in response.json()["detail"]
