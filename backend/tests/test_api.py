from pathlib import Path

import app.main as app_main_module
from fastapi.testclient import TestClient
from app.main import (
    LlmConfigUpdate,
    app,
    extract_advice_lines,
    normalize_base_url,
    resolve_runtime_config,
)


client = TestClient(app)


def test_health_reports_llm_configuration_state():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "llm_configured" in response.json()
    # 扩展（L3）：数据库健康与状态
    assert response.json()["db_ok"] is True
    assert response.json()["revision"] == 0
    assert response.json()["task_count"] == 0


def test_advice_returns_clear_error_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/api/advice", json={"date": "2026-06-03", "payload": {"tasks": []}})

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_config_write_is_forbidden_on_server(monkeypatch, tmp_path):
    """H7：服务器上 API Key 只能通过 /etc/kaoyan-console.env 配置，网页写 Key 必须 403。"""
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

    assert response.status_code == 403
    assert "/etc/kaoyan-console.env" in response.json()["detail"]


def test_normalize_base_url_accepts_full_chat_completions_url():
    assert normalize_base_url("https://api.example.com/v1/chat/completions") == "https://api.example.com/v1"
    assert normalize_base_url("https://api.example.com/v1/") == "https://api.example.com/v1"


def test_config_write_forbidden_also_when_key_input_is_blank(monkeypatch, tmp_path):
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

    assert response.status_code == 403
    assert "/etc/kaoyan-console.env" in response.json()["detail"]


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


def test_resolve_runtime_config_uses_current_config_when_body_is_empty():
    existing = {
        "api_key": "sk-env-key",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash-vision-exp",
    }
    # 空请求体（全默认 None）→ 必须沿用当前生效配置，绝不落到 OpenAI 默认
    runtime = resolve_runtime_config(LlmConfigUpdate(), existing)
    assert runtime == existing


def test_resolve_runtime_config_none_body_uses_current_config():
    existing = {"api_key": "sk-env-key", "base_url": "https://x.example/v1", "model": "m1"}
    assert resolve_runtime_config(None, existing) == existing


def test_resolve_runtime_config_explicit_values_do_not_override():
    """P0-4/SSRF：显式提供的 base_url / model 也一律不覆盖生效配置——
    测试连接不可能把生产 Key 发给请求方可控地址。"""
    existing = {"api_key": "sk-env-key", "base_url": "https://x.example/v1", "model": "m1"}
    runtime = resolve_runtime_config(
        LlmConfigUpdate(base_url="https://attacker.example/v1", model="evil-model"),
        existing,
    )
    assert runtime == existing


def test_resolve_runtime_config_blank_values_fall_back():
    existing = {"api_key": "sk-env-key", "base_url": "https://x.example/v1", "model": "m1"}
    runtime = resolve_runtime_config(LlmConfigUpdate(base_url="", model="  "), existing)
    assert runtime == existing


def test_no_server_side_today_defaults_in_source():
    """防回归（M5）：日期语义必须由客户端决定，后端禁止出现 date.today 类默认值。"""
    source = Path(app_main_module.__file__).read_text(encoding="utf-8")
    assert "date.today" not in source
    assert "datetime.now().date()" not in source


def test_config_test_only_uses_active_config_not_body_url(monkeypatch):
    """P0-4/SSRF：测试连接只允许请求「当前生效配置」；
    body 里传的 base_url / api_key 必须被忽略——防止把生产 Key 发给任意地址。"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-active-env")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-active")

    captured: dict[str, str] = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, url, **_kwargs):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeClient)

    response = client.post(
        "/api/config/test",
        json={
            "api_key": "sk-from-body",
            "base_url": "https://attacker.example/v1",
            "model": "evil-model",
        },
    )

    assert response.status_code == 200
    assert captured["url"] == "https://api.example.com/v1/chat/completions", (
        f"测试请求必须发往生效配置地址，实际 {captured['url']}"
    )


def test_health_returns_503_when_database_fails(monkeypatch):
    """P2-13：数据库故障时健康检查必须返回 503，部署脚本的 curl -f 才能真实感知。"""

    def boom(*_args, **_kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.main.db.connect", boom)

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["db_ok"] is False