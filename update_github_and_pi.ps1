# Update GitHub and Pi Script
# Run this script to commit changes, push to GitHub, and sync to Pi

Write-Host "="*80
Write-Host "UPDATING GITHUB AND PI"
Write-Host "="*80
Write-Host ""

# Change to project directory
$projectDir = "C:\Users\DC\OneDrive\Desktop\AITUNER\2025-AI-TUNER-AGENTV3"
Set-Location $projectDir

Write-Host "[1] Checking git status..." -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "[2] Staging all changes..." -ForegroundColor Cyan
git add -A

Write-Host ""
Write-Host "[3] Committing changes..." -ForegroundColor Cyan
$commitMessage = "Enhanced AI Chat Advisor: Google search integration, improved responses, auto-population system, comprehensive test suite"
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Committed successfully" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No changes to commit or commit failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4] Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Pushed to GitHub successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Push failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5] Syncing to Pi..." -ForegroundColor Cyan
$syncScript = Join-Path $projectDir "scripts\sync_to_pi5.ps1"
if (Test-Path $syncScript) {
    & $syncScript
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Synced to Pi successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Pi sync failed" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠ Sync script not found: $syncScript" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "="*80
Write-Host "UPDATE COMPLETE"
Write-Host "="*80

