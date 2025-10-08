@echo off
echo Starting EPC Information Combiner Update Process...
echo.

REM Try update methods in order of preference
if exist "updater.exe" (
    echo Method 1: Running standalone updater...
    "updater.exe" --install-dir "." --current-version "1.0.0" --force
    goto :check_result
)

REM If standalone updater doesn't exist, try Python
if exist "update\update_manager.py" (
    echo Method 2: Running Python update script with auto-detection...
    python update\update_manager.py --install-dir "." --current-version "1.0.0" --force
    if %errorlevel% neq 0 (
        echo Trying with py command...
        py update\update_manager.py --install-dir "." --current-version "1.0.0" --force
    )
    goto :check_result
)

REM All methods failed
echo All update methods failed!
echo Please download the latest version manually from GitHub.
pause
exit /b 1

:check_result
REM Final status check
if %errorlevel% neq 0 (
    echo.
    echo Update failed! Please check the logs or try manual download.
    pause
) else (
    echo.
    echo Update process completed successfully!
    echo.
    timeout /t 3 /nobreak > nul
)