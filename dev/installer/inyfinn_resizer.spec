# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — EXE na zewnątrz, biblioteki w _internal/."""

import os
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
ICON = ROOT / "assets" / "icon.ico"
PQ = ROOT / "tools" / "pngquant" / "pngquant.exe"

binaries = []
if PQ.is_file():
    binaries.append((str(PQ), os.path.join("tools", "pngquant")))

a = Analysis(
    [str(SRC / "inyfinn_resizer" / "main.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=[
        (str(SRC / "inyfinn_resizer" / "app" / "themes"), "inyfinn_resizer/app/themes"),
    ],
    hiddenimports=["pyvips", "PIL", "piexif", "watchdog", "inyfinn_resizer"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InyfinnPhotoResizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.is_file() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="InyfinnPhotoResizer",
)
