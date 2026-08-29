@echo off
:: One-Click Build & Packaging Script for Wokdens BusinessApp
:: Powered by wokdens.com

echo Starting BusinessApp Build Pipeline...
.venv\Scripts\python.exe build_installer.py
pause
