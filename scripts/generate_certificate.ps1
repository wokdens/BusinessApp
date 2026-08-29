# Generate Wokdens Authenticode Code Signing Certificate
# Powered by wokdens.com

$CertDir = Join-Path $PSScriptRoot "..\certificates"
if (-not (Test-Path $CertDir)) {
    New-Item -ItemType Directory -Path $CertDir -Force | Out-Null
}

$PfxPath = Join-Path $CertDir "wokdens_codesign.pfx"
$CerPath = Join-Path $CertDir "wokdens_codesign.cer"
$Password = ConvertTo-SecureString -String "Wokdens@2026" -Force -AsPlainText

Write-Host "Creating Wokdens Code Signing Certificate..." -ForegroundColor Cyan

$Cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Wokdens, O=Wokdens, OU=Software Development, E=support@wokdens.com" -KeyUsage DigitalSignature -KeySpec Signature -KeyLength 2048 -KeyAlgorithm RSA -HashAlgorithm SHA256 -NotAfter (Get-Date).AddYears(10) -CertStoreLocation "Cert:\CurrentUser\My"

Export-PfxCertificate -Cert $Cert -FilePath $PfxPath -Password $Password | Out-Null
Write-Host "Exported PFX: $PfxPath" -ForegroundColor Green

Export-Certificate -Cert $Cert -FilePath $CerPath | Out-Null
Write-Host "Exported CER: $CerPath" -ForegroundColor Green

Write-Host "Wokdens Code Signing Certificate generated successfully!" -ForegroundColor Green
