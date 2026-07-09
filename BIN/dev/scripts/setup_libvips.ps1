# Pobiera libvips win64 (web) do dev/tools/libvips — wymagane przez pyvips w EXE.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root "tools\libvips"
$version = "8.18.3"
$zipName = "vips-dev-x64-web-$version.zip"
$url = "https://github.com/libvips/build-win64-mxe/releases/download/v$version/$zipName"
$tmpZip = Join-Path $env:TEMP $zipName

if ((Test-Path (Join-Path $dest "bin\vips-42.dll")) -or (Test-Path (Join-Path $dest "bin\libvips-42.dll"))) {
    Write-Host "OK libvips juz jest w tools\libvips"
    exit 0
}

Write-Host "Pobieram libvips $version..."
Invoke-WebRequest -Uri $url -OutFile $tmpZip -UseBasicParsing

if (Test-Path $dest) {
    Remove-Item $dest -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Expand-Archive -Path $tmpZip -DestinationPath $dest -Force
Remove-Item $tmpZip -Force

# Zip ma podfolder vips-dev-x64-web-8.18.3 — spłaszcz do tools/libvips
$nested = Get-ChildItem $dest -Directory | Select-Object -First 1
if ($nested -and (Test-Path (Join-Path $nested.FullName "bin"))) {
    Get-ChildItem $nested.FullName | ForEach-Object {
        Move-Item $_.FullName (Join-Path $dest $_.Name) -Force
    }
    Remove-Item $nested.FullName -Recurse -Force
}

$dll = Get-ChildItem (Join-Path $dest "bin") -Filter "*vips*42*.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $dll) {
    Write-Error "libvips unpack failed - brak vips-42.dll w $dest\bin"
}
Write-Host "OK libvips w $dest"
