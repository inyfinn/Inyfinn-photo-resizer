@echo off
REM Przebuduj EXE + _internal (stabilny build; -Portable w package_release.ps1 opcjonalnie)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev\scripts\package_release.ps1" -Launch
pause
