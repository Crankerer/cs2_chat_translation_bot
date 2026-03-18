@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Build CS2ChatTranslationBot

:: === Settings ===
set APP_NAME=CS2ChatTranslationBot
set ENTRY_POINT=app\main.py
set CONFIG_FILE=config.json
set LANG_SRC_DIR=app\lang
set DIST_DIR=dist\%APP_NAME%
set NUITKA_BUILD_DIR=.nuitka_build

set UPDATE_HELPER_SCRIPT=update_helper.py
set UPDATE_HELPER_NAME=update_helper

echo.
echo Building %APP_NAME% with Nuitka...
echo.

:: --------------------------------------------------------------------------------
:: Create build number from current date/time: ddMMHHmm
for /f %%A in ('powershell -NoProfile -Command "Get-Date -Format \"yyddMMHHmm\""') do set BUILDNUMBER=%%A
set CURRENT_VERSION=0.5.%BUILDNUMBER%

echo CURRENT_VERSION = %CURRENT_VERSION%
:: --------------------------------------------------------------------------------

:: Write version module (imported by app at runtime)
echo CURRENT_VERSION = "%CURRENT_VERSION%" > app\_build_version.py

:: Clean old builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q %NUITKA_BUILD_DIR% 2>nul

:: --------------------------------------------------------------------------------
:: Build main app (standalone, no console window)
python -m nuitka ^
 --standalone ^
 --windows-console-mode=disable ^
 --output-filename=%APP_NAME%.exe ^
 --output-dir=%NUITKA_BUILD_DIR% ^
 --enable-plugin=tk-inter ^
 %ENTRY_POINT%

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

:: Move Nuitka output folder (main.dist) to dist\APP_NAME
mkdir dist 2>nul
move "%NUITKA_BUILD_DIR%\main.dist" "%DIST_DIR%"

:: --------------------------------------------------------------------------------
:: Build update_helper as single-file EXE
echo.
echo Building %UPDATE_HELPER_NAME% as onefile...
python -m nuitka ^
 --onefile ^
 --output-filename=%UPDATE_HELPER_NAME%.exe ^
 --output-dir=%NUITKA_BUILD_DIR% ^
 %UPDATE_HELPER_SCRIPT%

if %errorlevel% neq 0 (
    echo Build of %UPDATE_HELPER_NAME% failed!
    pause
    exit /b %errorlevel%
)

:: Copy update_helper.exe into the main dist folder
copy /Y "%NUITKA_BUILD_DIR%\%UPDATE_HELPER_NAME%.exe" "%DIST_DIR%\%UPDATE_HELPER_NAME%.exe" >nul

:: --------------------------------------------------------------------------------
:: Copy language files
echo.
echo Copying language files to %DIST_DIR%\lang ...
if not exist "%DIST_DIR%\lang" mkdir "%DIST_DIR%\lang"
copy "%LANG_SRC_DIR%\lang_*.json" "%DIST_DIR%\lang" >nul

:: Write VERSION.txt
echo %CURRENT_VERSION% > "%DIST_DIR%\VERSION.txt"

:: Cleanup Nuitka temp build folder
rmdir /s /q %NUITKA_BUILD_DIR% 2>nul

echo.
echo Build completed successfully!
echo Output: %DIST_DIR%
echo Version: %CURRENT_VERSION%
echo.
dir /b "%DIST_DIR%"
echo.

endlocal
