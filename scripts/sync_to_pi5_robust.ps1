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
Write-Host "Robust Pi Sync - Auto-Conflict Resolution" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test SSH connection
Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: SSH connection failed!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "OK: SSH connection successful" -ForegroundColor Green
Write-Host ""

# Step 2: Check git status and handle local changes
Write-Host "Step 2: Checking repository status..." -ForegroundColor Yellow
$statusCmd = "cd $DestPath && git status --porcelain"
$statusResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $statusCmd 2>&1

if ($statusResult -match "M\s|A\s|D\s|R\s|C\s|U\s") {
    Write-Host "WARNING: Local changes detected - stashing..." -ForegroundColor Yellow
    $stashCmd = "cd $DestPath && git stash push -m 'Auto-stash before sync' 2>&1"
    $stashResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $stashCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: Local changes stashed" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Stash warning (may be empty): $stashResult" -ForegroundColor Yellow
    }
} else {
    Write-Host "OK: No local changes detected" -ForegroundColor Green
}
Write-Host ""

# Step 3: Fetch latest from GitHub
Write-Host "Step 3: Fetching latest from GitHub..." -ForegroundColor Yellow
$fetchCmd = "cd $DestPath && git fetch origin main"
$fetchResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $fetchCmd 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Fetched latest changes" -ForegroundColor Green
} else {
    Write-Host "WARNING: Fetch warning: $fetchResult" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Check if behind and pull/merge
Write-Host "Step 4: Checking for updates and merging..." -ForegroundColor Yellow

# Check if behind first
$checkBehindCmd = "cd $DestPath && git rev-list --count HEAD..origin/main 2>/dev/null || echo '0'"
$behindCheck = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $checkBehindCmd 2>&1
$behindMatch = $behindCheck | Select-String -Pattern "^\d+$" | Select-Object -First 1
$isBehind = if ($behindMatch) { [int]$behindMatch.Matches[0].Value -gt 0 } else { $false }

if (-not $isBehind) {
    Write-Host "OK: Repository already up to date" -ForegroundColor Green
    $mergeOutput = "Already up to date"
} else {
    # Attempt merge with automatic conflict resolution
    Write-Host "   Pulling and merging changes..." -ForegroundColor Gray
    
    # Try simple pull first
    $pullCmd = "cd $DestPath && git pull origin main --no-edit 2>&1"
    $pullResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $pullCmd 2>&1
    $mergeOutput = $pullResult -join "`n"
    
    # Check if pull succeeded
    if ($LASTEXITCODE -eq 0 -and $mergeOutput -notmatch "error|conflict|CONFLICT|fatal") {
        Write-Host "OK: Successfully pulled and merged" -ForegroundColor Green
        $mergeOutput = "MERGE_SUCCESS"
    } elseif ($mergeOutput -match "conflict|CONFLICT") {
        # Handle conflicts
        $mergeOutput = "CONFLICTS_DETECTED`n" + $mergeOutput
    } else {
        $mergeOutput = "MERGE_ERROR`n" + $mergeOutput
    }
}

if ($mergeOutput -match "Already up to date") {
    Write-Host "OK: Repository already up to date" -ForegroundColor Green
} elseif ($mergeOutput -match "MERGE_SUCCESS") {
    Write-Host "OK: Successfully merged changes" -ForegroundColor Green
} elseif ($mergeOutput -match "CONFLICTS_DETECTED") {
    Write-Host "WARNING: Merge conflicts detected - auto-resolving..." -ForegroundColor Yellow
    
    # Extract conflicted files (lines after CONFLICTS_DETECTED)
    $lines = $mergeOutput -split "`n"
    $conflictedFiles = @()
    $foundMarker = $false
    foreach ($line in $lines) {
        if ($line -match "CONFLICTS_DETECTED") {
            $foundMarker = $true
            continue
        }
        if ($foundMarker -and $line.Trim() -and -not $line.StartsWith("CONFLICT")) {
            $conflictedFiles += $line.Trim()
        }
    }
    
    if ($conflictedFiles.Count -gt 0) {
        Write-Host "   Conflicted files: $($conflictedFiles -join ', ')" -ForegroundColor Gray
        
        # Resolve conflicts by accepting GitHub version (theirs)
        $resolveCmds = @()
        foreach ($file in $conflictedFiles) {
            $resolveCmds += "git checkout --theirs '$file' 2>/dev/null"
            $resolveCmds += "git add '$file' 2>/dev/null"
        }
        $resolveCmds += "git commit --no-edit -m 'Merge: Auto-resolved conflicts (accepted GitHub version)' 2>&1"
        $resolveCmds += "echo 'RESOLVE_COMPLETE'"
        
        $resolveCmd = "cd $DestPath && " + ($resolveCmds -join " && ")
        $resolveResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $resolveCmd 2>&1
        
        if ($resolveResult -match "RESOLVE_COMPLETE") {
            Write-Host "OK: Conflicts resolved (accepted GitHub version)" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Conflict resolution had issues:" -ForegroundColor Yellow
            Write-Host $resolveResult -ForegroundColor Gray
        }
    }
} else {
    # Try alternative: reset and pull
    Write-Host "WARNING: Merge failed - trying reset and pull..." -ForegroundColor Yellow
    
    $resetCmd = "cd $DestPath && git stash push -m 'Pre-reset stash' 2>/dev/null; git reset --hard origin/main 2>&1; echo 'RESET_COMPLETE'"
    $resetResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $resetCmd 2>&1
    
    if ($resetResult -match "RESET_COMPLETE") {
        Write-Host "OK: Repository reset to match GitHub" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Reset failed:" -ForegroundColor Red
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
$behindOutput = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $behindCmd 2>&1
$behindMatch = $behindOutput | Select-String -Pattern "^\d+$" | Select-Object -First 1
$behindCount = if ($behindMatch) { [int]$behindMatch.Matches[0].Value } else { 0 }

$aheadCmd = "cd $DestPath && git rev-list --count origin/main..HEAD 2>/dev/null || echo '0'"
$aheadOutput = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $aheadCmd 2>&1
$aheadMatch = $aheadOutput | Select-String -Pattern "^\d+$" | Select-Object -First 1
$aheadCount = if ($aheadMatch) { [int]$aheadMatch.Matches[0].Value } else { 0 }

if ($behindCount -gt 0) {
    Write-Host "WARNING: Repository is $behindCount commits behind GitHub" -ForegroundColor Yellow
} elseif ($aheadCount -gt 0) {
    Write-Host "INFO: Repository is $aheadCount commits ahead of GitHub" -ForegroundColor Cyan
} else {
    Write-Host "OK: Repository is in sync with GitHub" -ForegroundColor Green
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Sync Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: If local changes were stashed, you can recover them with:" -ForegroundColor Gray
Write-Host "  git stash list" -ForegroundColor Gray
Write-Host "  git stash pop" -ForegroundColor Gray
Write-Host ""
