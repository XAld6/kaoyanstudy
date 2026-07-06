@echo off
setlocal
cd /d "%~dp0"

echo Starting Kaoyan Study Console...
echo.
echo Backend: http://127.0.0.1:8018
echo Frontend: http://127.0.0.1:5188
echo.

start "kaoyan-backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8018"
start "kaoyan-frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo Both windows were opened. Keep them running while using the app.
pause
