@echo off
setlocal
title Build CS2ChatHUD

:: === Einstellungen ===
set APP_NAME=CS2ChatHUD
set ENTRY_POINT=app\main.py
set EXTRA_PATH=app
set CONFIG_FILE=config.json
set LANG_SRC_DIR=app\lang
set DIST_DIR=dist\%APP_NAME%

echo.
echo 🏗️  Baue %APP_NAME% mit PyInstaller...
echo.

:: Alte Builds löschen
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del "%APP_NAME%.spec" 2>nul

:: === PyInstaller-Aufruf ===
pyinstaller %ENTRY_POINT% ^
 --name %APP_NAME% ^
 --onedir ^
 --windowed ^
 --paths %EXTRA_PATH% ^
 --add-data "%CONFIG_FILE%;."

if %errorlevel% neq 0 (
    echo ❌ Fehler beim Build!
    pause
    exit /b %errorlevel%
)

:: === Sprachdateien kopieren ===
echo.
echo 📦 Kopiere Sprachdateien nach %DIST_DIR%\lang ...
if not exist "%DIST_DIR%\lang" mkdir "%DIST_DIR%\lang"
copy "%LANG_SRC_DIR%\lang_*.json" "%DIST_DIR%\lang" >nul

echo.
echo ✅ Build abgeschlossen!
echo 📁 Ausgabe: %DIST_DIR%
echo.
dir /b "%DIST_DIR%"
echo.
endlocal
