#Requires -Version 5.1
<#
.SYNOPSIS
  Buduje EXE + _internal w korzeniu projektu. Instalator opcjonalnie (-Installer).
#>
param(
    [switch]$Launch,
    [switch]$Installer
)

$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$AppRoot = Split-Path -Parent $DevRoot
Set-Location $DevRoot

$venvPy = Join-Path $DevRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    python -m venv (Join-Path $DevRoot ".venv")
    & $venvPy -m pip install -e ".[dev]" pyinstaller
}

& $venvPy (Join-Path $DevRoot "scripts\generate_icon.py")
& $venvPy -m pip install -e . pyinstaller -q

$pq = Join-Path $DevRoot "tools\pngquant\pngquant.exe"
if (-not (Test-Path $pq)) {
    Write-Error "Brak pngquant. Uruchom: dev\scripts\setup_tools.ps1"
}

Get-Process InyfinnPhotoResizer -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

& $venvPy -m PyInstaller (Join-Path $DevRoot "installer\inyfinn_resizer.spec") --noconfirm --distpath (Join-Path $DevRoot "build\dist") --workpath (Join-Path $DevRoot "build\work")

$built = Join-Path $DevRoot "build\dist\InyfinnPhotoResizer"
$exe = Join-Path $built "InyfinnPhotoResizer.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Build failed - brak $exe"
}

$oldInternal = Join-Path $AppRoot "_internal"
if (Test-Path $oldInternal) {
    Remove-Item $oldInternal -Recurse -Force
}
$oldExe = Join-Path $AppRoot "InyfinnPhotoResizer.exe"
if (Test-Path $oldExe) {
    Remove-Item $oldExe -Force
}

Copy-Item (Join-Path $built "_internal") $AppRoot -Recurse -Force
Copy-Item $exe (Join-Path $AppRoot "InyfinnPhotoResizer.exe") -Force

$iconSrc = Join-Path $DevRoot "assets\icon.ico"
$iconDst = Join-Path $AppRoot "InyfinnPhotoResizer.ico"
if (Test-Path $iconSrc) {
    Copy-Item $iconSrc $iconDst -Force
}

# Porzadek w korzeniu — tylko EXE, _internal, dev, git, build.bat, README
@(
    (Join-Path $AppRoot "installer-output"),
    (Join-Path $AppRoot "release"),
    (Join-Path $AppRoot "docs")
) | ForEach-Object {
    if (Test-Path $_) { Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue }
}
Get-ChildItem $AppRoot -Filter "*-setup.exe" -ErrorAction SilentlyContinue | Remove-Item -Force

& (Join-Path $DevRoot "scripts\sign_file.ps1") (Join-Path $AppRoot "InyfinnPhotoResizer.exe")

Write-Host ""
Write-Host "GOTOWE v$( & $venvPy -c 'from inyfinn_resizer import __version__; print(__version__)' )"
Write-Host "  $AppRoot\InyfinnPhotoResizer.exe"
Write-Host "  $AppRoot\_internal\"
Write-Host ""

$version = & $venvPy -c "from inyfinn_resizer import __version__; print(__version__)"
$releaseDir = Join-Path $DevRoot "installer-output"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$portableZip = Join-Path $releaseDir "InyfinnPhotoResizer-$version-portable.zip"
if (Test-Path $portableZip) { Remove-Item $portableZip -Force }
Compress-Archive -Path @(
    (Join-Path $AppRoot "InyfinnPhotoResizer.exe"),
    (Join-Path $AppRoot "InyfinnPhotoResizer.ico"),
    (Join-Path $AppRoot "_internal")
) -DestinationPath $portableZip -CompressionLevel Optimal
Write-Host "Portable ZIP: $portableZip"
Write-Host ""

if ($Launch) {
    Start-Process (Join-Path $AppRoot "InyfinnPhotoResizer.exe")
}

if ($Installer) {
    Write-Host "Budowanie instalatora (Inno Setup)..."
    & (Join-Path $DevRoot "scripts\build_installer.ps1")
}
