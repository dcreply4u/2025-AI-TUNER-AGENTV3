# PowerShell script to create GitHub repository via API
# Requires: GitHub Personal Access Token with 'repo' scope

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubToken,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "ai-tuner-agent",
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "AI-powered racing telemetry and tuning system",
    
    [Parameter(Mandatory=$false)]
    [switch]$Private = $false
)

$GitHubUsername = "dcreply4u"
$ApiUrl = "https://api.github.com/user/repos"

Write-Host "Creating GitHub repository: $RepoName" -ForegroundColor Green
Write-Host ""

# Prepare request body
$body = @{
    name = $RepoName
    description = $Description
    private = $Private.IsPresent
    auto_init = $false  # We already have files
} | ConvertTo-Json

# Create repository via API
try {
    $headers = @{
        "Authorization" = "token $GitHubToken"
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "AI-Tuner-Agent-Setup"
    }
    
    $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Headers $headers -Body $body -ContentType "application/json"
    
    Write-Host "✅ Repository created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository URL: $($response.html_url)" -ForegroundColor Cyan
    Write-Host "Clone URL: $($response.clone_url)" -ForegroundColor Cyan
    Write-Host ""
    
    # Now set up the remote and push
    Write-Host "Setting up local git remote..." -ForegroundColor Yellow
    
    # Remove existing remote if it exists
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        Write-Host "Removing existing remote..." -ForegroundColor Yellow
        git remote remove origin
    }
    
    # Add new remote
    git remote add origin $response.clone_url
    
    # Rename branch to main if needed
    $currentBranch = git branch --show-current
    if ($currentBranch -ne "main") {
        Write-Host "Renaming branch to 'main'..." -ForegroundColor Yellow
        git branch -M main
    }
    
    # Push to GitHub
    Write-Host ""
    Write-Host "Pushing code to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 Success! Your repository is now on GitHub!" -ForegroundColor Green
        Write-Host "View it at: $($response.html_url)" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "⚠️  Repository created, but push failed." -ForegroundColor Yellow
        Write-Host "You can push manually with: git push -u origin main" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Error creating repository:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host ""
        Write-Host "Authentication failed. Check your token:" -ForegroundColor Yellow
        Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor Yellow
        Write-Host "2. Generate new token (classic) with 'repo' scope" -ForegroundColor Yellow
    } elseif ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host ""
        Write-Host "Repository might already exist or name is invalid." -ForegroundColor Yellow
        Write-Host "Check: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Yellow
    }
    
    exit 1
}

