#Requires -Version 5.1
<#
.SYNOPSIS
  Buduje stabilna wersje one-dir w BIN/ i lekki launcher w korzeniu.
  -Portable = rozpakowany one-dir w PORTABLE/ (bez one-file 50 MB).
#>
param(
    [switch]$Launch,
    [switch]$Installer,
    [switch]$Portable
)

$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$BinRoot = Split-Path -Parent $DevRoot
$AppRoot = Split-Path -Parent $BinRoot
$PortableRoot = Join-Path $AppRoot "PORTABLE"
$PortableAppDir = Join-Path $PortableRoot "InyfinnPhotoResizer"
Set-Location $DevRoot

$venvPy = Join-Path $DevRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    python -m venv (Join-Path $DevRoot ".venv")
    & $venvPy -m pip install -e ".[dev]" pyinstaller
}

& $venvPy (Join-Path $DevRoot "scripts\generate_icon.py")
& $venvPy (Join-Path $DevRoot "src\inyfinn_resizer\app\themes\icons\generate_check_icons.py")
& $venvPy (Join-Path $DevRoot "src\inyfinn_resizer\app\themes\icons\generate_combo_icons.py")
& $venvPy -m pip install -e . pyinstaller -q

$pq = Join-Path $DevRoot "tools\pngquant\pngquant.exe"
if (-not (Test-Path $pq)) {
    Write-Error "Brak pngquant. Uruchom: BIN\dev\scripts\setup_tools.ps1"
}

Get-Process InyfinnPhotoResizer -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$distDir = Join-Path $DevRoot "build\dist"
& $venvPy -m PyInstaller (Join-Path $DevRoot "installer\inyfinn_resizer.spec") --noconfirm --clean `
    --distpath $distDir `
    --workpath (Join-Path $DevRoot "build\work")

$version = & $venvPy -c "from inyfinn_resizer import __version__; print(__version__)"

$built = Join-Path $distDir "InyfinnPhotoResizer"
$builtExe = Join-Path $built "InyfinnPhotoResizer.exe"
if (-not (Test-Path $builtExe)) {
    Write-Error "Build failed - brak $builtExe"
}

# Wdróż aplikację do BIN/ (EXE + _internal)
$binInternal = Join-Path $BinRoot "_internal"
if (Test-Path $binInternal) {
    Remove-Item $binInternal -Recurse -Force
}
$binAppExe = Join-Path $BinRoot "InyfinnPhotoResizer.exe"
if (Test-Path $binAppExe) {
    Remove-Item $binAppExe -Force
}

robocopy $built $BinRoot /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if (-not (Test-Path $binAppExe)) {
    Write-Error "Deploy failed - brak BIN\InyfinnPhotoResizer.exe"
}
if (-not (Test-Path $binInternal)) {
    Write-Error "Deploy failed - brak BIN\_internal"
}

$iconSrc = Join-Path $DevRoot "assets\icon.ico"
$iconDst = Join-Path $BinRoot "InyfinnPhotoResizer.ico"
if (Test-Path $iconSrc) {
    Copy-Item $iconSrc $iconDst -Force
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
@"
Inyfinn Photo Resizer
Wersja: $version
Typ: one-dir (BIN/)
Uruchom: InyfinnPhotoResizer.exe w korzeniu projektu
Zbudowano: $stamp
"@ | Set-Content -Path (Join-Path $BinRoot "WERSJA.txt") -Encoding UTF8

# Launcher w korzeniu (lekki onefile, uruchamia BIN\InyfinnPhotoResizer.exe)
$rootExe = Join-Path $AppRoot "InyfinnPhotoResizer.exe"
if (Test-Path $rootExe) {
    Remove-Item $rootExe -Force
}
& $venvPy -m PyInstaller (Join-Path $DevRoot "installer\inyfinn_launcher.spec") --noconfirm --clean `
    --distpath $distDir `
    --workpath (Join-Path $DevRoot "build\work-launcher")
$launcherBuilt = Join-Path $distDir "InyfinnPhotoResizer.exe"
if (-not (Test-Path $launcherBuilt)) {
    Write-Error "Launcher build failed - brak $launcherBuilt"
}
Copy-Item $launcherBuilt $rootExe -Force

& (Join-Path $DevRoot "scripts\sign_file.ps1") $binAppExe
& (Join-Path $DevRoot "scripts\sign_file.ps1") $rootExe

$binSizeMB = [math]::Round((Get-Item $binAppExe).Length / 1MB, 2)
$rootSizeMB = [math]::Round((Get-Item $rootExe).Length / 1MB, 2)
Write-Host ""
Write-Host "GOTOWE STABILNA v$version"
Write-Host "  $rootExe  (launcher ${rootSizeMB} MB)"
Write-Host "  $binAppExe  (aplikacja ${binSizeMB} MB)"
Write-Host "  $binInternal\"
Write-Host "  $(Join-Path $BinRoot 'WERSJA.txt')"
Write-Host ""

if ($Portable) {
    if (Test-Path $PortableAppDir) {
        Remove-Item $PortableAppDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $PortableAppDir | Out-Null
    robocopy $BinRoot $PortableAppDir /E /NFL /NDL /NJH /NJS /nc /ns /np `
        /XF "build.bat" | Out-Null
    # Portable = samodzielny folder (bez launcherowego korzenia)
    $portableReadme = @"
Inyfinn Photo Resizer v$version (portable, rozpakowany)

Uruchom: InyfinnPhotoResizer.exe w tym folderze.
Wymagany folder _internal obok EXE.
"@
    Set-Content -Path (Join-Path $PortableAppDir "README.txt") -Value $portableReadme -Encoding UTF8
    Write-Host "PORTABLE (rozpakowany): $PortableAppDir"
    Write-Host ""
}

if ($Launch) {
    Start-Process $rootExe
}

if ($Installer) {
    Write-Host "Budowanie instalatora (Inno Setup)..."
    & (Join-Path $DevRoot "scripts\build_installer.ps1")
}
