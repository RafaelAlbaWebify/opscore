$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11 or later is required." }
if (-not (Test-Path ".venv")) { python -m venv .venv }
$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"
Write-Host "OPSCORE setup PASS" -ForegroundColor Green
