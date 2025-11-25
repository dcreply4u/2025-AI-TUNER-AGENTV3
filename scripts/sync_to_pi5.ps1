# Sync AI-TUNER-AGENT to Raspberry Pi 5
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$SourcePath = "C:\Users\DC\OneDrive\Desktop\AITUNER\AI-TUNER-AGENT",
    [string]$DestPath = "~/AITUNER/AI-TUNER-AGENT"
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$pscpPath = "C:\Program Files\PuTTY\pscp.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔄 Syncing AI-TUNER-AGENT to Pi 5" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
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

Write-Host "Step 1: Creating directory structure on Pi..." -ForegroundColor Yellow
& $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "mkdir -p $DestPath/{services,ui,controllers,interfaces,core,scripts,data,logs,docs} 2>/dev/null; echo 'Directories created'"

Write-Host ""
Write-Host "Step 2: Copying essential files..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

# Copy key files first
$keyFiles = @(
    "requirements.txt",
    "demo_safe.py",
    "README.md"
)

foreach ($file in $keyFiles) {
    $src = Join-Path $SourcePath $file
    if (Test-Path $src) {
        Write-Host "  Copying $file..." -ForegroundColor Gray
        & $pscpPath -hostkey $hostKey -pw $PiPassword "$src" "$PiUser@$PiIP`:$DestPath/" 2>&1 | Out-Null
    }
}

# Copy directories (excluding patterns)
$dirsToCopy = @("services", "ui", "controllers", "interfaces", "core", "scripts", "docs")

foreach ($dir in $dirsToCopy) {
    $srcDir = Join-Path $SourcePath $dir
    if (Test-Path $srcDir) {
        Write-Host "  Copying $dir/..." -ForegroundColor Gray
        # Use pscp with recursive copy
        Get-ChildItem -Path $srcDir -Recurse -File | ForEach-Object {
            $relPath = $_.FullName.Substring($SourcePath.Length + 1)
            $destDir = Split-Path $relPath -Parent
            if ($destDir) {
                & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "mkdir -p `"$DestPath/$destDir`"" 2>&1 | Out-Null
            }
            & $pscpPath -hostkey $hostKey -pw $PiPassword $_.FullName "$PiUser@$PiIP`:$DestPath/$relPath" 2>&1 | Out-Null
        }
    }
}

Write-Host ""
Write-Host "✅ File sync complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Install Python dependencies on Pi" -ForegroundColor Cyan






