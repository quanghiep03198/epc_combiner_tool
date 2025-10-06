@echo off
setlocal enabledelayedexpansion

echo EPC Information Combiner Update Tool
echo =====================================
echo.

REM Get current directory
set "CURRENT_DIR=%~dp0"
set "UPDATE_DIR=%CURRENT_DIR%update_temp"
set "BACKUP_DIR=%CURRENT_DIR%backup_update"

REM Check for Python first, then use embedded solution
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python, using Python updater...
    if exist "update.py" (
        python "update.py"
        exit /b %errorlevel%
    ) else (
        echo update.py not found!
        goto :use_embedded
    )
) else (
    echo Python not found, using embedded updater...
    goto :use_embedded
)

:use_embedded
REM Use built-in Windows tools for basic update functionality
echo Checking for updates using embedded tools...

REM Download latest release info using PowerShell (available on Windows 7+)
powershell -Command "try { $response = Invoke-WebRequest -Uri 'https://api.github.com/repos/quanghiep03198/epc_combiner_tool/releases/latest' -UseBasicParsing; $release = $response.Content | ConvertFrom-Json; $version = $release.tag_name; $assets = $release.assets; foreach($asset in $assets) { if($asset.name -like '*windows-x64.zip*') { $downloadUrl = $asset.browser_download_url; break; } }; Write-Output \"VERSION:$version\"; Write-Output \"DOWNLOAD:$downloadUrl\"; } catch { Write-Output \"ERROR:Failed to check for updates\"; }" > update_info.tmp

REM Parse the response
set "UPDATE_VERSION="
set "DOWNLOAD_URL="
for /f "tokens=1,2 delims=:" %%a in (update_info.tmp) do (
    if "%%a"=="VERSION" set "UPDATE_VERSION=%%b"
    if "%%a"=="DOWNLOAD" set "DOWNLOAD_URL=%%b"
    if "%%a"=="ERROR" (
        echo %%b
        del update_info.tmp
        pause
        exit /b 1
    )
)
del update_info.tmp

if "%UPDATE_VERSION%"=="" (
    echo Failed to get version information
    pause
    exit /b 1
)

echo Latest version: %UPDATE_VERSION%

REM Simple version check - you might want to improve this
if exist "version.json" (
    REM Could parse version.json here for more accurate comparison
    echo Version check: Please verify if update is needed
) else (
    echo No version file found, proceeding with update...
)

REM Ask user confirmation
set /p "CONFIRM=Download and install %UPDATE_VERSION%? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Update cancelled by user
    pause
    exit /b 0
)

REM Create temp directory
if exist "%UPDATE_DIR%" rmdir /s /q "%UPDATE_DIR%"
mkdir "%UPDATE_DIR%"

echo Downloading update...
powershell -Command "try { Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%UPDATE_DIR%\update.zip' -UseBasicParsing; Write-Output 'Download completed'; } catch { Write-Output 'Download failed'; exit 1; }"
if %errorlevel% neq 0 (
    echo Download failed!
    pause
    exit /b 1
)

echo Extracting update...
powershell -Command "try { Expand-Archive -Path '%UPDATE_DIR%\update.zip' -DestinationPath '%UPDATE_DIR%' -Force; Write-Output 'Extract completed'; } catch { Write-Output 'Extract failed'; exit 1; }"
if %errorlevel% neq 0 (
    echo Extract failed!
    pause
    exit /b 1
)

REM Find extracted folder
for /d %%d in ("%UPDATE_DIR%\*") do (
    if exist "%%d\EPC Information Combiner.exe" (
        set "EXTRACTED_DIR=%%d"
        goto :found_app
    )
)

echo Could not find application in extracted files
pause
exit /b 1

:found_app
echo Found application in: !EXTRACTED_DIR!

REM Create backup
if exist "%BACKUP_DIR%" rmdir /s /q "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%"

echo Creating backup...
xcopy "%CURRENT_DIR%*.exe" "%BACKUP_DIR%\" /y >nul 2>&1
xcopy "%CURRENT_DIR%assets" "%BACKUP_DIR%\assets\" /s /y >nul 2>&1
xcopy "%CURRENT_DIR%themes" "%BACKUP_DIR%\themes\" /s /y >nul 2>&1

echo Installing update...
REM Copy new files (preserve user data)
xcopy "!EXTRACTED_DIR!\*" "%CURRENT_DIR%" /s /y /exclude:data_preserve.txt >nul 2>&1

echo Update completed!
echo.
echo Starting application...
start "" "%CURRENT_DIR%EPC Information Combiner.exe"

REM Clean up
timeout /t 3 /nobreak >nul
rmdir /s /q "%UPDATE_DIR%" >nul 2>&1

echo Update process finished!
pause