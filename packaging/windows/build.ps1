$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-NativeSuccess {
  param([string]$Step)
  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed with exit code $LASTEXITCODE"
  }
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Version = (Select-String -Path (Join-Path $Root "pyproject.toml") -Pattern '^version = "([^"]+)"$').Matches[0].Groups[1].Value
$Venv = Join-Path $Root ".venv-windows-build"
$Build = Join-Path $Root "build-windows"
$Output = Join-Path $Root "dist-windows"

Set-Location $Root

py -3 (Join-Path $Root "scripts\check-version-consistency.py")
Assert-NativeSuccess "Checking package version consistency"

if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
if (Test-Path $Build) { Remove-Item -Recurse -Force $Build }
if (Test-Path $Output) { Remove-Item -Recurse -Force $Output }
New-Item -ItemType Directory -Path $Build, $Output | Out-Null

py -3 -m venv $Venv
Assert-NativeSuccess "Creating the Windows build environment"
$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
Assert-NativeSuccess "Upgrading pip"
& $Python -m pip install -r (Join-Path $PSScriptRoot "requirements-build.txt")
Assert-NativeSuccess "Installing build dependencies"
& $Python -m pip install $Root
Assert-NativeSuccess "Installing Weightrail"
& $Python -m pytest -q $Root
Assert-NativeSuccess "Running the Windows test suite"

& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name Weightrail `
  --distpath $Build `
  --workpath (Join-Path $Root "build\pyinstaller-gui") `
  --specpath (Join-Path $Root "build") `
  --collect-all matplotlib `
  --hidden-import matplotlib.backends.backend_tkagg `
  (Join-Path $PSScriptRoot "gui_entry.py")
Assert-NativeSuccess "Building the Windows GUI executable"

& $Python -m PyInstaller --noconfirm --clean --onefile --console `
  --name Weightrail-CLI `
  --distpath $Build `
  --workpath (Join-Path $Root "build\pyinstaller-cli") `
  --specpath (Join-Path $Root "build") `
  (Join-Path $PSScriptRoot "cli_entry.py")
Assert-NativeSuccess "Building the Windows CLI executable"

& (Join-Path $Build "Weightrail-CLI.exe") --version
Assert-NativeSuccess "Checking the packaged CLI version"
$SmokeDb = Join-Path $env:TEMP "weightrail-windows-package-smoke.sqlite"
if (Test-Path $SmokeDb) { Remove-Item -Force $SmokeDb }
& (Join-Path $Build "Weightrail-CLI.exe") --db-path $SmokeDb 123.4 | Out-Null
Assert-NativeSuccess "Writing with the packaged CLI"
& (Join-Path $Build "Weightrail-CLI.exe") --db-path $SmokeDb --summary | Out-Null
Assert-NativeSuccess "Reading with the packaged CLI"
Remove-Item -Force $SmokeDb

Compress-Archive -Path (Join-Path $Build "Weightrail.exe"), (Join-Path $Build "Weightrail-CLI.exe") `
  -DestinationPath (Join-Path $Output "Weightrail-$Version-windows-x86_64-portable.zip")

$MakeNsis = (Get-Command makensis.exe -ErrorAction SilentlyContinue)
if (-not $MakeNsis) {
  $Candidates = @(
    "$env:ProgramFiles\NSIS\makensis.exe",
    "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
  )
  $MakeNsisPath = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $MakeNsisPath) { throw "NSIS makensis.exe was not found." }
} else {
  $MakeNsisPath = $MakeNsis.Source
}

& $MakeNsisPath "/DVERSION=$Version" "/DSOURCE_DIR=$Build" "/DOUTPUT_DIR=$Output" `
  (Join-Path $PSScriptRoot "Weightrail.nsi")
Assert-NativeSuccess "Building the Windows installer"

Get-FileHash -Algorithm SHA256 (Join-Path $Output "*") | ForEach-Object {
  "{0}  {1}" -f $_.Hash.ToLowerInvariant(), (Split-Path $_.Path -Leaf)
} | Set-Content -Encoding ascii (Join-Path $Output "SHA256SUMS")

Write-Host "Windows package build completed: $Output"
