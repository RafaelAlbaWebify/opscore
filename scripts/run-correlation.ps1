$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { & (Join-Path $Root "scripts\setup.ps1") }
& $Python -m opscore.cli correlate --workspace (Join-Path $Root ".opscore-data\imported")
Write-Host "OPSCORE import correlation PASS" -ForegroundColor Green
