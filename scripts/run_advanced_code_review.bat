@echo off
REM Advanced Code Review Automation Script (Windows Batch)
REM Runs comprehensive code analysis

setlocal

if "%1"=="" (
    set MODE=full
) else (
    set MODE=%1
)

echo ========================================
echo Advanced Code Review Automation
echo ========================================
echo.

REM Check if we're in the project root
if not exist "requirements-dev.txt" (
    echo Error: requirements-dev.txt not found. Are you in the project root?
    exit /b 1
)

REM Create reports directory
if not exist "reports" mkdir reports

REM Run code review
if "%MODE%"=="security" (
    echo Running security scans only...
    python tools\advanced_code_review.py --security-only
) else if "%MODE%"=="complexity" (
    echo Running complexity analysis only...
    python tools\advanced_code_review.py --complexity-only
) else (
    echo Running full code review...
    python tools\advanced_code_review.py
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Code Review Complete!
    echo ========================================
    echo.
    echo Reports saved to: reports\
) else (
    echo.
    echo Code review completed with errors. Check output above.
    exit /b 1
)

