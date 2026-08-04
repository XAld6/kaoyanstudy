@echo off
setlocal
echo [info] 尝试结束智爪识损相关进程...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  echo [info] 结束后端 PID %%p
  taskkill /PID %%p /F >nul 2>nul
)

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  echo [info] 结束前端 PID %%p
  taskkill /PID %%p /F >nul 2>nul
)

echo [info] 完成。若窗口仍在，可手动关闭 openclaw-backend / openclaw-frontend 终端。
endlocal
