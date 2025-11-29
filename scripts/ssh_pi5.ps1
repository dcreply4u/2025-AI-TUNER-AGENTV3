# SSH connection script for Pi 5 with password (non-interactive when using plink)
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$Command = ""
)

# Prefer plink with known host key (non-interactive), fall back to OpenSSH
$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"

if (Test-Path $plinkPath) {
    Write-Host "Using plink for SSH connection (non-interactive)..." -ForegroundColor Cyan
    $baseArgs = @(
        "-batch",
        "-ssh",
        "-hostkey", $hostKey,
        "-pw", $PiPassword,
        "$PiUser@$PiIP"
    )

    if ($Command) {
        & $plinkPath @baseArgs $Command
    } else {
        & $plinkPath @baseArgs
    }
} else {
    Write-Host "plink not found. Attempting with OpenSSH (may be interactive)..." -ForegroundColor Yellow
    Write-Host "To install plink (PuTTY): winget install PuTTY.PuTTY" -ForegroundColor Gray
    Write-Host ""

    if ($Command) {
        ssh -o StrictHostKeyChecking=no "$PiUser@$PiIP" $Command
    } else {
        ssh -o StrictHostKeyChecking=no "$PiUser@$PiIP"
    }
}
