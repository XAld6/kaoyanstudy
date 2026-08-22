import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app import db, state

logger = logging.getLogger("kaoyan.api")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Kaoyan Study Console API", lifespan=lifespan)

# 生产环境同源反代（Caddy 同域下发静态文件 + 转发 /api），CORS 中间件完全多余；
# 仅开发模式（本机 vite dev 需跨端口直连调试）通过 KAOYAN_DEV_CORS=1 开启。
if os.getenv("KAOYAN_DEV_CORS") == "1":
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
    # base_url/model 默认 None：空值表示「沿用当前生效配置」（环境变量/本地文件），
    # 避免把 OpenAI 默认值误当用户显式输入（否则空请求体会拿着现 key 去测 api.openai.com）
    base_url: str | None = None
    model: str | None = None


class ConfigTestResponse(BaseModel):
    ok: bool
    message: str
    model: str
    base_url: str


class StateUpdate(BaseModel):
    """PUT /api/state 请求体。前端按 camelCase 发送（baseRevision/focusStats），
    这里用 model_validator 显式重命名，避免依赖 Field(alias) 在个别
    pydantic 版本上的歧义行为。"""

    base_revision: int
    data: state.AppDataModel
    focus_stats: state.FocusStatsModel | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_camel_case(cls, value: Any) -> Any:
        if isinstance(value, dict):
            if "baseRevision" in value and "base_revision" not in value:
                value["base_revision"] = value.pop("baseRevision")
            if "focusStats" in value and "focus_stats" not in value:
                value["focus_stats"] = value.pop("focusStats")
        return value


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/") or "https://api.openai.com/v1"
    for suffix in ("/chat/completions", "/responses"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip("/")
    return normalized


def load_local_config() -> dict[str, str]:
    """只读回退：仅 Windows 本机开发用 llm_config.local.json；
    服务器上该文件不存在，密钥一律走 /etc/kaoyan-console.env。"""
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


def _first_validation_msg(exc: ValidationError) -> str:
    try:
        first = exc.errors()[0]
        loc = ".".join(str(part) for part in first.get("loc", ()))
        return f"{loc} {first.get('msg', '')}".strip()
    except Exception:
        return str(exc)


def trim_advice_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """服务端裁剪：控制 token 成本；output_format 与 system prompt 重复，直接丢弃。"""
    trimmed = dict(payload)
    today_tasks = trimmed.get("today_tasks")
    if isinstance(today_tasks, list):
        trimmed["today_tasks"] = today_tasks[:20]
    review = trimmed.get("review")
    if isinstance(review, str):
        trimmed["review"] = review[:500]
    trimmed.pop("output_format", None)
    return trimmed


@app.get("/api/health")
def health() -> dict[str, Any]:
    result = public_config(get_llm_config())
    try:
        with db.connect() as conn:
            full = state.read_full_state(conn)
        result["db_ok"] = True
        result["revision"] = full["revision"]
        result["task_count"] = len(full["data"]["tasks"]) if full["data"] else 0
    except Exception:
        result["db_ok"] = False
        result["revision"] = -1
        result["task_count"] = -1
    return result


@app.get("/api/config")
def read_config() -> dict[str, Any]:
    return public_config(get_llm_config())


@app.post("/api/config")
def save_config(_config: LlmConfigUpdate) -> dict[str, Any]:
    raise HTTPException(
        status_code=403,
        detail="服务器上的 API Key 只能通过 /etc/kaoyan-console.env 配置，网页不可修改。",
    )


def resolve_runtime_config(config: LlmConfigUpdate | None, existing: dict[str, str]) -> dict[str, str]:
    """决定 /api/config/test 实际使用的连接参数。

    - api_key 永远取当前生效配置（环境变量/本地文件），忽略请求体；
    - base_url/model 仅在请求体提供了非空值时覆盖，空值/缺省沿用当前配置。
    """
    return {
        "api_key": existing["api_key"],
        "base_url": normalize_base_url(config.base_url) if config and (config.base_url or "").strip() else existing["base_url"],
        "model": (config.model or "").strip() if config and (config.model or "").strip() else existing["model"],
    }


@app.post("/api/config/test", response_model=ConfigTestResponse)
async def test_config(config: LlmConfigUpdate | None = None) -> ConfigTestResponse:
    existing = get_llm_config()
    # 服务器上 Key 只能来自环境变量/本机文件；请求体里的 api_key 一律忽略
    runtime = resolve_runtime_config(config, existing)
    if not runtime["api_key"]:
        raise HTTPException(status_code=503, detail="请先配置 API Key（服务器上写入 /etc/kaoyan-console.env），再测试连接。")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)) as client:
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
                "你是一个考研学习教练。请基于用户最近 7 天任务、今日复盘和本地结构化建议，"
                "给出简短、具体、可执行的中文建议。不要鸡汤，不要编造不存在的数据。\n"
                "必须严格使用以下三个小节标题，每节 1-3 条，每条一行：\n"
                "【补哪科】\n"
                "【砍哪块】\n"
                "【明日三件事】\n"
                "不要输出其他大段说明。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"日期：{request.date}\n"
                f"学习数据：{json.dumps(trim_advice_payload(request.payload), ensure_ascii=False)}"
            ),
        },
    ]

    # 推理模型偶发「正文为空」（推理 token 吃光预算）：仅此类情况自动重试一次；
    # 网络错误与其他格式错误直接返回，不重复消费额度。
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)) as client:
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
                        # 推理模型（如 DeepSeek v4 系列）的 reasoning 也计入 max_tokens；
                        # 400 常被推理吃光导致正文为空，放宽到 1000 保证三段式正文能产出
                        "max_tokens": 1000,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=provider_error_message(exc)) from exc

        body = response.json()
        usage = body.get("usage") if isinstance(body, dict) else None
        if isinstance(usage, dict):
            logger.info("AI advice usage model=%s %s", config["model"], json.dumps(usage, ensure_ascii=False))

        try:
            lines = extract_advice_lines(body)
        except ValueError as exc:
            message_content = (body.get("choices") or [{}])[0].get("message", {}).get("content")
            empty_content = isinstance(message_content, str) and not message_content.strip()
            if attempt == 0 and empty_content:
                logger.info("AI advice empty content, retrying (attempt 2)")
                continue
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return AdviceResponse(advice=lines, source="llm")

    raise HTTPException(status_code=502, detail="AI 模型连续两次未返回可用内容，请稍后重试。")


