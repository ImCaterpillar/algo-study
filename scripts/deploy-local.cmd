@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "REGISTRY=%~1"
if "%REGISTRY%"=="" set "REGISTRY=https://registry.npmmirror.com/"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy-local.ps1" -NpmRegistry "%REGISTRY%" -OpenBrowser
exit /b %ERRORLEVEL%
