# Run command on Pi 5 via SSH with password
param(
    [string]$PiIP = "192.168.1.214",
    [string]$PiUser = "aituner",
    [string]$PiPassword = "aituner",
    [Parameter(Mandatory=$true)]
    [string]$Command
)

$plinkPath = "C:\Program Files\PuTTY\plink.exe"

if (-not (Test-Path $plinkPath)) {
    Write-Host "❌ plink not found at $plinkPath" -ForegroundColor Red
    exit 1
}

# Create a temporary script file for plink to execute
$tempScript = [System.IO.Path]::GetTempFileName()
$Command | Out-File -FilePath $tempScript -Encoding ASCII

try {
    # Use plink with password and host key acceptance
    $hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"
    $result = & $plinkPath -ssh -hostkey $hostKey -pw $PiPassword "$PiUser@$PiIP" $Command 2>&1
    
    # Filter out host key prompts
    $result = $result | Where-Object { 
        $_ -notmatch "host key" -and 
        $_ -notmatch "guarantee" -and 
        $_ -notmatch "fingerprint" -and
        $_ -notmatch "Connection abandoned"
    }
    
    if ($result) {
        $result
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    if (Test-Path $tempScript) {
        Remove-Item $tempScript -Force
    }
}


