@echo off
REM Przebuduj program (EXE laduje w tym samym folderze co ten plik)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev\scripts\package_release.ps1" -Installer -Launch
pause
