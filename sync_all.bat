@echo off
REM Sync All - Quick wrapper for sync_all.ps1
REM This script syncs to GitHub and Raspberry Pi

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "scripts\sync_all.ps1" %*

