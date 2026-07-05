# Setup bundled tools (pngquant, gifsicle)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$psTools = "X:\Marketing\- POLSKA\99 - WYMIANA\Krzysztof\--- Moj obszar pracy\Skrypty\PS\EKSPORT WIZEK PS\tools"

if (Test-Path "$psTools\pngquant\pngquant.exe") {
    New-Item -ItemType Directory -Force -Path "$root\tools\pngquant" | Out-Null
    Copy-Item "$psTools\pngquant\pngquant.exe" "$root\tools\pngquant\" -Force
    Write-Host "OK pngquant"
}

Write-Host "Optional: download gifsicle from https://eternallyconfuzzled.com/tuts/gifsicle/gifsicle-1.94-win64.zip"
Write-Host "Optional: libvips win64 from https://github.com/libvips/build-win64-mxe/releases"
