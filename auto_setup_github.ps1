# Automated GitHub Setup Script
# This will attempt to create the repository and push code

$GitHubUsername = "dcreply4u"
$RepoName = "ai-tuner-agent"
$RepoUrl = "https://github.com/$GitHubUsername/$RepoName.git"

Write-Host "=== Automated GitHub Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if repository already exists
Write-Host "Step 1: Checking if repository exists..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://api.github.com/repos/$GitHubUsername/$RepoName" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Repository already exists!" -ForegroundColor Green
    $repoExists = $true
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "⚠️  Repository doesn't exist yet." -ForegroundColor Yellow
        Write-Host "   You need to create it first at: https://github.com/new" -ForegroundColor Yellow
        Write-Host "   Repository name: $RepoName" -ForegroundColor Yellow
        Write-Host "   Then run this script again, or use create_github_repo.ps1 with a token" -ForegroundColor Yellow
        $repoExists = $false
    } else {
        Write-Host "❌ Error checking repository: $($_.Exception.Message)" -ForegroundColor Red
        $repoExists = $false
    }
}

if (-not $repoExists) {
    Write-Host ""
    Write-Host "Please create the repository first:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: $RepoName" -ForegroundColor White
    Write-Host "3. Description: AI-powered racing telemetry and tuning system" -ForegroundColor White
    Write-Host "4. Choose Public or Private" -ForegroundColor White
    Write-Host "5. DO NOT check 'Initialize with README'" -ForegroundColor White
    Write-Host "6. Click 'Create repository'" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Press Enter after creating the repository, or 'q' to quit"
    if ($continue -eq 'q') { exit }
}

# Step 2: Check current git status
Write-Host ""
Write-Host "Step 2: Checking git status..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Step 3: Remove existing remote if it exists
Write-Host ""
Write-Host "Step 3: Configuring remote..." -ForegroundColor Yellow
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Removing existing remote: $existingRemote" -ForegroundColor Yellow
    git remote remove origin
}
Write-Host "Adding remote: $RepoUrl" -ForegroundColor Cyan
git remote add origin $RepoUrl

# Step 4: Rename branch to main if needed
Write-Host ""
Write-Host "Step 4: Ensuring branch is 'main'..." -ForegroundColor Yellow
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch from '$currentBranch' to 'main'..." -ForegroundColor Cyan
    git branch -M main
} else {
    Write-Host "Already on 'main' branch" -ForegroundColor Green
}

# Step 5: Push to GitHub
Write-Host ""
Write-Host "Step 5: Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "You may be prompted for credentials." -ForegroundColor Yellow
Write-Host "Username: $GitHubUsername" -ForegroundColor Cyan
Write-Host "Password: Use a Personal Access Token (not your GitHub password)" -ForegroundColor Cyan
Write-Host "Get token at: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 SUCCESS! Repository pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository URL: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Yellow
    Write-Host "  - View your code: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor White
    Write-Host "  - Clone it elsewhere: git clone $RepoUrl" -ForegroundColor White
    Write-Host "  - Share it with others!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "  1. Repository doesn't exist - create it at https://github.com/new" -ForegroundColor Yellow
    Write-Host "  2. Authentication failed - use Personal Access Token as password" -ForegroundColor Yellow
    Write-Host "  3. Wrong credentials - check username and token" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To retry, run this script again after fixing the issue." -ForegroundColor Cyan
}

