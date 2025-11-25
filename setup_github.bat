@echo off
REM Batch script to set up GitHub repository
REM Usage: setup_github.bat <github-username> [repo-name]

if "%1"=="" (
    echo Usage: setup_github.bat ^<github-username^> [repo-name]
    echo Example: setup_github.bat dcreply4u ai-tuner-agent
    exit /b 1
)

set GITHUB_USERNAME=%1
set REPO_NAME=%2
if "%REPO_NAME%"=="" set REPO_NAME=ai-tuner-agent

echo Setting up GitHub repository...
echo.

REM Check if we're in a git repository
if not exist .git (
    echo Error: Not in a git repository. Run 'git init' first.
    exit /b 1
)

REM Check if remote already exists
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo Remote 'origin' already exists:
    git remote get-url origin
    set /p OVERWRITE="Overwrite? (y/n): "
    if /i not "%OVERWRITE%"=="y" (
        echo Aborted.
        exit /b 0
    )
    git remote remove origin
)

REM Add remote
set REMOTE_URL=https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
echo Adding remote: %REMOTE_URL%
git remote add origin %REMOTE_URL%

REM Rename branch to main if needed
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
if not "%CURRENT_BRANCH%"=="main" (
    echo Renaming branch from '%CURRENT_BRANCH%' to 'main'...
    git branch -M main
)

REM Check if there are uncommitted changes
git status --porcelain >nul 2>&1
if %errorlevel% equ 0 (
    echo Uncommitted changes detected. Staging and committing...
    git add .
    git commit -m "Update: Prepare for GitHub push"
)

REM Push to GitHub
echo.
echo Pushing to GitHub...
echo Note: You may be prompted for credentials.
echo Use a Personal Access Token as password: https://github.com/settings/tokens
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo Success! Repository pushed to GitHub.
    echo View at: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
) else (
    echo.
    echo Push failed. Common issues:
    echo 1. Repository doesn't exist on GitHub - create it first at https://github.com/new
    echo 2. Authentication failed - use Personal Access Token instead of password
    echo 3. Network issues - check your internet connection
)

pause

