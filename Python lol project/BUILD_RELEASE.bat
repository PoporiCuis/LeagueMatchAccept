@echo off
title LoL Match Assistant - Release Builder
color 0A

echo ================================================
echo    LoL Match Assistant - Release Builder
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Install/update dependencies
echo [1/5] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

REM Clean previous builds
echo [2/5] Cleaning previous builds...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1

REM Build executable
echo [3/5] Building executable (this may take a few minutes)...
pyinstaller main.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed! Check the output above.
    pause
    exit /b 1
)

REM Verify build success
if not exist "dist\LoLMatchAssistant.exe" (
    echo ERROR: Executable not created!
    pause
    exit /b 1
)

REM Create release folder on desktop
echo [4/5] Creating release package...
set "DESKTOP=%USERPROFILE%\Desktop"
set "RELEASE_FOLDER=%DESKTOP%\LoLMatchAssistant_Release"

if exist "%RELEASE_FOLDER%" (
    echo Removing existing release folder...
    rmdir /s /q "%RELEASE_FOLDER%" >nul 2>&1
)

mkdir "%RELEASE_FOLDER%"
if not exist "%RELEASE_FOLDER%" (
    echo ERROR: Could not create release folder on desktop!
    pause
    exit /b 1
)

REM Copy all necessary files
echo [5/5] Copying files to release package...

REM Copy main executable
copy "dist\LoLMatchAssistant.exe" "%RELEASE_FOLDER%\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy executable!
    pause
    exit /b 1
)

REM Copy configuration files
copy "config.json" "%RELEASE_FOLDER%\" >nul 2>&1
copy "champions.json" "%RELEASE_FOLDER%\" >nul 2>&1
copy "champions_owned.json" "%RELEASE_FOLDER%\" >nul 2>&1

REM Create README for end users
echo Creating README for end users...
(
echo LoL Match Assistant - Ready to Use
echo =====================================
echo.
echo QUICK START:
echo 1. Make sure League of Legends client is running
echo 2. Double-click LoLMatchAssistant.exe
echo 3. Configure your champion preferences
echo 4. Enable the features you want
echo.
echo FEATURES:
echo - Auto Accept matches
echo - Auto Ban/Pick champions
echo - Role-based champion profiles
echo - System tray integration
echo.
echo SYSTEM TRAY:
echo - Right-click tray icon for menu
echo - App runs in background when window is closed
echo.
echo TROUBLESHOOTING:
echo - Ensure League client is running before starting
echo - Only one instance can run at a time
echo - Check antivirus if app doesn't start
echo.
echo For support: Check the original project files
) > "%RELEASE_FOLDER%\README.txt"

REM Get file size for verification
for %%A in ("%RELEASE_FOLDER%\LoLMatchAssistant.exe") do set "FILESIZE=%%~zA"
set /a "FILESIZE_MB=%FILESIZE% / 1048576"

echo.
echo ================================================
echo           BUILD COMPLETED SUCCESSFULLY!
echo ================================================
echo.
echo Release package created at:
echo %RELEASE_FOLDER%
echo.
echo Package contents:
echo - LoLMatchAssistant.exe (%FILESIZE_MB% MB)
echo - Configuration files (JSON)
echo - README.txt
echo.
echo This folder is ready for distribution!
echo.

REM Ask to open folder
set /p OPEN="Open release folder? (Y/N): "
if /i "%OPEN%"=="Y" explorer "%RELEASE_FOLDER%"

echo.
echo Press any key to exit...
pause >nul
