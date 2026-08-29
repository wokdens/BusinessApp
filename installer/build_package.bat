@echo off
echo ===================================================
echo   Building BusinessApp (Powered by Wokdens)
echo ===================================================

echo [1/3] Cleaning previous build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q dist_installer 2>nul

echo [2/3] Compiling Python Application with PyInstaller...
..\.venv\Scripts\pyinstaller.exe --noconfirm BusinessApp.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller compilation failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Build complete in dist\BusinessApp\
echo.
echo If Inno Setup is installed, compile installer\setup_script.iss to create BusinessApp_Setup_v1.0.exe
echo ===================================================
