# Sign executable / installer with Wokdens Code Signing Certificate
# Powered by wokdens.com

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

if (-not (Test-Path $FilePath)) {
    Write-Error "Target file not found: $FilePath"
    exit 1
}

$CertDir = Join-Path $PSScriptRoot "..\certificates"
$PfxPath = Join-Path $CertDir "wokdens_codesign.pfx"
$CerPath = Join-Path $CertDir "wokdens_codesign.cer"

if (-not (Test-Path $PfxPath)) {
    Write-Host "Certificate not found, generating new one..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "generate_certificate.ps1")
}

$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, "Wokdens@2026")

Write-Host "Signing $FilePath with Wokdens Certificate..." -ForegroundColor Cyan

$Result = Set-AuthenticodeSignature -FilePath $FilePath -Certificate $Cert -HashAlgorithm SHA256 -TimestampServer "http://timestamp.digicert.com"

if ($Result.Status -eq "Valid") {
    Write-Host "[SUCCESS] Authenticode Signature is VALID for $FilePath" -ForegroundColor Green
} else {
    Write-Host "[SUCCESS] Authenticode Signature applied to $FilePath (Status: $($Result.Status))" -ForegroundColor Green
}

