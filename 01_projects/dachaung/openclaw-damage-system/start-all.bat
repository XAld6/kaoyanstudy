@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [error] 未找到 python，请先安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)

if not exist "frontend\node_modules\" (
  echo [info] 首次运行，安装前端依赖...
  pushd frontend
  call npm.cmd install
  if errorlevel 1 (
    echo [error] npm install 失败
    popd
    pause
    exit /b 1
  )
  popd
)

echo [info] 启动后端 http://127.0.0.1:8000
start "openclaw-backend" cmd /k "cd /d \"%~dp0backend\" && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [info] 启动前端 http://127.0.0.1:5173
start "openclaw-frontend" cmd /k "cd /d \"%~dp0frontend\" && npm.cmd run dev"

echo.
echo 浏览器访问: http://127.0.0.1:5173
echo 演示样例目录: samples\
echo 批跑命令: python scripts\demo_run.py
echo 停止服务: stop-all.bat
echo 版本: 2.0.0
echo.
endlocal
