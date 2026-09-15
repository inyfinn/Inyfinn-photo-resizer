#Requires -Version 5.1
<#
.SYNOPSIS
  Buduje instalator Inno Setup po zbudowaniu EXE (package_release.ps1).
#>
param(
    [switch]$Launch
)

$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$BinRoot = Split-Path -Parent $DevRoot
$AppRoot = Split-Path -Parent $BinRoot
$iss = Join-Path $DevRoot "installer\inyfinn_resizer.iss"
$outDir = Join-Path $DevRoot "installer-output"

$exe = Join-Path $BinRoot "InyfinnPhotoResizer.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Brak $exe — najpierw uruchom BIN\build.bat lub package_release.ps1"
}

$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
}
if (-not $iscc) {
    Write-Error "Brak Inno Setup 6 (ISCC.exe). Pobierz: https://jrsoftware.org/isinfo.php"
}

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
# D:\Marketing bywa reparse/sync — ISCC kończy kompresję i pada na „plik w użyciu”.
$isccOutDir = Join-Path $env:TEMP "inyfinn-installer-output"
if (Test-Path -LiteralPath $isccOutDir) {
    Remove-Item -LiteralPath $isccOutDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $isccOutDir | Out-Null
Write-Host "ISCC: $iscc"
Write-Host "ISS:  $iss"
Write-Host "OUT:  $isccOutDir"
& $iscc "/O$isccOutDir" $iss
$isccCode = $LASTEXITCODE
if ($null -eq $isccCode -or $isccCode -ne 0) {
    Write-Error "ISCC zakończył się kodem $isccCode"
}

$venvPy = Join-Path $DevRoot ".venv\Scripts\python.exe"
$version = "unknown"
if (Test-Path $venvPy) {
    $version = (& $venvPy -c "from inyfinn_resizer import __version__; print(__version__)").Trim()
}
$expectedName = "InyfinnPhotoResizer-$version-setup.exe"
$compiledSetup = Join-Path $isccOutDir $expectedName
if (-not (Test-Path -LiteralPath $compiledSetup)) {
    $found = Get-ChildItem -LiteralPath $isccOutDir -Filter "InyfinnPhotoResizer-*-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $compiledSetup = $found.FullName }
}
if (-not (Test-Path -LiteralPath $compiledSetup)) {
    Write-Error "Nie znaleziono pliku setup w $isccOutDir"
}

& (Join-Path $DevRoot "scripts\sign_file.ps1") $compiledSetup

$expectedPath = Join-Path $outDir $expectedName
Copy-Item -LiteralPath $compiledSetup -Destination $expectedPath -Force
$setup = Get-Item -LiteralPath $expectedPath

# Tylko bieżący setup — stare 2.4.x mylą i odpalają SmartScreen na niepodpisanym pliku.
$oldDirs = @($outDir, (Join-Path $AppRoot "PORTABLE"), (Join-Path $AppRoot "release"))
foreach ($dir in $oldDirs) {
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    Get-ChildItem -LiteralPath $dir -Recurse -Filter "InyfinnPhotoResizer-*-setup.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne $setup.FullName } |
        ForEach-Object {
            Write-Host "Usuwam stary instalator: $($_.FullName)"
            Remove-Item -LiteralPath $_.FullName -Force
        }
}

Write-Host ""
Write-Host "Instalator gotowy:"
Write-Host "  $($setup.FullName)"
Write-Host ""

if ($Launch) {
    Start-Process $setup.FullName
}
