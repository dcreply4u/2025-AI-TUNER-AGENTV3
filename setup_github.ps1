# PowerShell script to set up GitHub repository
# Run this after creating the repository on GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "ai-tuner-agent"
)

Write-Host "Setting up GitHub repository..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "Error: Not in a git repository. Run 'git init' first." -ForegroundColor Red
    exit 1
}

# Check if remote already exists
$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Host "Remote 'origin' already exists: $remoteExists" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
    git remote remove origin
}

# Add remote
$remoteUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "Adding remote: $remoteUrl" -ForegroundColor Cyan
git remote add origin $remoteUrl

# Rename branch to main if needed
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch from '$currentBranch' to 'main'..." -ForegroundColor Cyan
    git branch -M main
}

# Check if there are uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "Uncommitted changes detected. Staging and committing..." -ForegroundColor Yellow
    git add .
    git commit -m "Update: Prepare for GitHub push"
}

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "Note: You may be prompted for credentials." -ForegroundColor Yellow
Write-Host "Use a Personal Access Token as password: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Repository pushed to GitHub." -ForegroundColor Green
    Write-Host "View at: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Push failed. Common issues:" -ForegroundColor Red
    Write-Host "1. Repository doesn't exist on GitHub - create it first at https://github.com/new" -ForegroundColor Yellow
    Write-Host "2. Authentication failed - use Personal Access Token instead of password" -ForegroundColor Yellow
    Write-Host "3. Network issues - check your internet connection" -ForegroundColor Yellow
}

