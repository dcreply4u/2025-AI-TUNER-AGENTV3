# Setup SSH key authentication for Pi 5
# This will allow passwordless SSH access

param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner"
)

$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
$plinkPath = "C:\Program Files\PuTTY\plink.exe"

Write-Host "🔑 Setting up SSH key authentication..." -ForegroundColor Cyan
Write-Host ""

# Generate SSH key if it doesn't exist
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "Generating SSH key..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f $sshKeyPath -N '""' -q
    Write-Host "✅ SSH key generated" -ForegroundColor Green
} else {
    Write-Host "✅ SSH key already exists" -ForegroundColor Green
}

# Read public key
$publicKey = Get-Content "$sshKeyPath.pub"

Write-Host ""
Write-Host "📋 Public key:" -ForegroundColor Cyan
Write-Host $publicKey -ForegroundColor Gray
Write-Host ""

# Copy public key to Pi using plink
Write-Host "📤 Copying public key to Pi..." -ForegroundColor Yellow

# Create command to add key to authorized_keys
$addKeyCommand = @"
mkdir -p ~/.ssh && 
chmod 700 ~/.ssh && 
echo '$publicKey' >> ~/.ssh/authorized_keys && 
chmod 600 ~/.ssh/authorized_keys && 
echo 'SSH key added successfully'
"@

# Use plink to execute (user will need to accept host key first time)
Write-Host "⚠️  You may need to accept the host key (type 'y' when prompted)" -ForegroundColor Yellow
Write-Host ""

try {
    & $plinkPath -ssh -pw $PiPassword "$PiUser@$PiIP" $addKeyCommand
    
    Write-Host ""
    Write-Host "✅ SSH key authentication setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🧪 Testing passwordless connection..." -ForegroundColor Cyan
    
    # Test connection
    $testResult = & $plinkPath -ssh -i "$env:USERPROFILE\.ssh\id_rsa" "$PiUser@$PiIP" "echo 'Passwordless SSH works!'" 2>&1
    
    if ($testResult -match "Passwordless SSH works") {
        Write-Host "✅ Passwordless SSH is working!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Key may need to be added manually" -ForegroundColor Yellow
        Write-Host "   Run this on the Pi:" -ForegroundColor Gray
        Write-Host "   echo '$publicKey' >> ~/.ssh/authorized_keys" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual setup:" -ForegroundColor Yellow
    Write-Host "1. Copy this public key:" -ForegroundColor Gray
    Write-Host $publicKey -ForegroundColor White
    Write-Host ""
    Write-Host "2. On the Pi, run:" -ForegroundColor Gray
    Write-Host "   mkdir -p ~/.ssh" -ForegroundColor White
    Write-Host "   chmod 700 ~/.ssh" -ForegroundColor White
    Write-Host "   echo '$publicKey' >> ~/.ssh/authorized_keys" -ForegroundColor White
    Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor White
}







