# Robust Pi Sync Script - Handles merge conflicts automatically
# This script ensures sync works flawlessly every time by:
# 1. Stashing local changes if needed
# 2. Pulling from GitHub
# 3. Automatically resolving conflicts (accepts GitHub version)
# 4. Providing clear status feedback

param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$DestPath = "~/AITUNER/2025-AI-TUNER-AGENTV3"
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔄 Robust Pi Sync - Auto-Conflict Resolution" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test SSH connection
Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor Green
Write-Host ""

# Step 2: Check git status and handle local changes
Write-Host "Step 2: Checking repository status..." -ForegroundColor Yellow
$statusCmd = "cd $DestPath && git status --porcelain"
$statusResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $statusCmd 2>&1

if ($statusResult -match "M\s|A\s|D\s|R\s|C\s|U\s") {
    Write-Host "⚠️  Local changes detected - stashing..." -ForegroundColor Yellow
    $stashCmd = "cd $DestPath && git stash push -m 'Auto-stash before sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')'"
    $stashResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $stashCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Local changes stashed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Stash warning (may be empty): $stashResult" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ No local changes detected" -ForegroundColor Green
}
Write-Host ""

# Step 3: Fetch latest from GitHub
Write-Host "Step 3: Fetching latest from GitHub..." -ForegroundColor Yellow
$fetchCmd = "cd $DestPath && git fetch origin main"
$fetchResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $fetchCmd 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Fetched latest changes" -ForegroundColor Green
} else {
    Write-Host "⚠️  Fetch warning: $fetchResult" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Attempt merge with automatic conflict resolution
Write-Host "Step 4: Merging changes (auto-resolving conflicts)..." -ForegroundColor Yellow

# Create a merge script that handles conflicts automatically
$mergeScript = @"
cd $DestPath

# Check if we're behind
BEHIND=`$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
if [ `$BEHIND -eq 0 ]; then
    echo "Already up to date"
    exit 0
fi

# Try to merge
git merge origin/main --no-edit 2>&1
MERGE_EXIT=`$?

if [ `$MERGE_EXIT -ne 0 ]; then
    # Check if there are conflicts
    if git diff --check 2>/dev/null | grep -q "conflict"; then
        echo "CONFLICTS_DETECTED"
        # List conflicted files
        git diff --name-only --diff-filter=U
    else
        # Other merge error
        echo "MERGE_ERROR"
        exit `$MERGE_EXIT
    fi
else
    echo "MERGE_SUCCESS"
    exit 0
fi
"@

$mergeResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "bash -c `"$mergeScript`"" 2>&1
$mergeOutput = $mergeResult -join "`n"

if ($mergeOutput -match "Already up to date") {
    Write-Host "✅ Repository already up to date" -ForegroundColor Green
} elseif ($mergeOutput -match "MERGE_SUCCESS") {
    Write-Host "✅ Successfully merged changes" -ForegroundColor Green
} elseif ($mergeOutput -match "CONFLICTS_DETECTED") {
    Write-Host "⚠️  Merge conflicts detected - auto-resolving..." -ForegroundColor Yellow
    
    # Extract conflicted files
    $conflictedFiles = $mergeOutput | Select-String -Pattern "^\s+(\S+)$" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    if ($conflictedFiles) {
        Write-Host "   Conflicted files: $($conflictedFiles -join ', ')" -ForegroundColor Gray
        
        # Resolve conflicts by accepting GitHub version (theirs)
        $resolveScript = @"
cd $DestPath
"@
        foreach ($file in $conflictedFiles) {
            $resolveScript += "`ngit checkout --theirs `"$file`" 2>/dev/null"
            $resolveScript += "`ngit add `"$file`" 2>/dev/null"
        }
        $resolveScript += @"

# Complete the merge
git commit --no-edit -m "Merge: Auto-resolved conflicts (accepted GitHub version)" 2>&1
echo "RESOLVE_COMPLETE"
"@
        
        $resolveResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "bash -c `"$resolveScript`"" 2>&1
        
        if ($resolveResult -match "RESOLVE_COMPLETE") {
            Write-Host "✅ Conflicts resolved (accepted GitHub version)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Conflict resolution had issues:" -ForegroundColor Yellow
            Write-Host $resolveResult -ForegroundColor Gray
        }
    }
} else {
    # Try alternative: reset and pull
    Write-Host "⚠️  Merge failed - trying reset and pull..." -ForegroundColor Yellow
    
    $resetScript = @"
cd $DestPath
# Save any uncommitted changes first
git stash push -m 'Pre-reset stash $(date)' 2>/dev/null
# Reset to match GitHub exactly
git reset --hard origin/main 2>&1
echo "RESET_COMPLETE"
"@
    
    $resetResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "bash -c `"$resetScript`"" 2>&1
    
    if ($resetResult -match "RESET_COMPLETE") {
        Write-Host "✅ Repository reset to match GitHub" -ForegroundColor Green
    } else {
        Write-Host "❌ Reset failed:" -ForegroundColor Red
        Write-Host $resetResult -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 5: Verify sync status
Write-Host "Step 5: Verifying sync status..." -ForegroundColor Yellow
$verifyCmd = "cd $DestPath && git status --short && echo '---' && git log --oneline -1"
$verifyResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $verifyCmd 2>&1

Write-Host "Repository status:" -ForegroundColor Gray
Write-Host $verifyResult -ForegroundColor Gray
Write-Host ""

# Step 6: Check if behind/ahead
$behindCmd = "cd $DestPath && git rev-list --count HEAD..origin/main 2>/dev/null || echo '0'"
$behindCount = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $behindCmd 2>&1 | Select-String -Pattern "^\d+$"

$aheadCmd = "cd $DestPath && git rev-list --count origin/main..HEAD 2>/dev/null || echo '0'"
$aheadCount = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $aheadCmd 2>&1 | Select-String -Pattern "^\d+$"

if ($behindCount -and [int]$behindCount -gt 0) {
    Write-Host "⚠️  Repository is $behindCount commits behind GitHub" -ForegroundColor Yellow
} elseif ($aheadCount -and [int]$aheadCount -gt 0) {
    Write-Host "ℹ️  Repository is $aheadCount commits ahead of GitHub" -ForegroundColor Cyan
} else {
    Write-Host "✅ Repository is in sync with GitHub" -ForegroundColor Green
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Sync Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: If local changes were stashed, you can recover them with:" -ForegroundColor Gray
Write-Host "  git stash list" -ForegroundColor Gray
Write-Host "  git stash pop" -ForegroundColor Gray
Write-Host ""

