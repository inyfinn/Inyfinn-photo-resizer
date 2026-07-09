#Requires -Version 5.1
<#
.SYNOPSIS
  Instaluje wszystkie dekodery/enkodery do BIN/dev/tools/ (jak FastStone + EKSPORT WIZEK PS).

  Rdzen:     libvips/pyvips  - odczyt TIFF/JPEG/PNG, zapis WebP/AVIF/HEIC, skalowanie Lanczos
  PNG:       pngquant        - kompresja stratna PNG-8 (jak PS)
             oxipng          - optymalizacja bezstratna (fallback)
  WebP:      cwebp           - dodatkowa kompresja WebP
  AVIF:      avifenc         - enkoder AVIF
  GIF:       gifsicle        - kompresja GIF (GIF-COMPRESOR)
  TIFF CMYK: imagecodecs     - pakowane przez PyInstaller (nie ten skrypt)
#>
$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $DevRoot "tools"
$psTools = Join-Path (Split-Path -Parent (Split-Path -Parent $DevRoot)) "Skrypty\PS\EKSPORT WIZEK PS\tools"

New-Item -ItemType Directory -Force -Path $tools | Out-Null

function Ensure-Dir($path) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Copy-IfExists($src, $dst) {
    if (Test-Path $src) {
        Ensure-Dir (Split-Path $dst)
        Copy-Item $src $dst -Force
        return $true
    }
    return $false
}

function Download-ZipExe($url, $destDir, $exeName, $innerHint) {
    if (Test-Path (Join-Path $destDir $exeName)) {
        Write-Host "OK $exeName (juz jest)"
        return $true
    }
    Ensure-Dir $destDir
    $zip = Join-Path $env:TEMP ("inyfinn_" + $exeName + ".zip")
    Write-Host "Pobieram $exeName ..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    } catch {
        Write-Host "SKIP $exeName (download failed: $($_.Exception.Message))"
        return $false
    }
    $tmp = Join-Path $env:TEMP ("inyfinn_unpack_" + [guid]::NewGuid().ToString())
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $found = Get-ChildItem $tmp -Recurse -Filter $exeName -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found -and $innerHint) {
        $found = Get-ChildItem $tmp -Recurse -Filter $innerHint -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    if (-not $found) {
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "SKIP $exeName (nie znaleziono w archiwum)"
        return $false
    }
    Copy-Item $found.FullName (Join-Path $destDir $exeName) -Force
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "OK $exeName -> tools\$((Split-Path $destDir -Leaf))\"
    return $true
}

function Copy-FromPath($exeName, $destSubdir) {
    $cmd = Get-Command $exeName -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path $cmd.Source)) {
        $dst = Join-Path $tools $destSubdir
        Ensure-Dir $dst
        Copy-Item $cmd.Source (Join-Path $dst $exeName) -Force
        Write-Host "OK $exeName z PATH -> tools\$destSubdir\"
        return $true
    }
    return $false
}

Write-Host "=== Inyfinn Photo Resizer - instalacja narzedzi ===" -ForegroundColor Cyan
Write-Host ""

# 1. libvips (Lanczos, dekodowanie, enkodowanie)
& (Join-Path $PSScriptRoot "setup_libvips.ps1")

# 2. pngquant - najpierw z EKSPORT WIZEK PS, potem download
$pqDst = Join-Path $tools "pngquant\pngquant.exe"
if (-not (Test-Path $pqDst)) {
    $pqSrc = Join-Path $psTools "pngquant\pngquant.exe"
    if (Copy-IfExists $pqSrc $pqDst) {
        Write-Host "OK pngquant z EKSPORT WIZEK PS"
    } else {
        Download-ZipExe "https://pngquant.org/pngquant-windows.zip" (Join-Path $tools "pngquant") "pngquant.exe" "pngquant.exe"
    }
} else {
    Write-Host "OK pngquant (juz jest)"
}

# 3. gifsicle - jak GIF-COMPRESOR
$gifDst = Join-Path $tools "gifsicle\gifsicle.exe"
if (-not (Test-Path $gifDst)) {
    if (-not (Copy-FromPath "gifsicle.exe" "gifsicle")) {
        Download-ZipExe "https://eternallybored.org/misc/gifsicle/releases/gifsicle-1.94-win64.zip" (Join-Path $tools "gifsicle") "gifsicle.exe" "gifsicle.exe"
    }
} else {
    Write-Host "OK gifsicle (juz jest)"
}

# 4. cwebp - Google libwebp
$cwebpDst = Join-Path $tools "cwebp\cwebp.exe"
if (-not (Test-Path $cwebpDst)) {
    if (-not (Copy-FromPath "cwebp.exe" "cwebp")) {
        Download-ZipExe "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.5.0-windows-x64.zip" (Join-Path $tools "cwebp") "cwebp.exe" "cwebp.exe"
    }
} else {
    Write-Host "OK cwebp (juz jest)"
}

# 5. oxipng - bezstratny PNG
$oxDst = Join-Path $tools "oxipng\oxipng.exe"
if (-not (Test-Path $oxDst)) {
    if (-not (Copy-FromPath "oxipng.exe" "oxipng")) {
        # ostatni stabilny release oxipng win64
        Download-ZipExe "https://github.com/shssoichiro/oxipng/releases/download/v9.1.5/oxipng-9.1.5-x86_64-pc-windows-msvc.zip" (Join-Path $tools "oxipng") "oxipng.exe" "oxipng.exe"
    }
} else {
    Write-Host "OK oxipng (juz jest)"
}

# 6. avifenc - libavif
$avDst = Join-Path $tools "avifenc\avifenc.exe"
if (-not (Test-Path $avDst)) {
    if (-not (Copy-FromPath "avifenc.exe" "avifenc")) {
        Download-ZipExe "https://github.com/AOMediaCodec/libavif/releases/download/v1.4.2/windows-artifacts.zip" (Join-Path $tools "avifenc") "avifenc.exe" "avifenc.exe"
    }
} else {
    Write-Host "OK avifenc (juz jest)"
}

Write-Host ""
Write-Host "=== Podsumowanie ===" -ForegroundColor Cyan
$rows = @(
    @{ Tool = "libvips (Lanczos, TIFF/JPEG/PNG/WebP)"; Path = "tools\libvips\bin\libvips-42.dll" },
    @{ Tool = "pngquant (PNG-8)"; Path = "tools\pngquant\pngquant.exe" },
    @{ Tool = "oxipng (PNG bezstratny)"; Path = "tools\oxipng\oxipng.exe" },
    @{ Tool = "cwebp (WebP)"; Path = "tools\cwebp\cwebp.exe" },
    @{ Tool = "avifenc (AVIF)"; Path = "tools\avifenc\avifenc.exe" },
    @{ Tool = "gifsicle (GIF)"; Path = "tools\gifsicle\gifsicle.exe" }
)
foreach ($r in $rows) {
    $full = Join-Path $tools ($r.Path -replace '^tools\\', '')
    $ok = Test-Path $full
    $mark = if ($ok) { "[OK]" } else { "[--]" }
    Write-Host "$mark $($r.Tool)"
}
Write-Host ""
Write-Host "Lanczos: wbudowany w libvips (lanczos3) i Pillow fallback - osobny program nie jest potrzebny."
Write-Host "TIFF LZW/CMYK: imagecodecs + tifffile - pakowane do _internal przy build.bat"
