@echo off
title EPC Information Combiner - Isolated Python Startup

echo 🚀 Starting EPC Information Combiner with Complete Python Isolation
echo =====================================================================

:: Clear ALL Python-related environment variables
set PYTHONPATH=
set PYTHONHOME=
set PYTHON313_DLL=
set PYTHON3_DLL=
set PYTHON_DLL_PATH=
set PYTHONSTARTUP=
set PYTHONEXECUTABLE=

:: Set strict isolation
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

:: Save original PATH
set ORIGINAL_PATH=%PATH%

:: Create completely isolated PATH without ANY Python directories
set ISOLATED_PATH=
for %%P in ("%PATH:;=" "%") do (
    echo %%~P | findstr /i /c:"python" /c:"conda" /c:"anaconda" /c:"miniconda" >nul || (
        if defined ISOLATED_PATH (
            set "ISOLATED_PATH=!ISOLATED_PATH!;%%~P"
        ) else (
            set "ISOLATED_PATH=%%~P"
        )
    )
)

:: Set the isolated PATH
set PATH=%ISOLATED_PATH%

:: Add only Windows system directories to ensure basic functionality
set PATH=%PATH%;%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem

echo 🧹 Environment cleaned - Python isolation active
echo 📍 Current directory: %~dp0
echo 🎯 Starting application...

:: Start the application in isolated environment
cd /d "%~dp0"
start "" /wait "EPC Information Combiner.exe"

set EXIT_CODE=%ERRORLEVEL%

:: Restore original PATH
set PATH=%ORIGINAL_PATH%

if %EXIT_CODE% EQU 0 (
    echo ✅ Application exited successfully
) else (
    echo ❌ Application exited with error code: %EXIT_CODE%
    echo 💡 If you see DLL conflicts, try running as administrator
    pause
)

exit /b %EXIT_CODE%