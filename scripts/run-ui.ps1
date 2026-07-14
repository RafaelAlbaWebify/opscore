param(
    [int]$Port = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

$env:OPSCORE_WORKSPACE = Join-Path $Root ".opscore-data\api"
$Url = "http://127.0.0.1:$Port"

if (-not $NoBrowser) {
    Start-Process $Url
}

Write-Host "OPSCORE Operator Workbench: $Url" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the local server." -ForegroundColor DarkGray
Set-Location $Root
& $Python -m uvicorn opscore.api:app --host 127.0.0.1 --port $Port

if ($LASTEXITCODE -ne 0) {
    throw "OPSCORE operator interface exited with code $LASTEXITCODE."
}
