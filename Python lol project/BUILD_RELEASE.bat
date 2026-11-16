@echo off
setlocal
cd /d "%~dp0"
title LoL Match Assistant - Release Builder
color 0A

echo ================================================
echo    LoL Match Assistant - Release Builder
echo ================================================
echo.

if not exist "main.py" (
    echo ERROR: main.py not found beside this script.
    pause
    exit /b 1
)

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"

echo [1/5] Installing project dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/5] Cleaning previous build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [3/5] Building executable...
"%PYTHON_EXE%" -m PyInstaller main.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed. Check the output above.
    pause
    exit /b 1
)

if not exist "dist\LoLMatchAssistant.exe" (
    echo ERROR: The executable was not created.
    pause
    exit /b 1
)

set "RELEASE_FOLDER=%USERPROFILE%\Desktop\LoLMatchAssistant_Release"
if exist "%RELEASE_FOLDER%" (
    echo A release folder already exists:
    echo %RELEASE_FOLDER%
    choice /C YN /M "Replace that folder?"
    if errorlevel 2 (
        echo Keeping the existing release folder.
        exit /b 0
    )
    rmdir /s /q "%RELEASE_FOLDER%"
)

mkdir "%RELEASE_FOLDER%"
if errorlevel 1 (
    echo ERROR: Could not create the Desktop release folder.
    pause
    exit /b 1
)

echo [4/5] Copying the app and clean default files...
copy /y "dist\LoLMatchAssistant.exe" "%RELEASE_FOLDER%\" >nul
if errorlevel 1 goto :copy_error
copy /y "config.default.json" "%RELEASE_FOLDER%\config.json" >nul
if errorlevel 1 goto :copy_error
copy /y "champions.json" "%RELEASE_FOLDER%\" >nul
if errorlevel 1 goto :copy_error

echo [5/5] Writing quick-start instructions...
(
echo LoL Match Assistant
echo.
echo 1. Double-click LoLMatchAssistant.exe.
echo 2. If League is not open, the app will retry automatically.
echo 3. Close the app from the tray menu when you are done.
echo 4. To make a desktop shortcut: right-click the app, choose Show more options ^> Send to ^> Desktop to create a shortcut.
echo.
echo Your settings are saved in config.json beside the executable.
) > "%RELEASE_FOLDER%\README.txt"

echo.
echo Build complete:
echo %RELEASE_FOLDER%
echo Share this folder with your friends. They do not need Python installed.

exit /b 0

:copy_error
echo ERROR: Could not copy a release file.
pause
exit /b 1
