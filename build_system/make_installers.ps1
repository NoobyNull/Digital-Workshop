<#
  Build helper for Windows installers.
  - Ensures the PyInstaller EXE exists.
  - Produces a portable self-contained EXE copy.
  - Invokes NSIS (if available) to generate a setup installer.
  Usage:
    pwsh build_system/make_installers.ps1 [-SkipBuild] [-DistDir dist] [-AppName "Digital Workshop"]
#>
param(
  [switch]$SkipBuild = $false,
  [string]$DistDir = "dist",
  [string]$AppName = "Digital Workshop"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptPath
$DistPath = Join-Path $RepoRoot $DistDir
$ExeName = "$AppName.exe"

if (-not $SkipBuild) {
  Write-Host "[build] Ensuring PyInstaller output exists..."
  & python "$RepoRoot/build_system/build_exe.py"
}

$sourceExe = Join-Path $DistPath $ExeName
if (-not (Test-Path $sourceExe)) {
  throw "Expected EXE at $sourceExe; build may have failed."
}

# Create a portable/self-contained copy with a clear name.
$portableExe = Join-Path $DistPath "$AppName-portable.exe"
Copy-Item -Path $sourceExe -Destination $portableExe -Force
Write-Host "[ok] Portable EXE ready at $portableExe"

# Build NSIS installer if makensis is available.
$nsisScript = Join-Path $RepoRoot "build_system/installer.nsi"
$nsisOutput = Join-Path $DistPath "$AppName-Setup.exe"
$makensis = Get-Command "makensis.exe" -ErrorAction SilentlyContinue

if ($makensis) {
  Write-Host "[build] Creating NSIS installer..."
  & $makensis `
    "/DAPP_NAME=$AppName" `
    "/DAPP_EXE=$ExeName" `
    "/DDIST_DIR=$DistPath" `
    "/DOUTFILE=$nsisOutput" `
    "/DINSTALL_DIR=$PROGRAMFILES64\$AppName" `
    $nsisScript
  Write-Host "[ok] NSIS installer created at $nsisOutput"
} else {
  Write-Warning "makensis.exe not found on PATH; skipping NSIS installer. Install NSIS to enable."
}

Write-Host "[done] Installers are ready in $DistPath"
