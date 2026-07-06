import os
import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kaoyan Study Console API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5188", "http://localhost:5188"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "llm_config.local.json"


class AdviceRequest(BaseModel):
    date: str
    payload: dict[str, Any]


class AdviceResponse(BaseModel):
    advice: list[str]
    source: str


class LlmConfigUpdate(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"


class ConfigTestResponse(BaseModel):
    ok: bool
    message: str
    model: str
    base_url: str


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/") or "https://api.openai.com/v1"
    for suffix in ("/chat/completions", "/responses"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip("/")
    return normalized


def load_local_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: str(value) for key, value in data.items() if value}


def public_config(config: dict[str, str]) -> dict[str, Any]:
    return {
        "status": "ok",
        "llm_configured": bool(config["api_key"]),
        "model": config["model"],
        "base_url": config["base_url"],
    }


def get_llm_config() -> dict[str, str]:
    local = load_local_config()
    return {
        "api_key": os.getenv("OPENAI_API_KEY") or local.get("api_key", ""),
        "base_url": normalize_base_url(os.getenv("OPENAI_BASE_URL") or local.get("base_url", "https://api.openai.com/v1")),
        "model": os.getenv("OPENAI_MODEL") or local.get("model", "gpt-4.1-mini"),
    }


def provider_error_message(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.ConnectError):
        return "连接不到 API 服务。请检查 Base URL 是否能在本机访问，常见格式是 https://api.openai.com/v1 或你的中转服务 /v1 地址。"
    if isinstance(exc, httpx.TimeoutException):
        return "API 服务响应超时。请稍后重试，或检查代理/网络。"
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        detail = exc.response.text[:300].strip()
        if status_code in {401, 403}:
            return f"API Key 被服务拒绝，状态码 {status_code}。请检查 Key、Base URL 和账号权限。{detail}"
        if status_code == 404:
            return f"接口地址不存在，状态码 404。Base URL 通常要填到 /v1，不要填完整的 /chat/completions。{detail}"
        if status_code == 429:
            return f"请求被限流或额度不足，状态码 429。{detail}"
        return f"API 服务返回错误，状态码 {status_code}。{detail}"
    return f"API 连接测试失败：{exc}"


def extract_advice_lines(body: Any) -> list[str]:
    if not isinstance(body, dict):
        raise ValueError("API 服务响应格式不符合 OpenAI Chat Completions。")

    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("API 服务响应里没有 choices 字段。")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("API 服务响应里的 choices 格式不正确。")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("API 服务响应里没有 message 字段。")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("API 服务没有返回可用建议内容。")

    lines = [
        line.strip(" -0123456789.、")
        for line in content.splitlines()
        if line.strip(" -0123456789.、")
    ]
    return (lines or [content.strip()])[:5]


@app.get("/api/health")
def health() -> dict[str, Any]:
    return public_config(get_llm_config())


@app.get("/api/config")
def read_config() -> dict[str, Any]:
    return public_config(get_llm_config())


@app.post("/api/config")
def save_config(config: LlmConfigUpdate) -> dict[str, Any]:
    existing = load_local_config()
    payload = {
        "api_key": config.api_key.strip() or existing.get("api_key", ""),
        "base_url": normalize_base_url(config.base_url),
        "model": config.model.strip() or "gpt-4.1-mini",
    }
    try:
        CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"API 配置保存失败：{exc}") from exc
    return public_config(get_llm_config())


@app.post("/api/config/test", response_model=ConfigTestResponse)
async def test_config(config: LlmConfigUpdate | None = None) -> ConfigTestResponse:
    existing = get_llm_config()
    runtime = {
        "api_key": config.api_key.strip() if config and config.api_key.strip() else existing["api_key"],
        "base_url": normalize_base_url(config.base_url) if config and config.base_url.strip() else existing["base_url"],
        "model": config.model.strip() if config and config.model.strip() else existing["model"],
    }
    if not runtime["api_key"]:
        raise HTTPException(status_code=503, detail="请先填写并保存 API Key，再测试连接。")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{runtime['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {runtime['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": runtime["model"],
                    "messages": [{"role": "user", "content": "请只回复 OK，用于连接测试。"}],
                    "temperature": 0,
                    "max_tokens": 8,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=provider_error_message(exc)) from exc

    return ConfigTestResponse(
        ok=True,
        message="API 连接成功，模型已返回响应。",
        model=runtime["model"],
        base_url=runtime["base_url"],
    )


@app.post("/api/advice", response_model=AdviceResponse)
async def advice(request: AdviceRequest) -> AdviceResponse:
    config = get_llm_config()
    if not config["api_key"]:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on the local backend.")

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个考研学习教练。请基于用户最近 7 天任务、今日复盘和本地规则建议，"
                "输出 3-5 条简短、具体、可执行的中文建议。不要鸡汤，不要编造不存在的数据。"
            ),
        },
        {
            "role": "user",
            "content": f"日期：{request.date}\n学习数据：{request.payload}",
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config["model"],
                    "messages": messages,
                    "temperature": 0.4,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=provider_error_message(exc)) from exc

    try:
        lines = extract_advice_lines(response.json())
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AdviceResponse(advice=lines, source="llm")
