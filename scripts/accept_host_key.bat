@echo off
REM Accept SSH host key for Pi 5 and test connection
echo Accepting SSH host key for aituner@192.168.1.214...
echo.
echo This will prompt you to accept the host key.
echo Type 'yes' when prompted, then enter password: aituner
echo.
pause

"C:\Program Files\PuTTY\plink.exe" -ssh aituner@192.168.1.214 "echo Connection successful && uname -a && whoami"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Host key accepted! You can now use automated scripts.
) else (
    echo.
    echo ❌ Connection failed. Check:
    echo   1. Pi is powered on and connected to network
    echo   2. SSH is enabled on Pi
    echo   3. Username and password are correct
)

pause






