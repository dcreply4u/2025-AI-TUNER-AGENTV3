# Fast sync using git pull on Pi (RECOMMENDED - much faster!)
# This assumes the repo already exists on Pi and is connected to GitHub
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

Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Pulling latest changes from GitHub..." -ForegroundColor Yellow
$pullCmd = "cd $DestPath && git pull origin main"
$pullResult = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $pullCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pulled from GitHub!" -ForegroundColor Green
    Write-Host $pullResult
} else {
    Write-Host "⚠️  Git pull had issues:" -ForegroundColor Yellow
    Write-Host $pullResult
    Write-Host ""
    Write-Host "If merge conflicts, run on Pi:" -ForegroundColor Cyan
    Write-Host "  cd $DestPath" -ForegroundColor Gray
    Write-Host "  python3 fix_pi_merge.py" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Sync complete!" -ForegroundColor Green

