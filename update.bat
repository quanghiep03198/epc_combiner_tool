@echo off
echo Starting EPC Information Combiner Update Process...
echo.

REM Run the update script
echo Running update script...
python update.py

REM Check if update script ran successfully
if %errorlevel% neq 0 (
    echo Trying with py command...
    py update.py
)

REM Final status check
if %errorlevel% neq 0 (
    echo.
    echo ❌ Update failed! Please update manually.
    echo.
    pause
) else (
    echo.
    echo ✅ Update process completed!
    echo The installer should have started automatically.
    echo.
    timeout /t 3 /nobreak > nul
)