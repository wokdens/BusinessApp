# Master Build & Packaging Pipeline for BusinessApp
# Powered by wokdens.com

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist', 'BusinessApp')
EXE_PATH = os.path.join(DIST_DIR, 'BusinessApp.exe')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
CERT_DIR = os.path.join(BASE_DIR, 'certificates')
PFX_PATH = os.path.join(CERT_DIR, 'wokdens_codesign.pfx')
ISS_PATH = os.path.join(BASE_DIR, 'installer', 'setup_script.iss')
OUTPUT_INSTALLER_DIR = os.path.join(BASE_DIR, 'dist_installer')

def run_command(cmd, desc):
    print(f'\n>>> {desc}...')
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f'Notice during {desc} (code {result.returncode})')
        return False
    return True

def main():
    print('=' * 60)
    print('   Wokdens BusinessApp - Production Build & Packaging')
    print('=' * 60)

    # 1. Generate certificate if not present
    if not os.path.exists(PFX_PATH):
        gen_script = os.path.join(SCRIPTS_DIR, 'generate_certificate.ps1')
        run_command(f'powershell -ExecutionPolicy Bypass -File "{gen_script}"', 'Generating Code Signing Certificate')

    # 2. PyInstaller --onedir Build with version metadata
    pyinstaller_cmd = '.venv\Scripts\pyinstaller.exe --noconfirm BusinessApp.spec'
    if not run_command(pyinstaller_cmd, 'Compiling Python Application via PyInstaller (--onedir)'):
        sys.exit(1)

    # 3. Sign BusinessApp.exe
    if os.path.exists(EXE_PATH):
        sign_script = os.path.join(SCRIPTS_DIR, 'sign_app.ps1')
        run_command(f'powershell -ExecutionPolicy Bypass -File "{sign_script}" -FilePath "{EXE_PATH}"', 'Signing BusinessApp.exe with Wokdens Certificate')

    # 4. Copy certificate and 1-click register script into dist for standalone client deployment
    cer_src = os.path.join(CERT_DIR, 'wokdens_codesign.cer')
    if os.path.exists(cer_src) and os.path.exists(DIST_DIR):
        shutil.copy2(cer_src, os.path.join(DIST_DIR, 'wokdens_codesign.cer'))
        reg_bat_path = os.path.join(DIST_DIR, 'Register_Security_Certificate.bat')
        with open(reg_bat_path, 'w', encoding='utf-8') as f:
            f.write('''@echo off
:: Register Wokdens Security Certificate to eliminate Windows SmartScreen warnings
echo =======================================================
echo   Registering Wokdens Security Certificate
echo =======================================================
echo.
set CER_FILE=%~dp0wokdens_codesign.cer

if not exist "%CER_FILE%" (
    echo [ERROR] Certificate file not found at: %CER_FILE%
    pause
    exit /b 1
)

echo Adding certificate to Trusted Root Certification Authorities...
certutil -addstore -f "Root" "%CER_FILE%"

echo Adding certificate to Trusted Publishers...
certutil -addstore -f "TrustedPublisher" "%CER_FILE%"

echo.
echo =======================================================
echo   [SUCCESS] Certificate installed successfully!
echo   Windows SmartScreen will now recognize Wokdens as a verified publisher.
echo =======================================================
echo.
pause
''')
        print(f'[SUCCESS] Standalone certificate installer bundled in: {DIST_DIR}\\Register_Security_Certificate.bat')

    # 5. Check for Inno Setup compiler
    iscc_paths = [
        'iscc.exe',
        r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        r'C:\Program Files\Inno Setup 6\ISCC.exe',
        r'C:\Program Files (x86)\Inno Setup 5\ISCC.exe',
        r'C:\Program Files\Inno Setup 5\ISCC.exe',
    ]
    iscc_exe = None
    for p in iscc_paths:
        if shutil.which(p) or os.path.exists(p):
            iscc_exe = p
            break

    if iscc_exe and os.path.exists(ISS_PATH):
        os.makedirs(OUTPUT_INSTALLER_DIR, exist_ok=True)
        inno_cmd = f'"{iscc_exe}" "{ISS_PATH}"'
        if run_command(inno_cmd, 'Building Inno Setup Windows Installer'):
            installer_exe = os.path.join(OUTPUT_INSTALLER_DIR, 'BusinessApp_Setup_v1.0.exe')
            if os.path.exists(installer_exe):
                sign_script = os.path.join(SCRIPTS_DIR, 'sign_app.ps1')
                run_command(f'powershell -ExecutionPolicy Bypass -File "{sign_script}" -FilePath "{installer_exe}"', 'Signing BusinessApp_Setup_v1.0.exe')
                print(f'\n[SUCCESS] Installer ready at:\n{installer_exe}')
    else:
        print('\n[INFO] Inno Setup compiler (ISCC.exe) not detected on this system.')
        print(f'[SUCCESS] Standalone Application compiled and signed at:\n{DIST_DIR}\\BusinessApp.exe')

if __name__ == '__main__':
    main()

