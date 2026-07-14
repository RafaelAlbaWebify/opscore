$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { & (Join-Path $Root "scripts\setup.ps1") }
New-Item -ItemType Directory -Path (Join-Path $Root "artifacts") -Force | Out-Null
& $Python -m ruff check .
& $Python -m mypy src
& $Python -m pytest --junitxml=artifacts\test-results.xml
Write-Host "OPSCORE verification PASS" -ForegroundColor Green
