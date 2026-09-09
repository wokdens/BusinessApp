@echo off
setlocal EnableDelayedExpansion

:: Check Admin Rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges to register certificate...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo =======================================================
echo   Wokdens Code Signing Certificate Setup (Trusted)
echo   Powered by wokdens.com
echo =======================================================
echo.

set "CER_FILE="
if exist "%~dp0wokdens_codesign.cer" set "CER_FILE=%~dp0wokdens_codesign.cer"
if exist "%~dp0certificates\wokdens_codesign.cer" set "CER_FILE=%~dp0certificates\wokdens_codesign.cer"
if exist "%~dp0..\certificates\wokdens_codesign.cer" set "CER_FILE=%~dp0..\certificates\wokdens_codesign.cer"
if exist "wokdens_codesign.cer" set "CER_FILE=%CD%\wokdens_codesign.cer"

if not defined CER_FILE (
    echo [ERROR] Certificate file wokdens_codesign.cer not found in:
    echo %~dp0
    echo.
    pause
    exit /b 1
)

echo Found Certificate: "!CER_FILE!"
echo.
echo [1/3] Registering into Current User Trusted Publishers...
certutil -user -addstore -f "TrustedPublisher" "!CER_FILE!" >nul 2>&1

echo [2/3] Registering into Machine Trusted Root Certification Authorities...
certutil -addstore -f "Root" "!CER_FILE!" >nul 2>&1

echo [3/3] Registering into Machine Trusted Publishers...
certutil -addstore -f "TrustedPublisher" "!CER_FILE!" >nul 2>&1

echo.
echo =======================================================
echo   [SUCCESS] Wokdens Security Certificate Registered!
echo   Windows SmartScreen and Defender will now trust
echo   BusinessApp and its Installer.
echo =======================================================
echo.
pause


