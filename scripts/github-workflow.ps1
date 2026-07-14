param(
    [Parameter(Position = 0)]
    [ValidateSet("verify-pr", "sync", "ui")]
    [string]$Command = "verify-pr",

    [Parameter(Position = 1)]
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Repo = "RafaelAlbaWebify/opscore"
$Git = (Get-Command git.exe -ErrorAction Stop).Source
$Gh = @(
    (Get-Command gh.exe -ErrorAction SilentlyContinue).Source
    "$env:ProgramFiles\GitHub CLI\gh.exe"
    "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $Gh) {
    throw "GitHub CLI was not found. Install it with winget install --id GitHub.cli --exact."
}

function Invoke-Native {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter(ValueFromRemainingArguments)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE."
    }
}

function Get-LatestPullRequestRun {
    $Json = & $Gh run list `
        --repo $Repo `
        --workflow ci.yml `
        --branch $Branch `
        --event pull_request `
        --limit 1 `
        --json databaseId,status,conclusion,url,headSha,createdAt

    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $Runs = $Json | ConvertFrom-Json
    if ($Runs.Count -eq 0) {
        return $null
    }

    return $Runs[0]
}

try {
    Write-Host "Checking GitHub authentication..." -ForegroundColor Cyan
    Invoke-Native $Gh auth status --hostname github.com

    Push-Location $Root
    try {
        Write-Host "Updating OPSCORE repository..." -ForegroundColor Cyan
        Invoke-Native $Git fetch origin --prune

        & $Git ls-remote --exit-code --heads origin $Branch 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Remote branch '$Branch' does not exist."
        }

        $CurrentBranch = (& $Git branch --show-current).Trim()
        if ($CurrentBranch -ne $Branch) {
            & $Git show-ref --verify --quiet "refs/heads/$Branch"
            if ($LASTEXITCODE -eq 0) {
                Invoke-Native $Git checkout $Branch
            }
            else {
                Invoke-Native $Git checkout -b $Branch --track "origin/$Branch"
            }
        }

        Invoke-Native $Git reset --hard "origin/$Branch"
        Invoke-Native $Git clean -fd

        switch ($Command) {
            "sync" {
                Write-Host "`nOPSCORE synchronized." -ForegroundColor Green
                Write-Host "Repository: $Root"
                Write-Host "Branch:     $Branch"
            }

            "ui" {
                Write-Host "Starting OPSCORE UI..." -ForegroundColor Cyan
                & powershell.exe `
                    -NoProfile `
                    -ExecutionPolicy Bypass `
                    -File (Join-Path $Root "OPSCORE.ps1") `
                    ui
            }

            "verify-pr" {
                $PrJson = & $Gh pr list `
                    --repo $Repo `
                    --head $Branch `
                    --state open `
                    --limit 1 `
                    --json number,url,isDraft

                if ($LASTEXITCODE -ne 0) {
                    throw "Could not query the pull request for '$Branch'."
                }

                $Prs = $PrJson | ConvertFrom-Json
                if ($Prs.Count -eq 0) {
                    throw "No open pull request exists for '$Branch'."
                }

                $Pr = $Prs[0]
                $PreviousRun = Get-LatestPullRequestRun
                $PreviousRunId = if ($PreviousRun) {
                    [string]$PreviousRun.databaseId
                }
                else {
                    $null
                }

                Write-Host "Creating an empty verification commit..." -ForegroundColor Cyan
                Invoke-Native $Git commit `
                    --allow-empty `
                    -m "Trigger CI verification for $Branch"

                Write-Host "Pushing normally to trigger CI..." -ForegroundColor Cyan
                Invoke-Native $Git push origin $Branch

                $Run = $null
                for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
                    Start-Sleep -Seconds 5
                    $Candidate = Get-LatestPullRequestRun
                    if (
                        $Candidate -and
                        [string]$Candidate.databaseId -ne $PreviousRunId
                    ) {
                        $Run = $Candidate
                        break
                    }
                    Write-Host "Waiting... $Attempt/30" -ForegroundColor DarkGray
                }

                if (-not $Run) {
                    throw "The push succeeded, but a new pull-request run was not found."
                }

                $RunId = [string]$Run.databaseId
                Write-Host "`nPR:      #$($Pr.number)" -ForegroundColor Green
                Write-Host "PR URL:  $($Pr.url)"
                Write-Host "Run ID:  $RunId"
                Write-Host "Run URL: $($Run.url)"

                & $Gh run watch $RunId --repo $Repo --exit-status
                $WatchExitCode = $LASTEXITCODE

                $FinalJson = & $Gh run view $RunId `
                    --repo $Repo `
                    --json status,conclusion,url,jobs

                if ($LASTEXITCODE -ne 0) {
                    throw "Could not retrieve the final workflow result."
                }

                $Final = $FinalJson | ConvertFrom-Json
                Write-Host "`nFinal result: $($Final.conclusion)" -ForegroundColor Cyan

                foreach ($Job in $Final.jobs) {
                    $Result = if ($Job.conclusion) {
                        $Job.conclusion
                    }
                    else {
                        $Job.status
                    }
                    $Color = if ($Result -eq "success") {
                        "Green"
                    }
                    elseif ($Result -eq "failure") {
                        "Red"
                    }
                    else {
                        "Yellow"
                    }
                    Write-Host "$($Job.name): $Result" -ForegroundColor $Color
                    foreach ($Step in $Job.steps) {
                        $StepResult = if ($Step.conclusion) {
                            $Step.conclusion
                        }
                        else {
                            $Step.status
                        }
                        Write-Host "  - $($Step.name): $StepResult"
                    }
                }

                if ($WatchExitCode -ne 0 -or $Final.conclusion -ne "success") {
                    $LogPath = Join-Path `
                        ([Environment]::GetFolderPath("Desktop")) `
                        "OPSCORE_CI_FAILED_$RunId.txt"
                    & $Gh run view $RunId --repo $Repo --log-failed |
                        Set-Content -Path $LogPath -Encoding UTF8
                    Write-Host "Failure log saved to $LogPath" -ForegroundColor Yellow
                    throw "OPSCORE CI failed. Do not merge PR #$($Pr.number)."
                }

                Write-Host "`nOPSCORE CI PASS" -ForegroundColor Green
                Write-Host "PR #$($Pr.number) is ready for final review." -ForegroundColor Green
            }
        }
    }
    finally {
        Pop-Location
    }
}
catch {
    Write-Host "`nOPSCORE GitHub workflow failed." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
