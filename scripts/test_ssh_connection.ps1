# Test SSH connection to Pi 5
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner"
)

Write-Host "Testing SSH connection to $PiUser@$PiIP..." -ForegroundColor Cyan

# Method 1: Try with plink and auto-accept host key
$plinkPath = "C:\Program Files\PuTTY\plink.exe"

if (Test-Path $plinkPath) {
    Write-Host "`n[Method 1] Using plink..." -ForegroundColor Yellow
    
    # First, accept the host key by connecting once
    Write-Host "Accepting host key (this may take a moment)..." -ForegroundColor Gray
    $null = echo y | & $plinkPath -ssh -pw $PiPassword "$PiUser@$PiIP" "exit" 2>&1
    
    # Now try the actual command
    Write-Host "Running test command..." -ForegroundColor Gray
    $output = & $plinkPath -ssh -pw $PiPassword "$PiUser@$PiIP" "echo '=== CONNECTION SUCCESSFUL ==='; uname -a; whoami; pwd; python3 --version 2>&1 || echo 'Python3 not found'" 2>&1
    
    if ($output) {
        Write-Host "`n✅ Connection successful! Output:" -ForegroundColor Green
        $output | Where-Object { $_ -notmatch "host key" -and $_ -notmatch "guarantee" } | ForEach-Object { Write-Host $_ }
        return $true
    } else {
        Write-Host "❌ Connection failed - no output" -ForegroundColor Red
    }
} else {
    Write-Host "plink not found at $plinkPath" -ForegroundColor Red
}

# Method 2: Try with OpenSSH (requires manual password entry or SSH keys)
Write-Host "`n[Method 2] OpenSSH requires interactive password or SSH keys" -ForegroundColor Yellow
Write-Host "To use OpenSSH, you need to:" -ForegroundColor Cyan
Write-Host "  1. Accept host key manually: ssh $PiUser@$PiIP" -ForegroundColor Gray
Write-Host "  2. Or set up SSH keys using: .\setup_ssh_keys.ps1" -ForegroundColor Gray

return $false






