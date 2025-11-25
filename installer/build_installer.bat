@echo off
REM Build script for TelemetryIQ Windows Installer
REM Requires Inno Setup to be installed

echo Building TelemetryIQ Windows Installer...
echo.

REM Check if Inno Setup is installed
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist %INNO_SETUP% (
    echo ERROR: Inno Setup not found!
    echo Please install Inno Setup from https://jrsoftware.org/isdl.php
    echo Expected location: C:\Program Files (x86)\Inno Setup 6\
    pause
    exit /b 1
)

echo Using Inno Setup: %INNO_SETUP%
echo.

REM Compile installer
%INNO_SETUP% "%~dp0windows_installer.iss"

if errorlevel 1 (
    echo.
    echo ERROR: Installer build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installer built successfully!
echo Output: dist\TelemetryIQ-Setup.exe
echo ========================================
echo.
pause











