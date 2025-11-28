# Advanced Code Review Automation Script
# Runs comprehensive code analysis including security, complexity, and performance

param(
    [string]$Mode = "full",  # full, security, complexity, performance
    [switch]$InstallDeps = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Advanced Code Review Automation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the project root
if (-not (Test-Path "requirements-dev.txt")) {
    Write-Host "Error: requirements-dev.txt not found. Are you in the project root?" -ForegroundColor Red
    exit 1
}

# Install dependencies if requested
if ($InstallDeps) {
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow
    pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Create reports directory
$reportsDir = "reports"
if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir | Out-Null
}

# Run code review based on mode
switch ($Mode) {
    "security" {
        Write-Host "Running security scans only..." -ForegroundColor Yellow
        python tools/advanced_code_review.py --security-only
    }
    "complexity" {
        Write-Host "Running complexity analysis only..." -ForegroundColor Yellow
        python tools/advanced_code_review.py --complexity-only
    }
    "full" {
        Write-Host "Running full code review..." -ForegroundColor Yellow
        python tools/advanced_code_review.py
    }
    default {
        Write-Host "Invalid mode: $Mode. Use: full, security, or complexity" -ForegroundColor Red
        exit 1
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Code Review Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Reports saved to: $reportsDir/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view reports:" -ForegroundColor Yellow
    Write-Host "  - Security: reports/bandit-report.json, reports/pip-audit-report.json" -ForegroundColor White
    Write-Host "  - Complexity: reports/radon-complexity.json, reports/radon-maintainability.json" -ForegroundColor White
    Write-Host "  - Full Report: reports/full-code-review.json" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Code review completed with errors. Check output above." -ForegroundColor Red
    exit 1
}

