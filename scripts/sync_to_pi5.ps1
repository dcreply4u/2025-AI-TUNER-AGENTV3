# Sync 2025-AI-TUNER-AGENTV3 to Raspberry Pi 5
# NOTE: This script copies files one-by-one and can be slow for large projects
# For faster sync, use sync_to_pi5_fast.ps1 (uses git pull on Pi)
# FIXED: Now uses correct source path (2025-AI-TUNER-AGENTV3)
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$SourcePath = "C:\Users\DC\OneDrive\Desktop\AITUNER\2025-AI-TUNER-AGENTV3",
    [string]$DestPath = "~/AITUNER/2025-AI-TUNER-AGENTV3"
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$pscpPath = "C:\Program Files\PuTTY\pscp.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔄 Syncing 2025-AI-TUNER-AGENTV3 to Pi 5" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Source: $SourcePath" -ForegroundColor Gray
Write-Host "Destination: $DestPath" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  NOTE: This method copies files one-by-one and can be slow." -ForegroundColor Yellow
Write-Host "    For faster sync, use: .\scripts\sync_to_pi5_fast.ps1" -ForegroundColor Yellow
Write-Host "    (Uses git pull on Pi - much faster!)" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $pscpPath)) {
    Write-Host "❌ pscp not found. Please install PuTTY." -ForegroundColor Red
    exit 1
}

# Exclude patterns
$excludePatterns = @(
    "*.log",
    "*.pyc",
    "__pycache__",
    ".git",
    "venv",
    "*.zip",
    "*.tmp"
)

Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Creating directory structure on Pi..." -ForegroundColor Yellow
$mkdirResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "mkdir -p $DestPath/{services,ui,controllers,interfaces,core,scripts,data,logs,docs} 2>/dev/null; echo 'Directories created'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Directories created" -ForegroundColor Green
} else {
    Write-Host "⚠️  Directory creation warning: $mkdirResult" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 3: Copying essential files..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

# Copy key files first
$keyFiles = @(
    "requirements.txt",
    "demo_safe.py",
    "README.md"
)

$fileCount = 0
foreach ($file in $keyFiles) {
    $src = Join-Path $SourcePath $file
    if (Test-Path $src) {
        Write-Host "  Copying $file..." -ForegroundColor Gray -NoNewline
        $copyResult = & $pscpPath -hostkey $hostKey -pw $PiPassword "$src" "$PiUser@$PiIP`:$DestPath/" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
            $fileCount++
        } else {
            Write-Host " ❌ Failed" -ForegroundColor Red
            Write-Host "    Error: $copyResult" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️  $file not found, skipping..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Step 4: Copying directories..." -ForegroundColor Yellow
# Copy directories (excluding patterns)
$dirsToCopy = @("services", "ui", "controllers", "interfaces", "core", "scripts", "docs")

$totalFiles = 0
$copiedFiles = 0
$failedFiles = 0

foreach ($dir in $dirsToCopy) {
    $srcDir = Join-Path $SourcePath $dir
    if (Test-Path $srcDir) {
        $files = Get-ChildItem -Path $srcDir -Recurse -File
        $dirFileCount = $files.Count
        $totalFiles += $dirFileCount
        Write-Host "  Copying $dir/ ($dirFileCount files)..." -ForegroundColor Gray
        
        $dirCopied = 0
        $dirFailed = 0
        
        # Use pscp with recursive copy
        foreach ($file in $files) {
            $relPath = $file.FullName.Substring($SourcePath.Length + 1)
            $destDir = Split-Path $relPath -Parent
            
            # Create directory if needed
            if ($destDir) {
                $mkdirCmd = "mkdir -p `"$DestPath/$destDir`""
                $mkdirResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $mkdirCmd 2>&1
            }
            
            # Copy file
            $copyResult = & $pscpPath -hostkey $hostKey -pw $PiPassword $file.FullName "$PiUser@$PiIP`:$DestPath/$relPath" 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dirCopied++
                $copiedFiles++
            } else {
                $dirFailed++
                $failedFiles++
                Write-Host "    ❌ Failed: $relPath" -ForegroundColor Red
            }
            
            # Progress indicator every 10 files
            if (($dirCopied + $dirFailed) % 10 -eq 0) {
                Write-Host "    Progress: $($dirCopied + $dirFailed)/$dirFileCount" -ForegroundColor Gray
            }
        }
        
        Write-Host "    ✅ $dirCopied files copied, ❌ $dirFailed failed" -ForegroundColor $(if ($dirFailed -eq 0) { "Green" } else { "Yellow" })
    } else {
        Write-Host "  ⚠️  $dir/ not found, skipping..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Summary: $copiedFiles files copied successfully" -ForegroundColor Green
if ($failedFiles -gt 0) {
    Write-Host "         $failedFiles files failed to copy" -ForegroundColor Red
}

Write-Host ""
if ($failedFiles -eq 0) {
    Write-Host "✅ File sync complete!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Sync completed with $failedFiles errors" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Next: Install Python dependencies on Pi" -ForegroundColor Cyan
Write-Host "      Or run: git pull origin main (if repo exists on Pi)" -ForegroundColor Cyan






