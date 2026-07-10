#Requires -Version 5.1
<#
.SYNOPSIS
  Pobiera modele BiRefNet dla rembg (usuwanie tła) do BIN/dev/tools/rmbg/.
#>
$ErrorActionPreference = "Stop"
$DevRoot = Split-Path -Parent $PSScriptRoot
$modelsDir = Join-Path $DevRoot "tools\rmbg"
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$baseUrl = "https://github.com/danielgatis/rembg/releases/download/v0.0.0"
$models = @(
    @{
        Name = "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx"
        Label = "birefnet-general-lite"
    },
    @{
        Name = "BiRefNet-general-epoch_244.onnx"
        Label = "birefnet-general"
    }
)

Write-Host "=== Inyfinn Photo Resizer - modele usuwania tla ===" -ForegroundColor Cyan
Write-Host ""

foreach ($model in $models) {
    $dest = Join-Path $modelsDir $model.Name
    if (Test-Path $dest) {
        $sizeMb = [math]::Round((Get-Item $dest).Length / 1MB, 1)
        Write-Host "OK $($model.Label) ($sizeMb MB)"
        continue
    }
    $url = "$baseUrl/$($model.Name)"
    Write-Host "Pobieram $($model.Label) ..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        $sizeMb = [math]::Round((Get-Item $dest).Length / 1MB, 1)
        Write-Host "OK $($model.Label) -> tools\rmbg\$($model.Name) ($sizeMb MB)"
    } catch {
        Write-Error "Nie udalo sie pobrac $($model.Name): $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "Modele w: $modelsDir" -ForegroundColor Green
