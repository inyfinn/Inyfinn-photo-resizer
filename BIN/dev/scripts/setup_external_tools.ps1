#Requires -Version 5.1
# Kopiuje enkodery z PATH do BIN/dev/tools/
$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $DevRoot "tools"

function Copy-ToolExe($name, $destSubdir) {
    $src = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $src) {
        Write-Host "SKIP $name (brak w PATH)"
        return $false
    }
    $destDir = Join-Path $tools $destSubdir
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Copy-Item $src.Source (Join-Path $destDir $name) -Force
    Write-Host "OK $name -> tools\$destSubdir\"
    return $true
}

$pqSrc = "X:\Marketing\- POLSKA\99 - WYMIANA\Krzysztof\--- Moj obszar pracy\Skrypty\PS\EKSPORT WIZEK PS\tools\pngquant\pngquant.exe"
$pqDst = Join-Path $tools "pngquant\pngquant.exe"
if (-not (Test-Path $pqDst) -and (Test-Path $pqSrc)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $pqDst) | Out-Null
    Copy-Item $pqSrc $pqDst -Force
    Write-Host "OK pngquant z EKSPORT WIZEK PS"
}

Copy-ToolExe "heif-enc.exe" "heif" | Out-Null
Copy-ToolExe "avifenc.exe" "avifenc" | Out-Null
Copy-ToolExe "cwebp.exe" "cwebp" | Out-Null
Copy-ToolExe "gifsicle.exe" "gifsicle" | Out-Null

Write-Host ""
Write-Host "Opcjonalnie: choco install libavif-tools libheif"
