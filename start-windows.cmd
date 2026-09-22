@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
cd /d "%ROOT%" || (
  echo [algo-study] Cannot enter project directory: %ROOT%
  pause
  exit /b 1
)

set "REGISTRY=%~1"
if "%REGISTRY%"=="" set "REGISTRY=https://registry.npmmirror.com/"

if not exist "%ROOT%scripts\deploy-local.ps1" (
  echo [algo-study] scripts\deploy-local.ps1 not found. Please run this file from the full project directory.
  pause
  exit /b 1
)

echo [algo-study] Starting AlgoStudy
echo [algo-study] Project directory: %ROOT%
echo [algo-study] npm registry: %REGISTRY%
echo.

echo [algo-study] Fixing npm registry settings ...
call "%ROOT%scripts\fix-npm-registry.cmd" "%REGISTRY%"
if errorlevel 1 (
  echo.
  echo [algo-study] Failed to fix npm registry. Please check Node.js/npm installation.
  pause
  exit /b 1
)

echo.
echo [algo-study] Starting backend and frontend. First run may take several minutes to install dependencies.
echo [algo-study] Browser will open automatically: http://127.0.0.1:5173
echo [algo-study] Press Ctrl+C to stop services.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\deploy-local.ps1" -NpmRegistry "%REGISTRY%" -OpenBrowser
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
  echo [algo-study] Startup failed. Exit code: %EXIT_CODE%
  echo [algo-study] Common causes: Python/Node.js not installed, port 8000/5173 occupied, or npm registry unreachable.
) else (
  echo [algo-study] Services stopped.
)
pause
exit /b %EXIT_CODE%
