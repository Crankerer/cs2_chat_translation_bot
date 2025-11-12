@echo off
setlocal
title Build CS2ChatHUD

:: === Settings ===
set APP_NAME=CS2ChatHUD
set ENTRY_POINT=app\main.py
set EXTRA_PATH=app
set CONFIG_FILE=config.json
set LANG_SRC_DIR=app\lang
set DIST_DIR=dist\%APP_NAME%

echo.
echo 🏗️  Building %APP_NAME% with PyInstaller...
echo.

:: Delete old builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del "%APP_NAME%.spec" 2>nul

:: === PyInstaller command ===
pyinstaller %ENTRY_POINT% ^
 --name %APP_NAME% ^
 --onedir ^
 --windowed ^
 --paths %EXTRA_PATH% ^
 --add-data "%CONFIG_FILE%;."

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b %errorlevel%
)

:: === Copy language files ===
echo.
echo 📦 Copying language files to %DIST_DIR%\lang ...
if not exist "%DIST_DIR%\lang" mkdir "%DIST_DIR%\lang"
copy "%LANG_SRC_DIR%\lang_*.json" "%DIST_DIR%\lang" >nul

echo.
echo ✅ Build completed successfully!
echo 📁 Output: %DIST_DIR%
echo.
dir /b "%DIST_DIR%"
echo.
endlocal
