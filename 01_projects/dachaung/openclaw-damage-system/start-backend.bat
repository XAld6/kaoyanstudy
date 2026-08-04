@echo off
cd /d "%~dp0backend"

where python >nul 2>nul
if errorlevel 1 (
  echo [error] 未找到 python，请先安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
