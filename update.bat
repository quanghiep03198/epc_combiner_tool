@echo off
echo Starting EPC Information Combiner Update Process...
echo.

REM Try update methods in order of preference
if exist "updater.exe" (
    echo Method 1: Running standalone updater...
    "updater.exe"
    goto :check_result
)

REM If standalone updater failed or doesn't exist, try Python
if exist "update.py" (
    echo Method 2: Running Python update script...
    python update.py
    if %errorlevel% neq 0 (
        echo Trying with py command...
        py update.py
    )
    goto :check_result
)

REM If Python failed or doesn't exist, use standalone batch updater
if exist "update_standalone.bat" (
    echo Method 3: Running standalone batch updater...
    call "update_standalone.bat"
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
    echo Update failed! Trying alternative method...
    if exist "update_standalone.bat" (
        echo Running fallback updater...
        call "update_standalone.bat"
    ) else (
        echo No fallback available. Please update manually.
        pause
    )
) else (
    echo.
    echo Update process completed!
    echo.
    timeout /t 3 /nobreak > nul
)