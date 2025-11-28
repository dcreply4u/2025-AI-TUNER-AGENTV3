# Sync All Script - Syncs to GitHub and Raspberry Pi
# This script:
# 1. Commits and pushes all changes to GitHub
# 2. Syncs the Pi repository to match GitHub
#
# Usage:
#   .\scripts\sync_all.ps1
#   .\scripts\sync_all.ps1 -CommitMessage "Your commit message"
#   .\scripts\sync_all.ps1 -SkipCommit  # Only sync Pi (assumes GitHub is already updated)

param(
    [string]$CommitMessage = "",
    [switch]$SkipCommit = $false,
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$DestPath = "~/AITUNER/2025-AI-TUNER-AGENTV3"
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

function Write-Progress-Step {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Activity,
        [string]$Status
    )
    $percent = [math]::Round(($Step / $Total) * 100)
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $percent -Id 1
    Write-Host "[$Step/$Total] $Status" -ForegroundColor Cyan
}

function Show-Summary {
    param(
        [string]$Title,
        [hashtable]$Data
    )
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    foreach ($key in $Data.Keys) {
        Write-Host "  $key : " -NoNewline -ForegroundColor Gray
        Write-Host $Data[$key] -ForegroundColor White
    }
    Write-Host ""
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Sync All - GitHub & Raspberry Pi        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get the script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Change to project root
Push-Location $projectRoot

try {
    $totalSteps = if ($SkipCommit) { 4 } else { 7 }
    $currentStep = 0
    
    # Step 1: Sync to GitHub
    if (-not $SkipCommit) {
        Write-Host "┌──────────────────────────────────────────┐" -ForegroundColor Yellow
        Write-Host "│  STEP 1: Syncing to GitHub                │" -ForegroundColor Yellow
        Write-Host "└──────────────────────────────────────────┘" -ForegroundColor Yellow
        Write-Host ""
        
        # Check if there are changes to commit
        $currentStep++
        Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Checking for changes..."
        $status = git status --porcelain
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Host "  ✓ No changes to commit" -ForegroundColor Green
            $githubSummary = @{
                "Status" = "Up to date"
                "Files Changed" = "0"
                "Action" = "Skipped"
            }
        } else {
            # Count changes
            $statusLines = $status -split "`n" | Where-Object { $_.Trim() -ne "" }
            $modified = ($statusLines | Where-Object { $_ -match "^\s*M" }).Count
            $added = ($statusLines | Where-Object { $_ -match "^\s*A" }).Count
            $deleted = ($statusLines | Where-Object { $_ -match "^\s*D" }).Count
            $totalFiles = $statusLines.Count
            
            Write-Host "  📋 Changes detected:" -ForegroundColor Cyan
            Write-Host "     Modified: $modified" -ForegroundColor Yellow
            Write-Host "     Added: $added" -ForegroundColor Green
            Write-Host "     Deleted: $deleted" -ForegroundColor Red
            Write-Host "     Total: $totalFiles files" -ForegroundColor White
            Write-Host ""
            
            # Show file list
            Write-Host "  Files:" -ForegroundColor Gray
            git status --short | ForEach-Object {
                $line = $_.Trim()
                if ($line -match "^\?\?") {
                    Write-Host "    + $($line.Substring(3))" -ForegroundColor Green
                } elseif ($line -match "^A") {
                    Write-Host "    + $($line.Substring(3))" -ForegroundColor Green
                } elseif ($line -match "^M") {
                    Write-Host "    ~ $($line.Substring(3))" -ForegroundColor Yellow
                } elseif ($line -match "^D") {
                    Write-Host "    - $($line.Substring(3))" -ForegroundColor Red
                } else {
                    Write-Host "    $($line.Substring(3))" -ForegroundColor Gray
                }
            }
            Write-Host ""
            
            # Get commit message
            if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
                $CommitMessage = Read-Host "  Enter commit message (or press Enter for default)"
                if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
                    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    $CommitMessage = "Auto-sync: $timestamp"
                }
            }
            
            # Add all changes
            $currentStep++
            Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Staging changes..."
            Write-Host "  📦 Staging $totalFiles files..." -ForegroundColor Cyan
            $addOutput = git add -A 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to add changes: $addOutput"
            }
            Write-Host "  ✓ All changes staged" -ForegroundColor Green
            Write-Host ""
            
            # Commit
            $currentStep++
            Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Creating commit..."
            Write-Host "  💾 Committing changes..." -ForegroundColor Cyan
            Write-Host "     Message: $CommitMessage" -ForegroundColor Gray
            $commitOutput = git commit -m $CommitMessage 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to commit changes: $commitOutput"
            }
            
            # Extract commit hash
            $commitHash = (git log -1 --format="%h") -replace "`n", ""
            $commitHashFull = (git log -1 --format="%H") -replace "`n", ""
            Write-Host "  ✓ Commit created: $commitHash" -ForegroundColor Green
            Write-Host ""
            
            # Push to GitHub
            $currentStep++
            Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Pushing to GitHub..."
            Write-Host "  🚀 Pushing to GitHub (origin/main)..." -ForegroundColor Cyan
            $pushOutput = git push origin main 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to push to GitHub: $pushOutput"
            }
            
            # Parse push output for details
            if ($pushOutput -match "(\d+)\s+objects") {
                $objects = $matches[1]
                Write-Host "  ✓ Pushed $objects objects to GitHub" -ForegroundColor Green
            } else {
                Write-Host "  ✓ Pushed to GitHub successfully" -ForegroundColor Green
            }
            
            $githubSummary = @{
                "Status" = "Success"
                "Files Changed" = $totalFiles
                "Commit Hash" = $commitHash
                "Commit Message" = $CommitMessage
                "Branch" = "main"
            }
            Write-Host ""
        }
        
        Show-Summary -Title "GitHub Sync Summary" -Data $githubSummary
    } else {
        Write-Host "┌──────────────────────────────────────────┐" -ForegroundColor Yellow
        Write-Host "│  STEP 1: Skipping GitHub Sync            │" -ForegroundColor Yellow
        Write-Host "└──────────────────────────────────────────┘" -ForegroundColor Yellow
        Write-Host "  (Using -SkipCommit flag)" -ForegroundColor Gray
        Write-Host ""
    }
    
    # Step 2: Sync to Pi
    Write-Host "┌──────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "│  STEP 2: Syncing Raspberry Pi             │" -ForegroundColor Yellow
    Write-Host "└──────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Target: $PiUser@$PiIP" -ForegroundColor Gray
    Write-Host "  Path: $DestPath" -ForegroundColor Gray
    Write-Host ""
    
    # Test SSH connection
    $currentStep++
    Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Connecting to Raspberry Pi..."
    Write-Host "  🔌 Testing SSH connection..." -ForegroundColor Cyan
    $testResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ ERROR: SSH connection failed!" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Connected to Raspberry Pi" -ForegroundColor Green
    Write-Host ""
    
    # Check for local changes on Pi and stash if needed
    $currentStep++
    Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Checking Pi repository status..."
    Write-Host "  📊 Checking repository status..." -ForegroundColor Cyan
    $statusCmd = "cd $DestPath; git status --porcelain"
    $statusResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $statusCmd 2>&1
    
    $hasLocalChanges = $false
    if ($statusResult -match "M\s|A\s|D\s|R\s|C\s|U\s") {
        $hasLocalChanges = $true
        $statusLines = ($statusResult -split "`n" | Where-Object { $_.Trim() -ne "" }).Count
        Write-Host "  [WARNING] Local changes detected: $statusLines file(s)" -ForegroundColor Yellow
        Write-Host "  [INFO] Stashing local changes..." -ForegroundColor Cyan
        $stashCmd = "cd $DestPath; git stash push -m 'Auto-stash before sync' 2>&1"
        $stashResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $stashCmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Local changes stashed (can recover with 'git stash pop')" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] Stash warning (may be empty): $stashResult" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✓ No local changes detected" -ForegroundColor Green
    }
    Write-Host ""
    
    # Fetch latest from GitHub
    $currentStep++
    Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Fetching latest from GitHub..."
    Write-Host "  📥 Fetching latest changes from GitHub..." -ForegroundColor Cyan
    $fetchCmd = "cd $DestPath; git fetch origin main"
    $fetchResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $fetchCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Fetched latest changes" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Fetch warning: $fetchResult" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Check if behind
    $behindCmd = "cd $DestPath; git rev-list --count HEAD..origin/main 2>/dev/null"
    $behindCmdAlt = "cd $DestPath; echo '0'"
    $behindOutput = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $behindCmd 2>&1
    $behindMatch = $behindOutput | Select-String -Pattern "^\d+$" | Select-Object -First 1
    $commitsBehind = if ($behindMatch) { [int]$behindMatch.Matches[0].Value } else { 0 }
    
    if ($commitsBehind -gt 0) {
        Write-Host "  📊 Repository is $commitsBehind commits behind GitHub" -ForegroundColor Yellow
    } else {
        Write-Host "  📊 Repository is up to date" -ForegroundColor Green
    }
    Write-Host ""
    
    # Pull and merge
    $currentStep++
    Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Pulling and merging changes..."
    Write-Host "  🔄 Pulling and merging changes..." -ForegroundColor Cyan
    $pullCmd = "cd $DestPath; git pull origin main --no-edit 2>&1"
    $pullResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $pullCmd 2>&1
    $pullOutput = $pullResult -join "`n"
    
    $syncStatus = "Unknown"
    $filesUpdated = 0
    
    if ($LASTEXITCODE -eq 0 -and $pullOutput -notmatch "error|conflict|CONFLICT|fatal") {
        if ($pullOutput -match "Already up to date") {
            Write-Host "  ✓ Repository already up to date" -ForegroundColor Green
            $syncStatus = "Up to date"
        } else {
            # Parse files updated
            if ($pullOutput -match "(\d+)\s+files?\s+changed") {
                $filesUpdated = [int]$matches[1]
            } elseif ($pullOutput -match "Fast-forward") {
                $filesUpdated = $commitsBehind
            }
            Write-Host "  ✓ Successfully pulled and merged" -ForegroundColor Green
            if ($filesUpdated -gt 0) {
                Write-Host "     Files updated: $filesUpdated" -ForegroundColor Gray
            }
            $syncStatus = "Success"
        }
    } elseif ($pullOutput -match "conflict|CONFLICT") {
        Write-Host "  [WARNING] Merge conflicts detected" -ForegroundColor Yellow
        Write-Host "  🔧 Auto-resolving conflicts (accepting GitHub version)..." -ForegroundColor Cyan
        
        # Resolve conflicts by accepting GitHub version
        $resolveCmd = "cd $DestPath; git checkout --theirs . 2>/dev/null; git add . 2>/dev/null; git commit --no-edit -m 'Merge: Auto-resolved conflicts (accepted GitHub version)' 2>&1; echo 'RESOLVE_COMPLETE'"
        $resolveResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $resolveCmd 2>&1
        
        if ($resolveResult -match "RESOLVE_COMPLETE") {
            Write-Host "  ✓ Conflicts resolved (accepted GitHub version)" -ForegroundColor Green
            $syncStatus = "Resolved conflicts"
        } else {
            Write-Host "  [WARNING] Conflict resolution had issues, trying reset..." -ForegroundColor Yellow
            $resetCmd = "cd $DestPath; git reset --hard origin/main 2>&1; echo 'RESET_COMPLETE'"
            $resetResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $resetCmd 2>&1
            if ($resetResult -match "RESET_COMPLETE") {
                Write-Host "  ✓ Repository reset to match GitHub" -ForegroundColor Green
                $syncStatus = "Reset to match GitHub"
            } else {
                throw "Failed to resolve conflicts"
            }
        }
    } else {
        Write-Host "  [WARNING] Pull had issues, trying reset..." -ForegroundColor Yellow
        $resetCmd = "cd $DestPath && git reset --hard origin/main 2>&1 && echo 'RESET_COMPLETE'"
        $resetResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $resetCmd 2>&1
        if ($resetResult -match "RESET_COMPLETE") {
            Write-Host "  ✓ Repository reset to match GitHub" -ForegroundColor Green
            $syncStatus = "Reset to match GitHub"
        } else {
            throw "Failed to sync Pi repository"
        }
    }
    Write-Host ""
    
    # Verify sync status
    $currentStep++
    Write-Progress-Step -Step $currentStep -Total $totalSteps -Activity "Sync All" -Status "Verifying sync status..."
    Write-Host "  ✅ Verifying sync status..." -ForegroundColor Cyan
    $verifyCmd = "cd $DestPath; git log --oneline -1; echo '---'; git rev-parse --short HEAD"
    $verifyResult = & $plinkPath -batch -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $verifyCmd 2>&1
    $commitInfo = ($verifyResult | Select-Object -First 1) -replace "`n", ""
    $commitHash = ($verifyResult | Select-Object -Last 1) -replace "`n", ""
    
    Write-Host "  Latest commit: $commitInfo" -ForegroundColor Gray
    Write-Host "  Commit hash: $commitHash" -ForegroundColor Gray
    Write-Host ""
    
    # Pi sync summary
    $piSummary = @{
        "Status" = $syncStatus
        "Connection" = "$PiUser@$PiIP"
        "Local Changes" = if ($hasLocalChanges) { "Stashed" } else { "None" }
        "Commits Behind" = if ($commitsBehind -gt 0) { "$commitsBehind" } else { "0" }
        "Files Updated" = if ($filesUpdated -gt 0) { "$filesUpdated" } else { "0" }
        "Latest Commit" = $commitHash
    }
    Show-Summary -Title "Pi Sync Summary" -Data $piSummary
    
    # Final summary
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║         ✓ Sync Complete!                 ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  GitHub: " -NoNewline -ForegroundColor Gray
    if (-not $SkipCommit) {
        Write-Host "Synced" -ForegroundColor Green
    } else {
        Write-Host "Skipped" -ForegroundColor Yellow
    }
    Write-Host "  Raspberry Pi: " -NoNewline -ForegroundColor Gray
    Write-Host "Synced" -ForegroundColor Green
    Write-Host ""
    
    Write-Progress -Activity "Sync All" -Completed -Id 1
    
} catch {
    Write-Progress -Activity "Sync All" -Completed -Id 1
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║            ✗ Sync Failed                 ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.InnerException) {
        Write-Host "  Details: $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  Troubleshooting:" -ForegroundColor Yellow
    Write-Host "    1. Check your internet connection" -ForegroundColor Gray
    Write-Host "    2. Verify GitHub credentials are configured" -ForegroundColor Gray
    Write-Host "    3. Ensure Pi is reachable: ping $PiIP" -ForegroundColor Gray
    Write-Host "    4. Check SSH connection: .\scripts\test_ssh_connection.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
} finally {
    Pop-Location
}

