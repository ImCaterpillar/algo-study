@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0..\"
set "REGISTRY=%~1"
if "%REGISTRY%"=="" set "REGISTRY=https://registry.npmjs.org/"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix-npm-registry.ps1" -Registry "%REGISTRY%"
exit /b %ERRORLEVEL%
