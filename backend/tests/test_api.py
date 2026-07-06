from fastapi.testclient import TestClient
from app.main import app, extract_advice_lines, normalize_base_url


client = TestClient(app)


def test_health_reports_llm_configuration_state():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "llm_configured" in response.json()


def test_advice_returns_clear_error_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/api/advice", json={"date": "2026-06-03", "payload": {"tasks": []}})

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_config_endpoint_accepts_openai_compatible_settings(monkeypatch, tmp_path):
    config_path = tmp_path / "test_llm_config.local.json"
    monkeypatch.setattr("app.main.CONFIG_PATH", config_path)

    response = client.post(
        "/api/config",
        json={
            "api_key": "sk-local-test",
            "base_url": "https://api.example.com/v1",
            "model": "gpt-test",
        },
    )

    assert response.status_code == 200
    assert response.json()["llm_configured"] is True
    assert response.json()["base_url"] == "https://api.example.com/v1"
    assert response.json()["model"] == "gpt-test"
    assert "api_key" not in response.json()


def test_normalize_base_url_accepts_full_chat_completions_url():
    assert normalize_base_url("https://api.example.com/v1/chat/completions") == "https://api.example.com/v1"
    assert normalize_base_url("https://api.example.com/v1/") == "https://api.example.com/v1"


def test_config_endpoint_keeps_existing_key_when_key_input_is_blank(monkeypatch, tmp_path):
    config_path = tmp_path / "test_llm_config.local.json"
    config_path.write_text(
        '{"api_key":"sk-existing","base_url":"https://api.old.example/v1","model":"old-model"}',
        encoding="utf-8",
    )
    monkeypatch.setattr("app.main.CONFIG_PATH", config_path)

    response = client.post(
        "/api/config",
        json={
            "api_key": "",
            "base_url": "https://api.new.example/v1",
            "model": "new-model",
        },
    )

    assert response.status_code == 200
    assert response.json()["llm_configured"] is True
    assert response.json()["base_url"] == "https://api.new.example/v1"
    assert response.json()["model"] == "new-model"
    assert "sk-existing" in config_path.read_text(encoding="utf-8")


def test_config_test_returns_clear_error_without_api_key(monkeypatch, tmp_path):
    config_path = tmp_path / "test_llm_config.local.json"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("app.main.CONFIG_PATH", config_path)

    response = client.post("/api/config/test", json={"api_key": "", "base_url": "https://api.example.com/v1", "model": "gpt-test"})

    assert response.status_code == 503
    assert "API Key" in response.json()["detail"]


def test_extract_advice_lines_rejects_unexpected_provider_response():
    try:
        extract_advice_lines({"error": "bad gateway"})
    except ValueError as exc:
        assert "choices" in str(exc)
    else:
        raise AssertionError("expected invalid provider response to raise ValueError")
