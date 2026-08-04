@echo off
cd /d "%~dp0frontend"

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [error] 未找到 npm，请先安装 Node.js。
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo [info] 安装前端依赖...
  call npm.cmd install
  if errorlevel 1 (
    echo [error] npm install 失败
    pause
    exit /b 1
  )
)

npm.cmd run dev
