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
& $iscc $iss
if ($LASTEXITCODE -ne 0) {
    Write-Error "ISCC zakończył się kodem $LASTEXITCODE"
}

$setup = Get-ChildItem $outDir -Filter "InyfinnPhotoResizer-*-setup.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $setup) {
    $setup = Get-ChildItem (Join-Path $AppRoot "installer-output") -Filter "InyfinnPhotoResizer-*-setup.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}
if (-not $setup) {
    Write-Error "Nie znaleziono pliku setup w $outDir"
}

& (Join-Path $DevRoot "scripts\sign_file.ps1") $setup.FullName
Write-Host ""
Write-Host "Instalator gotowy:"
Write-Host "  $($setup.FullName)"
Write-Host ""

if ($Launch) {
    Start-Process $setup.FullName
}
