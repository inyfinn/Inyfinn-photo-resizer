#Requires -Version 5.1
<#
.SYNOPSIS
  Podpisuje EXE/instalator certyfikatem Authenticode (usuwa SmartScreen po zbudowaniu reputacji).

  Zmienne środowiskowe:
    INYFINN_CODESIGN_PFX   — ścieżka do pliku .pfx
    INYFINN_CODESIGN_PASS  — hasło certyfikatu
    INYFINN_CODESIGN_TS    — opcjonalny URL timestamp (domyślnie DigiCert)
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $FilePath)) {
    Write-Error "Brak pliku: $FilePath"
}

$pfx = $env:INYFINN_CODESIGN_PFX
$pass = $env:INYFINN_CODESIGN_PASS
if (-not $pfx -or -not (Test-Path $pfx)) {
    Write-Host "Pomijam podpisywanie (brak INYFINN_CODESIGN_PFX): $FilePath"
    exit 0
}
if (-not $pass) {
    Write-Error "Ustaw INYFINN_CODESIGN_PASS dla certyfikatu PFX"
}

$signtool = @(
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
    "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
) | Get-Item -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1

if (-not $signtool) {
    $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
}
if (-not $signtool) {
    Write-Error "Brak signtool.exe — zainstaluj Windows SDK"
}

$ts = if ($env:INYFINN_CODESIGN_TS) { $env:INYFINN_CODESIGN_TS } else { "http://timestamp.digicert.com" }

& $signtool.FullName sign /f $pfx /p $pass /tr $ts /td sha256 /fd sha256 $FilePath
if ($LASTEXITCODE -ne 0) {
    Write-Error "signtool zakończył się kodem $LASTEXITCODE"
}
Write-Host "Podpisano: $FilePath"
