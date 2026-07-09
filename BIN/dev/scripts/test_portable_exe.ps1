#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke-test portable one-file EXE w izolowanym folderze (bez _internal).
#>
param(
    [string]$ExePath
)

$ErrorActionPreference = "Stop"

if (-not $ExePath) {
    $AppRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $ExePath = Join-Path $AppRoot "InyfinnPhotoResizer.exe"
}
if (-not (Test-Path $ExePath)) {
    Write-Error "Brak EXE: $ExePath"
}

$iso = Join-Path $env:TEMP ("inyfinn_portable_test_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $iso | Out-Null
$copy = Join-Path $iso "InyfinnPhotoResizer.exe"
Copy-Item $ExePath $copy -Force

Write-Host "Test portable w: $iso"
$proc = Start-Process -FilePath $copy -PassThru -WorkingDirectory $iso
Start-Sleep -Seconds 4
if ($proc.HasExited) {
    Remove-Item $iso -Recurse -Force -ErrorAction SilentlyContinue
    Write-Error "EXE zakonczyl sie z kodem $($proc.ExitCode)"
}
$sizeMB = [math]::Round((Get-Item $copy).Length / 1MB, 1)
Write-Host "OK - proces dziala (PID $($proc.Id)), rozmiar ${sizeMB} MB, brak _internal obok EXE"
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Remove-Item $iso -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Smoke test PASSED"
