#Requires -Version 5.1
<#
.SYNOPSIS
  Pobiera modele BiRefNet dla rembg (usuwanie tla) do BIN/dev/tools/rmbg/ - tylko do testow dev.
  Instalator ich NIE zawiera (od 2.4.8): aplikacja pobiera je przy pierwszym uzyciu "Usun tlo".
  Nazwy i SHA256 musza byc zgodne z core/transforms/rmbg_models.py.
#>
$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$modelsDir = Join-Path $DevRoot "tools\rmbg"
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$baseUrl = "https://github.com/danielgatis/rembg/releases/download/v0.0.0"
$models = @(
    @{
        Source = "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx"
        Name = "birefnet-general-lite.onnx"
        Sha256 = "5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333"
    },
    @{
        Source = "BiRefNet-general-epoch_244.onnx"
        Name = "birefnet-general.onnx"
        Sha256 = "58f621f00f5d756097615970a88a791584600dcf7c45b18a0a6267535a1ebd3c"
    }
)

Write-Host "=== Inyfinn Photo Resizer - modele usuwania tla (dev) ===" -ForegroundColor Cyan

foreach ($model in $models) {
    $dest = Join-Path $modelsDir $model.Name
    if (Test-Path -LiteralPath $dest) {
        $hash = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()
        if ($hash -eq $model.Sha256) {
            Write-Host "OK $($model.Name)"
            continue
        }
        Write-Host "Zla suma kontrolna $($model.Name) - pobieram ponownie" -ForegroundColor Yellow
    }
    $part = "$dest.part"
    Write-Host "Pobieram $($model.Name) ..."
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri "$baseUrl/$($model.Source)" -OutFile $part -UseBasicParsing
    $hash = (Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $model.Sha256) {
        Remove-Item -LiteralPath $part -Force
        Write-Error "Zla suma kontrolna pobranego $($model.Name): $hash"
    }
    Move-Item -LiteralPath $part -Destination $dest -Force
    Write-Host "OK $($model.Name)"
}

Write-Host "Modele w: $modelsDir" -ForegroundColor Green
