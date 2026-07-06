"""FastAPI 应用入口与路由定义。"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, seed_demo_tasks, to_web_path
from app.services import (
    latest_records,
    latest_tasks,
    latest_work_orders,
    process_sample,
    process_upload,
    process_uploads,
    risk_stats,
    sample_images,
    settings,
    update_work_order_status,
)
from models.detector import WallDefectDetector
from models.risk import RISK_LABELS
from utils.config import ensure_project_dirs, project_path
from utils.sample_generator import generate_samples

# ── 初始化 ──────────────────────────────────────────────────────────
ensure_project_dirs()
init_db()
seed_demo_tasks()

sample_dir = project_path(settings["paths"]["samples_dir"])
if not any(sample_dir.glob("*.jpg")):
    generate_samples(count=8)

app = FastAPI(title=settings["project"]["name"], version=settings["project"]["version"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get("server", {}).get("cors_origins", ["*"]),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=project_path("static")), name="static")
app.mount("/uploads", StaticFiles(directory=project_path(settings["paths"]["uploads_dir"])), name="uploads")
app.mount("/results", StaticFiles(directory=project_path(settings["paths"]["results_dir"])), name="results")
app.mount("/samples", StaticFiles(directory=project_path(settings["paths"]["samples_dir"])), name="samples")
templates = Jinja2Templates(directory=project_path("templates"))
detector = WallDefectDetector(settings)


# ── 异常处理 ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(request, "404.html", status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse(request, "500.html", status_code=500)


# ── Web 页面路由 ────────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": detector.engine}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "project": settings["project"],
            "records": latest_records(limit=6),
            "stats": risk_stats(),
            "samples": sample_images(),
            "risk_labels": RISK_LABELS,
            "engine": detector.engine,
        },
    )


@app.get("/records", response_class=HTMLResponse)
def records_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "records.html",
        {"records": latest_records(limit=100), "risk_labels": RISK_LABELS},
    )


@app.post("/detect", response_class=HTMLResponse)
async def detect_page(request: Request, file: UploadFile = File(...)) -> HTMLResponse:
    record = await process_upload(file, detector)
    return templates.TemplateResponse(
        request, "result.html", {"record": record, "risk_labels": RISK_LABELS}
    )


@app.post("/detect-batch", response_class=HTMLResponse)
async def detect_batch_page(request: Request, files: list[UploadFile] = File(...)) -> HTMLResponse:
    records = await process_uploads(files, detector)
    return templates.TemplateResponse(
        request, "batch_result.html", {"records": records}
    )


@app.post("/detect-sample", response_class=HTMLResponse)
def detect_sample_page(request: Request, sample: str = Form(...)) -> HTMLResponse:
    record = process_sample(sample, detector)
    return templates.TemplateResponse(
        request, "result.html", {"record": record, "risk_labels": RISK_LABELS}
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "tasks.html", {"tasks": latest_tasks()})


@app.get("/work-orders", response_class=HTMLResponse)
def work_orders_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "work_orders.html",
        {"orders": latest_work_orders(), "risk_labels": RISK_LABELS},
    )


@app.post("/work-orders/{order_id}/status")
def update_order_status(order_id: int, status: str = Form(...)) -> RedirectResponse:
    update_work_order_status(order_id, status)
    return RedirectResponse(url="/work-orders", status_code=303)


@app.post("/generate-samples")
def generate_samples_page() -> RedirectResponse:
    generate_samples(count=8)
    return RedirectResponse(url="/", status_code=303)


# ── API 路由 ────────────────────────────────────────────────────────
@app.post("/api/detect")
async def api_detect(file: UploadFile = File(...)) -> dict:
    return {"record": await process_upload(file, detector)}


@app.post("/api/detect-batch")
async def api_detect_batch(files: list[UploadFile] = File(...)) -> dict:
    return {"records": await process_uploads(files, detector)}


@app.post("/api/detect-sample")
def api_detect_sample(sample: str = Form(...)) -> dict:
    return {"record": process_sample(sample, detector)}


@app.get("/api/records")
def api_records() -> dict:
    return {"records": latest_records(limit=100)}


@app.get("/api/tasks")
def api_tasks() -> dict:
    return {"tasks": latest_tasks()}


@app.get("/api/work-orders")
def api_work_orders() -> dict:
    return {"orders": latest_work_orders()}


@app.post("/api/generate-samples")
def api_generate_samples(count: int = 8) -> dict:
    paths = generate_samples(count=count)
    return {"samples": [to_web_path(path) for path in paths]}
