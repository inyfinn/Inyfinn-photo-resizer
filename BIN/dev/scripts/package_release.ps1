#Requires -Version 5.1
<#
.SYNOPSIS
  Buduje stabilna wersje one-dir w BIN/ i lekki launcher w korzeniu.
  -Portable = rozpakowany one-dir w PORTABLE/ (bez one-file 50 MB).
#>
param(
    [switch]$Launch,
    [switch]$Installer,
    [switch]$Portable,
    [switch]$Release
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
& $venvPy -m pip install -e . pyinstaller -q 3>$null

& (Join-Path $DevRoot "scripts\setup_tools.ps1")
& (Join-Path $DevRoot "scripts\setup_rmbg_models.ps1")

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
$rootIconDst = Join-Path $AppRoot "InyfinnPhotoResizer.ico"
if (Test-Path $iconSrc) {
    Copy-Item $iconSrc $iconDst -Force
    Copy-Item $iconSrc $rootIconDst -Force
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
@"
Inyfinn Photo Resizer
Wersja: $version
Typ: one-dir (BIN/)
Uruchom: InyfinnPhotoResizer.exe w korzeniu projektu
Zbudowano: $stamp
"@ | Set-Content -Path (Join-Path $BinRoot "WERSJA.txt") -Encoding UTF8

# Launcher w korzeniu (najpierw .NET, fallback PyInstaller)
$rootExe = Join-Path $AppRoot "InyfinnPhotoResizer.exe"
if (Test-Path $rootExe) {
    Remove-Item $rootExe -Force
}
$launcherBuilt = $null
$launcherProj = Join-Path $DevRoot "launcher\InyfinnLauncher.csproj"
$launcherOut = Join-Path $DevRoot "build\launcher"
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    try {
        dotnet publish $launcherProj -c Release -o $launcherOut --nologo -v q 2>$null
        $candidate = Join-Path $launcherOut "InyfinnPhotoResizer.exe"
        if (Test-Path $candidate) { $launcherBuilt = $candidate }
    } catch {}
}
if (-not $launcherBuilt) {
    $csc = Join-Path ${env:WINDIR} "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    $netfxSrc = Join-Path $DevRoot "launcher\Program.NetFx.cs"
    $netfxOut = Join-Path $DevRoot "build\launcher-netfx"
    if ((Test-Path $csc) -and (Test-Path $netfxSrc)) {
        New-Item -ItemType Directory -Force -Path $netfxOut | Out-Null
        $netfxExe = Join-Path $netfxOut "InyfinnPhotoResizer.exe"
        $iconArg = ""
        if (Test-Path $iconSrc) {
            $iconArg = "/win32icon:$iconSrc"
        }
        & $csc /nologo /target:winexe /out:$netfxExe $iconArg `
            /reference:System.dll `
            /reference:System.Windows.Forms.dll `
            $netfxSrc
        if ($LASTEXITCODE -eq 0 -and (Test-Path $netfxExe)) {
            $launcherBuilt = $netfxExe
            Write-Host "Launcher .NET Framework (szybki): $netfxExe"
        }
    }
}
if (-not $launcherBuilt) {
    & $venvPy -m PyInstaller (Join-Path $DevRoot "installer\inyfinn_launcher.spec") --noconfirm --clean `
        --distpath $distDir `
        --workpath (Join-Path $DevRoot "build\work-launcher")
    $candidate = Join-Path $distDir "InyfinnPhotoResizer.exe"
    if (Test-Path $candidate) { $launcherBuilt = $candidate }
}
if (-not $launcherBuilt) {
    Write-Error "Launcher build failed"
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

if ($Release) {
    $releaseDir = Join-Path $AppRoot "release"
    New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
    $zipName = "InyfinnPhotoResizer-v$version.zip"
    $zipPath = Join-Path $releaseDir $zipName
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    $staging = Join-Path $releaseDir "_staging"
    if (Test-Path $staging) {
        cmd /c "rd /s /q `"$staging`"" 2>$null
        if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
    }
    New-Item -ItemType Directory -Force -Path $staging | Out-Null

    # Tylko pliki runtime (bez BIN/dev, .venv, duplikatów modeli)
    $rootExe = Join-Path $AppRoot "InyfinnPhotoResizer.exe"
    if (Test-Path $rootExe) { Copy-Item $rootExe (Join-Path $staging "InyfinnPhotoResizer.exe") -Force }
    $rootIco = Join-Path $AppRoot "InyfinnPhotoResizer.ico"
    if (Test-Path $rootIco) { Copy-Item $rootIco (Join-Path $staging "InyfinnPhotoResizer.ico") -Force }
    $binStaging = Join-Path $staging "BIN"
    New-Item -ItemType Directory -Force -Path $binStaging | Out-Null
    foreach ($item in @("InyfinnPhotoResizer.exe", "InyfinnPhotoResizer.ico", "WERSJA.txt")) {
        $src = Join-Path $BinRoot $item
        if (Test-Path $src) { Copy-Item $src (Join-Path $binStaging $item) -Force }
    }
    $internalSrc = Join-Path $BinRoot "_internal"
    if (Test-Path $internalSrc) {
        robocopy $internalSrc (Join-Path $binStaging "_internal") /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    }

    $readme = @"
Inyfinn Photo Resizer v$version

Uruchom: InyfinnPhotoResizer.exe w korzeniu tego folderu.
Aplikacja: BIN\InyfinnPhotoResizer.exe + BIN\_internal\

Skala: suwak pod Jakością (np. 50% = połowa wymiarów).
Min. najdłuższa krawędź: domyślnie 1080 px (włączone).
Usuwanie tła: modele BiRefNet w BIN\_internal\tools\rmbg\

Zbudowano: $stamp
"@
    Set-Content -Path (Join-Path $staging "README.txt") -Value $readme -Encoding UTF8
    Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -Force
    cmd /c "rd /s /q `"$staging`"" 2>$null
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
    $zipMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
    Write-Host "RELEASE ZIP: $zipPath (${zipMb} MB)"
    Write-Host ""
}
