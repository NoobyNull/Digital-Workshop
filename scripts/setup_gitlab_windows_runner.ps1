<#
.SYNOPSIS
    Idempotently provisions a Windows GitLab Runner for Digital Workshop builds.

.DESCRIPTION
    - Downloads gitlab-runner.exe if missing.
    - Registers the runner against the GitLab instance (defaults to http://192.168.0.40).
    - Applies the required tags so `.gitlab-ci.yml` jobs can target the runner.
    - Installs/starts the runner as a Windows service.
    - Optionally enforces a specific concurrent job limit and build/cache directories.

.EXAMPLE
    .\scripts\setup_gitlab_windows_runner.ps1 `
        -GitlabUrl "http://192.168.0.40" `
        -RegistrationToken "<TOKEN>" `
        -RunnerName "digital-workshop-windows-01" `
        -Tags "windows,digital-workshop,pyinstaller" `
        -WorkDir "C:\GitLab-Runner\builds"
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$RegistrationToken,

    [string]$GitlabUrl = "http://192.168.0.40",
    [string]$RunnerName = "digital-workshop-windows",
    [string]$Tags = "windows,digital-workshop,pyinstaller",
    [ValidateSet("shell")]
    [string]$Executor = "shell",
    [string]$InstallDir = "C:\GitLab-Runner",
    [string]$WorkDir = "C:\GitLab-Runner\builds",
    [string]$CacheDir = "C:\GitLab-Runner\cache",
    [int]$MaxConcurrentJobs = 1,
    [bool]$AllowUntagged = $true,
    [switch]$ForceDownload,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","SUCCESS")]
        [string]$Level = "INFO"
    )

    if ($Quiet -and $Level -eq "INFO") { return }
    $prefix = @{
        INFO    = "[INFO]"
        WARN    = "[WARN]"
        ERROR   = "[ERROR]"
        SUCCESS = "[ OK ]"
    }[$Level]

    Write-Host "$prefix $Message"
}

function Ensure-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Please run this script from an elevated PowerShell session."
    }
}

function Get-RunnerBinary {
    param([string]$DestinationPath)

    $runnerUri = "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-windows-amd64.exe"
    if (-not (Test-Path $DestinationPath) -or $ForceDownload) {
        Write-Log "Downloading GitLab Runner binary..." "INFO"
        Invoke-WebRequest -UseBasicParsing -Uri $runnerUri -OutFile $DestinationPath
        Write-Log "Runner binary downloaded to $DestinationPath" "SUCCESS"
    }
}

function Invoke-Runner {
    param(
        [string[]]$Arguments,
        [switch]$IgnoreErrors
    )

    $runnerExe = Join-Path $InstallDir "gitlab-runner.exe"
    if (-not (Test-Path $runnerExe)) {
        throw "gitlab-runner.exe not found at $runnerExe"
    }

    Write-Log "Running: gitlab-runner $($Arguments -join ' ')" "INFO"
    & $runnerExe @Arguments
    if ($LASTEXITCODE -ne 0 -and -not $IgnoreErrors) {
        throw "gitlab-runner exited with code $LASTEXITCODE"
    }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

Ensure-Admin
Ensure-Directory -Path $InstallDir
Ensure-Directory -Path $WorkDir
Ensure-Directory -Path $CacheDir

$runnerPath = Join-Path $InstallDir "gitlab-runner.exe"
Get-RunnerBinary -DestinationPath $runnerPath

$configPath = Join-Path $InstallDir "config.toml"
$runnerRegistered = $false
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw
    $runnerRegistered = $configContent -match [Regex]::Escape($RunnerName)
}

if (-not $runnerRegistered) {
    Write-Log "Registering runner '$RunnerName' with $GitlabUrl" "INFO"
    $args = @(
        "register",
        "--non-interactive",
        "--url", $GitlabUrl.TrimEnd("/"),
        "--registration-token", $RegistrationToken,
        "--executor", $Executor,
        "--name", $RunnerName,
        "--tag-list", $Tags,
        "--builds-dir", $WorkDir,
        "--cache-dir", $CacheDir,
        "--output-limit", "10000"
    )
    if ($AllowUntagged.IsPresent) {
        $args += "--run-untagged"
    }
    Invoke-Runner -Arguments $args
} else {
    Write-Log "Runner '$RunnerName' already registered. Skipping registration." "WARN"
}

Write-Log "Installing runner as Windows service" "INFO"
Invoke-Runner -Arguments @("install", "--working-directory", $WorkDir, "--config", $configPath) -IgnoreErrors
Invoke-Runner -Arguments @("start") -IgnoreErrors

if (Test-Path $configPath) {
    $configText = Get-Content $configPath -Raw
    if ($configText -match "concurrent\s*=") {
        $configText = [Regex]::Replace($configText, "concurrent\s*=\s*\d+", "concurrent = $MaxConcurrentJobs", 1)
    } else {
        $configText = "concurrent = $MaxConcurrentJobs`n$configText"
    }

    if ($configText -match "shell\s*=") {
        $configText = [Regex]::Replace($configText, "shell\s*=\s*""[^""]+""", "shell = ""powershell""", 1)
    }
    Set-Content -Path $configPath -Value $configText -Encoding UTF8
}

Write-Log "Verifying runner connectivity..." "INFO"
Invoke-Runner -Arguments @("verify", "--name", $RunnerName) -IgnoreErrors
Invoke-Runner -Arguments @("status") -IgnoreErrors

Write-Log "Runner setup complete. Monitor CI/CD → Runners on $GitlabUrl for the green status badge." "SUCCESS"
