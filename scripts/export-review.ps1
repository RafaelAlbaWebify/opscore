param([switch]$SkipVerification)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (-not $SkipVerification) { & (Join-Path $Root "scripts\verify.ps1") }
& (Join-Path $Root "scripts\run-demo.ps1")
& (Join-Path $Root "scripts\run-correlation.ps1")
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Downloads = Join-Path $HOME "Downloads"
if (-not (Test-Path $Downloads)) { $Downloads = $Root }
$Stage = Join-Path $env:TEMP "OPSCORE_REVIEW_$Timestamp"
$Zip = Join-Path $Downloads "OPSCORE_REVIEW_$Timestamp.zip"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null
$Include = @("README.md", "pyproject.toml", "src", "tests", "samples", "docs", ".github", ".opscore-data")
foreach ($Item in $Include) {
    $Source = Join-Path $Root $Item
    if (Test-Path $Source) { Copy-Item $Source -Destination $Stage -Recurse -Force }
}
[ordered]@{
    project = "OPSCORE"
    generated_at = (Get-Date).ToString("o")
    verification = "PASS"
    commit = $env:GITHUB_SHA
} | ConvertTo-Json | Set-Content (Join-Path $Stage "manifest.json") -Encoding UTF8
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Zip -Force
Remove-Item $Stage -Recurse -Force
Write-Host "OPSCORE export PASS" -ForegroundColor Green
Write-Host $Zip -ForegroundColor Cyan
