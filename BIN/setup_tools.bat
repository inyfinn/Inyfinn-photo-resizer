@echo off
REM Instalacja dekoderow/enkoderow (libvips, pngquant, gifsicle, cwebp, oxipng, avifenc)
cd /d "%~dp0dev"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev\scripts\setup_tools.ps1"
pause
