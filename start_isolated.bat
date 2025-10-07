@echo off
echo Starting EPC Information Combiner with DLL isolation...

:: Clear Python environment variables
set PYTHONPATH=
set PYTHONHOME=
set PYTHON313_DLL=

:: Set isolated environment
set PYTHONPATH=%~dp0
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8

:: Remove system Python from PATH temporarily
set ORIGINAL_PATH=%PATH%
set PATH=%PATH:C:\Python313\Scripts;=%
set PATH=%PATH:C:\Python313\;=%

:: Start application
echo 🚀 Starting application with isolated environment...
start "" "%~dp0EPC Information Combiner.exe"

:: Wait a moment then restore PATH
timeout /t 3 /nobreak >nul
set PATH=%ORIGINAL_PATH%

echo ✅ Application started successfully
pause