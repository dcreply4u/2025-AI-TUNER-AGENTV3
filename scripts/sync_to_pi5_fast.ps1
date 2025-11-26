# Fast sync using git pull on Pi (RECOMMENDED - much faster!)
# This script now uses robust conflict resolution
# For maximum reliability, use sync_to_pi5_robust.ps1 instead
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$DestPath = "~/AITUNER/2025-AI-TUNER-AGENTV3"
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔄 Fast Sync: Pulling from GitHub on Pi" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tip: For automatic conflict resolution, use:" -ForegroundColor Yellow
Write-Host "    .\scripts\sync_to_pi5_robust.ps1" -ForegroundColor Yellow
Write-Host ""

Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Stashing local changes (if any)..." -ForegroundColor Yellow
$stashCmd = "cd $DestPath && git stash push -m 'Auto-stash before sync' 2>&1 || echo 'No changes to stash'"
$stashResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $stashCmd 2>&1
Write-Host $stashResult -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Pulling latest changes from GitHub..." -ForegroundColor Yellow
$pullCmd = "cd $DestPath && git pull origin main 2>&1"
$pullResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $pullCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pulled from GitHub!" -ForegroundColor Green
    Write-Host $pullResult
} else {
    Write-Host "⚠️  Git pull had issues:" -ForegroundColor Yellow
    Write-Host $pullResult
    Write-Host ""
    Write-Host "💡 Auto-resolving conflicts..." -ForegroundColor Cyan
    
    # Auto-resolve conflicts
    $resolveCmd = @"
cd $DestPath
# Check for conflicts
if git diff --check 2>/dev/null | grep -q conflict || git status --porcelain | grep -q "^UU"; then
    # Get conflicted files
    CONFLICTED=`$(git diff --name-only --diff-filter=U 2>/dev/null)
    if [ -n "`$CONFLICTED" ]; then
        echo "Resolving conflicts in: `$CONFLICTED"
        echo `$CONFLICTED | xargs -I {} git checkout --theirs {} 2>/dev/null
        echo `$CONFLICTED | xargs -I {} git add {} 2>/dev/null
        git commit --no-edit -m "Merge: Auto-resolved conflicts" 2>&1
        echo "CONFLICTS_RESOLVED"
    fi
else
    # Try reset if merge completely failed
    git reset --hard origin/main 2>&1
    echo "RESET_TO_ORIGIN"
fi
"@
    
    $resolveResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "bash -c `"$resolveCmd`"" 2>&1
    
    if ($resolveResult -match "CONFLICTS_RESOLVED" -or $resolveResult -match "RESET_TO_ORIGIN") {
        Write-Host "✅ Conflicts automatically resolved!" -ForegroundColor Green
        Write-Host $resolveResult -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Could not auto-resolve. Please use sync_to_pi5_robust.ps1" -ForegroundColor Yellow
        Write-Host $resolveResult -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✅ Sync complete!" -ForegroundColor Green

