#Requires -Version 5.1
<#
.SYNOPSIS
  Podpisuje EXE/instalator Authenticode (SHA256).

  1) INYFINN_CODESIGN_PFX + INYFINN_CODESIGN_PASS — certyfikat komercyjny (OV/EV).
  2) W przeciwnym razie trwały self-signed CN=Inyfinn Photo Resizer w CurrentUser\My
     + publiczny cert w TrustedPublisher (ta stacja: SmartScreen nie krzyczy „Nieznany wydawca”).

  Bez OV/EV nowy wydawca i tak zbiera reputację SmartScreen u obcych użytkowników.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $FilePath)) {
    Write-Error "Brak pliku: $FilePath"
}

$Subject = "CN=Inyfinn Photo Resizer, O=Inyfinn"
$TimestampUrl = if ($env:INYFINN_CODESIGN_TS) { $env:INYFINN_CODESIGN_TS } else { "http://timestamp.digicert.com" }

function Get-CommercialCert {
    $pfx = $env:INYFINN_CODESIGN_PFX
    if (-not $pfx -or -not (Test-Path -LiteralPath $pfx)) {
        return $null
    }
    $pass = $env:INYFINN_CODESIGN_PASS
    if (-not $pass) {
        Write-Error "Ustaw INYFINN_CODESIGN_PASS dla certyfikatu PFX"
    }
    $secure = ConvertTo-SecureString -String $pass -AsPlainText -Force
    return New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfx, $secure)
}

function Get-OrCreateLocalCodeCert {
    $existing = @(Get-ChildItem Cert:\CurrentUser\My -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Subject -eq $Subject -and
            $_.HasPrivateKey -and
            $_.NotAfter -gt (Get-Date).AddDays(14)
        } | Sort-Object NotAfter -Descending)
    if ($existing.Count -gt 0) {
        return $existing[0]
    }
    return New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $Subject `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyExportPolicy Exportable `
        -KeySpec Signature `
        -HashAlgorithm SHA256 `
        -NotAfter (Get-Date).AddYears(5) `
        -FriendlyName "Inyfinn Photo Resizer code signing"
}

function Install-LocalTrust([System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert) {
    $pub = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $pub.Import($Cert.RawData)
    # Tylko TrustedPublisher — Root wyświetla modal Windows i wiesza nienadzorowany build.
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPublisher", "CurrentUser")
    try {
        $store.Open("ReadWrite")
        $store.Add($pub)
    } finally {
        $store.Close()
    }
}

function Invoke-SignTool([string]$Target, [string]$PfxPath, [string]$Password) {
    $tool = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
    ) | Get-Item -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $tool) {
        $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
        if ($cmd) { $tool = Get-Item $cmd.Source }
    }
    if (-not $tool) {
        return $false
    }
    & $tool.FullName sign /f $PfxPath /p $Password /tr $TimestampUrl /td sha256 /fd sha256 $Target
    return ($LASTEXITCODE -eq 0)
}

$cert = Get-CommercialCert
$usedLocal = $false
if (-not $cert) {
    $cert = Get-OrCreateLocalCodeCert
    $usedLocal = $true
}

Install-LocalTrust $cert

$workPath = $FilePath
$tempCopy = $null
$attrs = (Get-Item -LiteralPath $FilePath).Attributes.ToString()
if ($attrs -match "ReparsePoint") {
    $tempCopy = Join-Path $env:TEMP ("inyfinn-sign-" + [guid]::NewGuid().ToString() + [IO.Path]::GetExtension($FilePath))
    Copy-Item -LiteralPath $FilePath -Destination $tempCopy -Force
    $workPath = $tempCopy
}

$signed = $false
$pfxEnv = $env:INYFINN_CODESIGN_PFX
if ($pfxEnv -and (Test-Path -LiteralPath $pfxEnv) -and $env:INYFINN_CODESIGN_PASS) {
    $signed = Invoke-SignTool $workPath $pfxEnv $env:INYFINN_CODESIGN_PASS
}

if (-not $signed) {
    $sig = Set-AuthenticodeSignature -FilePath $workPath -Certificate $cert -TimestampServer $TimestampUrl -HashAlgorithm SHA256
    if (-not $sig.SignerCertificate) {
        $sig = Set-AuthenticodeSignature -FilePath $workPath -Certificate $cert -HashAlgorithm SHA256
    }
    if (-not $sig.SignerCertificate) {
        Write-Error "Podpis Authenticode nie został zapisany: $($sig.StatusMessage)"
    }
}

if ($tempCopy) {
    Copy-Item -LiteralPath $tempCopy -Destination $FilePath -Force
    Remove-Item -LiteralPath $tempCopy -Force -ErrorAction SilentlyContinue
}

$ErrorActionPreference = "Continue"
Unblock-File -LiteralPath $FilePath -ErrorAction SilentlyContinue

$check = Get-AuthenticodeSignature -FilePath $FilePath
# Self-signed: Status=UnknownError (łańcuch bez zaufanego root), ale SignerCertificate jest.
# NotSigned na D:\Marketing = reparse/uszkodzony PE — nie mylić z brakiem próby podpisu.
if (-not $check.SignerCertificate) {
    Write-Error "Plik nadal niepodpisany: $FilePath ($($check.StatusMessage))"
}
# HashMismatch = plik zmienił się po podpisie (np. kopia przez zsynchronizowany D:\) — podpis nieważny.
$okStatus = @("Valid")
if ($usedLocal) { $okStatus += "UnknownError" }
if ($okStatus -notcontains $check.Status.ToString()) {
    Write-Error "Podpis nieważny ($($check.Status)): $FilePath - $($check.StatusMessage)"
}

$kind = if ($usedLocal) { "lokalny Inyfinn (TrustedPublisher na tej stacji)" } else { "PFX" }
Write-Host "Podpisano ($kind, $($check.Status)): $FilePath"
