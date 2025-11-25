# Remote Setup Script for Raspberry Pi 5
# Run this from your Windows computer after SSH is enabled

param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner"
)

Write-Host "🚀 Starting Raspberry Pi 5 Remote Setup..." -ForegroundColor Cyan
Write-Host ""

# Test connection
Write-Host "📡 Testing connection to $PiIP..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $PiIP -Count 2 -Quiet
if (-not $pingResult) {
    Write-Host "❌ Cannot ping $PiIP. Check network connection." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Pi is reachable" -ForegroundColor Green

# Test SSH
Write-Host ""
Write-Host "🔐 Testing SSH connection..." -ForegroundColor Yellow
$sshTest = Test-NetConnection -ComputerName $PiIP -Port 22 -WarningAction SilentlyContinue
if (-not $sshTest.TcpTestSucceeded) {
    Write-Host "❌ SSH port 22 is not open. Please enable SSH on the Pi first." -ForegroundColor Red
    Write-Host "   See: docs/ENABLE_SSH_PI5.md" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ SSH port is open" -ForegroundColor Green

Write-Host ""
Write-Host "📋 Next steps (run these commands on the Pi via SSH):" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Connect to Pi:" -ForegroundColor White
Write-Host "   ssh $PiUser@$PiIP" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Update system:" -ForegroundColor White
Write-Host "   sudo apt update && sudo apt upgrade -y" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Install prerequisites:" -ForegroundColor White
Write-Host "   sudo apt install -y git python3 python3-pip python3-venv" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Clone repository:" -ForegroundColor White
Write-Host "   cd ~ && git clone https://github.com/dcreply4u/ai-tuner-agent.git AI-TUNER-AGENT" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Run setup:" -ForegroundColor White
Write-Host "   cd ~/AI-TUNER-AGENT && chmod +x scripts/*.sh && sudo ./scripts/pi5_setup.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Or use the automated setup script once SSH is working!" -ForegroundColor Yellow







