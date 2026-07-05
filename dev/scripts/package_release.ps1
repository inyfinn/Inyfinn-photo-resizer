#Requires -Version 5.1
<#
.SYNOPSIS
  Buduje program: EXE + ikona w korzeniu PHOTO RESIZER, zaleznosci w _internal/
#>
param(
    [switch]$Launch
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

$dupRelease = Join-Path $AppRoot "release"
if (Test-Path $dupRelease) {
    Remove-Item $dupRelease -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "GOTOWE - uruchom:"
Write-Host "  $AppRoot\InyfinnPhotoResizer.exe"
Write-Host ""

if ($Launch) {
    Start-Process (Join-Path $AppRoot "InyfinnPhotoResizer.exe")
}
