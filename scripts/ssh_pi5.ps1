# SSH connection script for Pi 5 with password
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [string]$Command = ""
)

# Check if plink is available (PuTTY)
$plinkPath = Get-Command plink -ErrorAction SilentlyContinue

if ($plinkPath) {
    Write-Host "Using plink for SSH connection..." -ForegroundColor Cyan
    if ($Command) {
        echo y | plink -ssh -pw $PiPassword "$PiUser@$PiIP" $Command
    } else {
        plink -ssh -pw $PiPassword "$PiUser@$PiIP"
    }
} else {
    Write-Host "plink not found. Attempting with OpenSSH..." -ForegroundColor Yellow
    Write-Host "Note: OpenSSH requires interactive password entry" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To install plink (PuTTY):" -ForegroundColor Cyan
    Write-Host "  winget install PuTTY.PuTTY" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or connect manually:" -ForegroundColor Cyan
    Write-Host "  ssh $PiUser@$PiIP" -ForegroundColor Gray
    Write-Host ""
    
    if ($Command) {
        ssh -o StrictHostKeyChecking=no "$PiUser@$PiIP" $Command
    } else {
        ssh -o StrictHostKeyChecking=no "$PiUser@$PiIP"
    }
}







