@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Build CS2ChatTranslationBot

:: === Settings ===
set APP_NAME=CS2ChatTranslationBot
set ENTRY_POINT=app\main.py
set EXTRA_PATH=app
set CONFIG_FILE=config.json
set LANG_SRC_DIR=app\lang
set DIST_DIR=dist\%APP_NAME%
set UPDATER_FILE=app\updater.py

echo.
echo 🏗️  Building %APP_NAME% with PyInstaller...
echo.

:: --------------------------------------------------------------------------------
:: Create build number from current date/time: ddMMHHmm  (day, month, hour, minute)
:: Using PowerShell for locale-independent formatting
for /f %%A in ('powershell -NoProfile -Command "Get-Date -Format \"ddMMHHmm\""') do set BUILDNUMBER=%%A
set CURRENT_VERSION=0.1.%BUILDNUMBER%

echo 📌 CURRENT_VERSION = %CURRENT_VERSION%
:: --------------------------------------------------------------------------------

:: Clean old builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del "%APP_NAME%.spec" 2>nul

:: --------------------------------------------------------------------------------
:: Also write a version module your app can import if you want:
::   Python: from _build_version import CURRENT_VERSION
echo CURRENT_VERSION = "%CURRENT_VERSION%" > app\_build_version.py

:: --------------------------------------------------------------------------------
:: PyInstaller command
pyinstaller %ENTRY_POINT% ^
 --name %APP_NAME% ^
 --onedir ^
 --windowed ^
 --paths %EXTRA_PATH% ^
 --add-data "%CONFIG_FILE%;." ^
 --add-data "app\_build_version.py;."

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    :: restore updater file if patched
    if exist "%UPDATER_FILE%.bak" move /y "%UPDATER_FILE%.bak" "%UPDATER_FILE%" >nul
    pause
    exit /b %errorlevel%
)

:: Restore original updater after successful build
if exist "%UPDATER_FILE%.bak" (
    move /y "%UPDATER_FILE%.bak" "%UPDATER_FILE%" >nul
)

:: --------------------------------------------------------------------------------
:: Copy language files
echo.
echo 📦 Copying language files to %DIST_DIR%\lang ...
if not exist "%DIST_DIR%\lang" mkdir "%DIST_DIR%\lang"
copy "%LANG_SRC_DIR%\lang_*.json" "%DIST_DIR%\lang" >nul

:: Write VERSION.txt into the output folder for reference
echo %CURRENT_VERSION% > "%DIST_DIR%\VERSION.txt"

echo.
echo ✅ Build completed successfully!
echo 📁 Output: %DIST_DIR%
echo 🔖 Version: %CURRENT_VERSION%
echo.
dir /b "%DIST_DIR%"
echo.

endlocal
