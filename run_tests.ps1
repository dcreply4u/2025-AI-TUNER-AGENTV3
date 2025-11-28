# QA Test Runner - Opens in new terminal window
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host "QA TEST RUNNER - Starting Tests" -ForegroundColor Cyan
Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host ""

# Run the test script with unbuffered output
python -u run_tests_console.py

Write-Host ""
Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

