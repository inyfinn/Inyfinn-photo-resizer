#Requires -Version 5.1
<#
  Bezpieczny odpowiednik package_release.ps1 -Installer -Release dla agenta (pierwszy raz uzyty przy 2.6.7):
  ta sama sekwencja, ale BEZ kasowania rekurencyjnego - stare katalogi sa PRZENOSZONE do build\_old-<stamp>\,
  pliki tymczasowe zostaja w %TEMP% (unikalne nazwy), PyInstaller dostaje swiezy katalog cache zamiast --clean.
  Uzycie (po podbiciu wersji i testach): package_release_safe.ps1 -Stage build | installer | zip  (kolejno, ten sam -Stamp).
  Launcher w korzeniu projektu zostaje (rebuild tylko gdy zmienil sie kod launcher\). Stare pliki setup i ZIP-y nie sa ruszane.
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet("build", "installer", "zip")][string]$Stage,
    [string]$Stamp = ""
)
$ErrorActionPreference = "Stop"
$Dev = 'D:\Marketing\- POLSKA\99 - WYMIANA\Krzysztof\--- Moj obszar pracy\Inyfinn Image resizer\BIN\dev'
$Bin = Split-Path -Parent $Dev
$App = Split-Path -Parent $Bin
$py = Join-Path $Dev '.venv\Scripts\python.exe'
$env:PYTHONPATH = Join-Path $Dev 'src'
if (-not $Stamp) { $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss' }
$stateFile = Join-Path $env:TEMP "inyf-build-267.state.txt"
$version = (& $py -c "from inyfinn_resizer import __version__; print(__version__)").Trim()
Write-Host "Wersja: $version  Stage: $Stage  Stamp: $Stamp"

$dist = Join-Path $Dev 'build\dist'
$work = Join-Path $Dev 'build\work'
$built = Join-Path $dist 'InyfinnPhotoResizer'
$builtExe = Join-Path $built 'InyfinnPhotoResizer.exe'
$binExe = Join-Path $Bin 'InyfinnPhotoResizer.exe'
$binInternal = Join-Path $Bin '_internal'
$rootExe = Join-Path $App 'InyfinnPhotoResizer.exe'

function Assert-Signed([string]$Path) {
    $sig = Get-AuthenticodeSignature -FilePath $Path
    if (-not $sig.SignerCertificate) { throw "Brak podpisu: $Path ($($sig.StatusMessage))" }
    $st = $sig.Status.ToString()
    if (@("Valid", "UnknownError") -notcontains $st) { throw "Podpis niewazny ($st): $Path" }
    Write-Host ("  podpis OK ({0}): {1}" -f $st, $Path)
}

function Sign-OnLocalCopy([string]$Path, [string]$Dir) {
    # podpis na dysku C: (D:\Marketing to reparse/sync - podpis wprost na D: bywa HashMismatch), potem zwykla kopia
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    $copy = Join-Path $Dir ([IO.Path]::GetFileName($Path))
    Copy-Item -LiteralPath $Path -Destination $copy -Force
    & (Join-Path $Dev 'scripts\sign_file.ps1') $copy
    return $copy
}

if ($Stage -eq "build") {
    $old = Join-Path $Dev "build\_old-$Stamp"
    New-Item -ItemType Directory -Force -Path $old | Out-Null
    $procs = @(Get-Process InyfinnPhotoResizer -ErrorAction SilentlyContinue)
    foreach ($p in $procs) { [void]$p.CloseMainWindow() }
    if ($procs.Count -gt 0) {
        Start-Sleep -Seconds 8
        Get-Process InyfinnPhotoResizer -ErrorAction SilentlyContinue | Stop-Process -Force
    }
    # przeniesienie na bok zamiast kasowania
    foreach ($pair in @(@($dist, 'dist'), @($work, 'work'), @($binInternal, 'BIN_internal'))) {
        if (Test-Path -LiteralPath $pair[0]) {
            Move-Item -LiteralPath $pair[0] -Destination (Join-Path $old $pair[1])
            Write-Host "Przeniesiono: $($pair[0]) -> $old\$($pair[1])"
        }
    }
    if (Test-Path -LiteralPath $binExe) {
        Move-Item -LiteralPath $binExe -Destination (Join-Path $old 'BIN_InyfinnPhotoResizer.exe')
    }
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $env:TEMP "pyi-cache-$Stamp"
    Set-Location $Dev
    & $py -m PyInstaller (Join-Path $Dev 'installer\inyfinn_resizer.spec') --noconfirm --distpath $dist --workpath $work
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller: kod $LASTEXITCODE" }
    if (-not (Test-Path -LiteralPath $builtExe)) { throw "Build failed - brak $builtExe" }

    $signed = Sign-OnLocalCopy $builtExe (Join-Path $env:TEMP "inyf-sign-$Stamp")
    Copy-Item -LiteralPath $signed -Destination $builtExe -Force
    robocopy $built $Bin /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy: kod $LASTEXITCODE" }
    Copy-Item -LiteralPath $signed -Destination $binExe -Force
    if (-not (Test-Path -LiteralPath $binInternal)) { throw "Deploy failed - brak BIN\_internal" }
    if ((Get-FileHash -LiteralPath $builtExe).Hash -ne (Get-FileHash -LiteralPath $binExe).Hash) { throw "Hash EXE: dist != BIN" }
    Assert-Signed $builtExe
    Assert-Signed $binExe

    $stampText = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    @"
Inyfinn Photo Resizer
Wersja: $version
Typ: one-dir (BIN/)
Uruchom: InyfinnPhotoResizer.exe w korzeniu projektu
Zbudowano: $stampText
"@ | Set-Content -Path (Join-Path $Bin "WERSJA.txt") -Encoding UTF8
    Assert-Signed $rootExe   # launcher w korzeniu zostaje (kod launchera bez zmian od 2.6.6)
    Set-Content -Path $stateFile -Value "$Stamp|$stampText" -Encoding UTF8
    $mb = [math]::Round((Get-Item -LiteralPath $binExe).Length / 1MB, 2)
    Write-Host "BUILD GOTOWY v$version  EXE ${mb} MB  $binExe"
}

if ($Stage -eq "installer") {
    $iscc = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
    if (-not (Test-Path -LiteralPath $iscc)) { throw "Brak ISCC: $iscc" }
    $outDir = Join-Path $Dev 'installer-output'
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $isccOut = Join-Path $env:TEMP "inyf-installer-$Stamp"
    New-Item -ItemType Directory -Force -Path $isccOut | Out-Null
    & $iscc "/O$isccOut" (Join-Path $Dev 'installer\inyfinn_resizer.iss')
    if ($LASTEXITCODE -ne 0) { throw "ISCC: kod $LASTEXITCODE" }
    $name = "InyfinnPhotoResizer-$version-setup.exe"
    $compiled = Join-Path $isccOut $name
    if (-not (Test-Path -LiteralPath $compiled)) { throw "Brak $compiled" }
    & (Join-Path $Dev 'scripts\sign_file.ps1') $compiled
    $size = (Get-Item -LiteralPath $compiled).Length
    Write-Host ("Rozmiar setupu: {0:N0} B" -f $size)
    if ($size -gt 2000000000) { throw "Setup przekracza 2 000 000 000 B" }
    $target = Join-Path $outDir $name
    Copy-Item -LiteralPath $compiled -Destination $target -Force
    if ((Get-FileHash -LiteralPath $compiled).Hash -ne (Get-FileHash -LiteralPath $target).Hash) { throw "Hash setupu: temp != installer-output" }
    Assert-Signed $target
    Write-Host "INSTALATOR GOTOWY: $target"
}

if ($Stage -eq "zip") {
    $releaseDir = Join-Path $App 'release'
    New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
    $zipName = "InyfinnPhotoResizer-v$version.zip"
    $zipPath = Join-Path $releaseDir $zipName
    if (Test-Path -LiteralPath $zipPath) { throw "Juz istnieje: $zipPath (nie nadpisuje)" }
    $tempRoot = Join-Path $env:TEMP "inyf-release-$Stamp"
    $staging = Join-Path $tempRoot "staging"
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    Copy-Item -LiteralPath $rootExe -Destination (Join-Path $staging 'InyfinnPhotoResizer.exe') -Force
    $rootIco = Join-Path $App 'InyfinnPhotoResizer.ico'
    if (Test-Path -LiteralPath $rootIco) { Copy-Item -LiteralPath $rootIco -Destination (Join-Path $staging 'InyfinnPhotoResizer.ico') -Force }
    $binStaging = Join-Path $staging 'BIN'
    New-Item -ItemType Directory -Force -Path $binStaging | Out-Null
    foreach ($item in @('InyfinnPhotoResizer.exe', 'InyfinnPhotoResizer.ico', 'WERSJA.txt')) {
        $src = Join-Path $Bin $item
        if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination (Join-Path $binStaging $item) -Force }
    }
    robocopy $binInternal (Join-Path $binStaging '_internal') /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy: kod $LASTEXITCODE" }
    $stampText = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $readme = @"
Inyfinn Photo Resizer v$version

Uruchom: InyfinnPhotoResizer.exe w korzeniu tego folderu.
Aplikacja: BIN\InyfinnPhotoResizer.exe + BIN\_internal\

Skala: suwak pod Jakością (np. 50% = połowa wymiarów).
Min. najdłuższa krawędź: opcjonalna, domyślnie wyłączona.
Własny format: zaznacz i podaj szerokość x wysokość.
Kadr: róża wiatrów wybiera punkt odniesienia przycięcia.
Usuwanie tła: model pobiera się przy pierwszym użyciu (214 MB lub 928 MB)
do %LOCALAPPDATA%\Inyfinn\PhotoResizer\rmbg\
Filmy (MP4, MOV, WebM) → GIF: Ustawienia GIF — tryb, liczba klatek, szerokość.

Program korzysta z ffmpeg 7.1 (build gyan.dev, licencja GPL v3).
Kod źródłowy ffmpeg: https://ffmpeg.org/download.html

Zbudowano: $stampText
"@
    Set-Content -Path (Join-Path $staging 'README.txt') -Value $readme -Encoding UTF8
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $tempZip = Join-Path $tempRoot $zipName
    [System.IO.Compression.ZipFile]::CreateFromDirectory($staging, $tempZip, [System.IO.Compression.CompressionLevel]::Optimal, $false)
    Copy-Item -LiteralPath $tempZip -Destination $zipPath
    if ((Get-FileHash -LiteralPath $tempZip).Hash -ne (Get-FileHash -LiteralPath $zipPath).Hash) { throw "ZIP: temp != release" }
    $zipMb = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1MB, 1)
    Write-Host "RELEASE ZIP: $zipPath (${zipMb} MB)  staging zostaje w $tempRoot"
}
