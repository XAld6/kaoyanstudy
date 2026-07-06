@echo off
cd /d "%~dp0"

set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%PS_EXE%" goto run_menu

set "PS_EXE=%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%PS_EXE%" goto run_menu

set "PS_EXE=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%PS_EXE%" goto run_menu

echo Windows PowerShell was not found.
echo Please check: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
pause
exit /b 1

:run_menu
"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0kaoyan-console.ps1"
pause