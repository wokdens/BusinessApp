@echo off
:: Install Wokdens Code Signing Certificate to eliminate SmartScreen warning on this laptop
:: Powered by wokdens.com

echo =======================================================
echo   Wokdens Code Signing Certificate Setup (Admin Mode)
echo =======================================================
echo.

set CER_FILE=%~dp0..\certificates\wokdens_codesign.cer

if not exist "%CER_FILE%" (
    echo [ERROR] Certificate file not found at: %CER_FILE%
    pause
    exit /b 1
)

echo Registering Wokdens Certificate into Trusted Root Certification Authorities...
certutil -addstore -f "Root" "%CER_FILE%"

echo Registering Wokdens Certificate into Trusted Publishers...
certutil -addstore -f "TrustedPublisher" "%CER_FILE%"

echo.
echo =======================================================
echo   [SUCCESS] Certificate installed!
echo   SmartScreen and Defender will now trust Wokdens apps.
echo =======================================================
echo.
pause
