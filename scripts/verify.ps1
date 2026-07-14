$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "OPSCORE setup failed with exit code $LASTEXITCODE."
    }
}

New-Item -ItemType Directory -Path (Join-Path $Root "artifacts") -Force | Out-Null

function Invoke-VerificationStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "Running $Name..." -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Invoke-VerificationStep -Name "Ruff" -Command {
    & $Python -m ruff check .
}

Invoke-VerificationStep -Name "mypy" -Command {
    & $Python -m mypy src
}

Invoke-VerificationStep -Name "pytest" -Command {
    & $Python -m pytest --junitxml=artifacts\test-results.xml
}

Write-Host "OPSCORE verification PASS" -ForegroundColor Green