# ---------- 状态读写（同步 def：FastAPI 丢进线程池，不阻塞事件循环） ----------


@app.get("/api/state")
def read_state() -> dict[str, Any]:
    with db.connect() as conn:
        return state.read_full_state(conn)


@app.put("/api/state")
def update_state(update: StateUpdate) -> dict[str, Any]:
    with db.connect() as conn:
        current = state.read_full_state(conn)
        if current["revision"] != update.base_revision:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "数据已被其他设备更新，请选择「加载服务器版本」或「用本机版本覆盖」。",
                    "server": current,
                },
            )
        state.write_state(conn, update.data, update.focus_stats)
        return state.read_full_state(conn)


@app.post("/api/state/import")
def import_state(body: dict[str, Any]) -> dict[str, Any]:
    """兼容两种输入：
    1) {data, focusStats?, mode}（前端新格式）
    2) 裸 AppData / {...AppData, focusStats}（老备份文件，等价 replace）
    """
    mode = body.get("mode", "replace")
    if mode not in ("replace", "merge"):
        raise HTTPException(status_code=422, detail="mode 只能是 replace 或 merge。")

    data_raw = body.get("data") if isinstance(body.get("data"), dict) else body
    stats_raw = body.get("focusStats")
    try:
        data = state.AppDataModel.model_validate(data_raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"学习数据格式不合法：{_first_validation_msg(exc)}") from exc
    focus_stats = None
    if isinstance(stats_raw, dict):
        try:
            focus_stats = state.FocusStatsModel.model_validate(stats_raw)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=f"专注统计格式不合法：{_first_validation_msg(exc)}") from exc

    # 写入前自动落一份数据库快照，对应前端「导入前自动导出」行为
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    db.backup_db_to(db.BACKUP_DIR / f"pre-import-{ts}.db")

    with db.connect() as conn:
        if mode == "replace":
            state.write_state(conn, data, focus_stats)
        else:
            state.merge_state(conn, data, focus_stats)
        return state.read_full_state(conn)


@app.get("/api/state/export")
def export_state() -> JSONResponse:
    with db.connect() as conn:
        full = state.read_full_state(conn)
    if full["data"] is None:
        raise HTTPException(status_code=404, detail="服务器上还没有学习数据。")
    payload = {**full["data"], "focusStats": full["focusStats"]}
    filename = f"kaoyan-study-server-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )