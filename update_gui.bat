@echo off
echo Starting EPC Update Manager GUI...
echo.

REM Try Python commands in order
if exist "update\update_manager_gui.py" (
    echo Launching GUI application...
    python update\update_manager_gui.py
    if %errorlevel% neq 0 (
        echo Trying with py command...
        py update\update_manager_gui.py
    )
) else (
    echo Error: update\update_manager_gui.py not found!
    pause
    exit /b 1
)

REM Exit normally
exit /b 0
