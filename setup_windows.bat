@echo off
REM TelemetryIQ Windows Setup Script
REM Sets up Python environment, installs dependencies, and configures drivers

echo ========================================
echo TelemetryIQ Windows Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or later from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Upgrade pip
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [3/5] Installing Python dependencies...
python -m pip install -r requirements.txt
echo.

REM Install Windows-specific dependencies
echo [4/5] Installing Windows-specific dependencies...
python -m pip install pyserial pyusb python-OBD
echo.

REM Create virtual environment (optional but recommended)
echo [5/5] Creating virtual environment (optional)...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created. Activate with: venv\Scripts\activate
) else (
    echo Virtual environment already exists.
)
echo.

REM Check for drivers
echo Checking for hardware drivers...
if exist "drivers\FTDI\CDM21228_Setup.exe" (
    echo FTDI driver found. Run drivers\FTDI\CDM21228_Setup.exe to install.
)
if exist "drivers\CH340\CH341SER.EXE" (
    echo CH340 driver found. Run drivers\CH340\CH341SER.EXE to install.
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Install hardware drivers if using USB adapters
echo 2. Connect your hardware (Arduino, USB-CAN adapter, etc.)
echo 3. Run: python demo.py
echo.
pause











