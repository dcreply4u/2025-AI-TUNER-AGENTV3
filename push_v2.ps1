# PowerShell script to push v2 branch to GitHub using token
param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubToken
)

$ErrorActionPreference = "Stop"

Write-Host "Pushing v2 branch to GitHub..." -ForegroundColor Green
Write-Host ""

# Get current remote URL
$remoteUrl = git remote get-url origin
Write-Host "Current remote: $remoteUrl" -ForegroundColor Cyan

# Extract username and repo from URL
if ($remoteUrl -match "https://github.com/([^/]+)/([^/]+)\.git") {
    $username = $matches[1]
    $repo = $matches[2]
    
    # Update remote URL to include token
    $newRemoteUrl = "https://$username`:$GitHubToken@github.com/$username/$repo.git"
    
    Write-Host "Updating remote URL with token..." -ForegroundColor Yellow
    git remote set-url origin $newRemoteUrl
    
    try {
        # Push to v2 branch
        Write-Host "Pushing to origin/v2..." -ForegroundColor Yellow
        git push origin v2
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Successfully pushed to GitHub v2 branch!" -ForegroundColor Green
            Write-Host "Repository: https://github.com/$username/$repo/tree/v2" -ForegroundColor Cyan
        } else {
            Write-Host ""
            Write-Host "❌ Push failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            exit 1
        }
    } finally {
        # Restore original remote URL (remove token for security)
        Write-Host ""
        Write-Host "Restoring original remote URL (removing token)..." -ForegroundColor Yellow
        git remote set-url origin $remoteUrl
        Write-Host "✅ Remote URL restored" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Could not parse remote URL: $remoteUrl" -ForegroundColor Red
    exit 1
}
















