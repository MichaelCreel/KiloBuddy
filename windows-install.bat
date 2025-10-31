@echo off
title KiloBuddy Installer for Windows

echo Starting KiloBuddy installation for Windows...
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check if Installer.py exists
if not exist "Installer.py" (
    echo Error: Installer.py not found in current directory.
    echo Make sure you're running this from the KiloBuddy folder.
    echo.
    pause
    exit /b 1
)

REM Run the Python installer
echo Launching Python installer...
python Installer.py

REM Keep window open so user can see any messages
echo.
pause