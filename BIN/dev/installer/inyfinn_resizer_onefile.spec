# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — jeden plik EXE (portable, bez _internal)."""

import os
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
ICON = ROOT / "assets" / "icon.ico"
TOOLS = ROOT / "tools"

# Pillow AVIF (~8 MB) — problemy z UPX/dekompresją w onefile; AVIF obsługuje pyvips/avifenc.
SKIP_PIL_BINARIES = ("_avif.", "_imagingtk.")


def _filter_binaries(binaries):
    out = []
    for item in binaries:
        src = item[0]
        name = os.path.basename(src).lower()
        if any(marker in name for marker in SKIP_PIL_BINARIES):
            continue
        out.append(item)
    return out


binaries = []
datas = [
    (str(SRC / "inyfinn_resizer" / "app" / "themes"), "inyfinn_resizer/app/themes"),
]
if ICON.is_file():
    datas.append((str(ICON), "."))

# Narzędzia kompresji — opcjonalne, pakowane gdy istnieją w dev/tools/
for folder, arc_prefix in [
    ("pngquant", "tools/pngquant"),
    ("gifsicle", "tools/gifsicle"),
    ("cwebp", "tools/cwebp"),
    ("oxipng", "tools/oxipng"),
    ("avifenc", "tools/avifenc"),
]:
    tool_dir = TOOLS / folder
    if not tool_dir.is_dir():
        continue
    for item in tool_dir.iterdir():
        if item.is_file():
            binaries.append((str(item), arc_prefix))

# libvips (opcjonalnie — gdy ręcznie dodany do tools/libvips)
libvips = TOOLS / "libvips"
if libvips.is_dir():
    for item in libvips.rglob("*"):
        if item.is_file():
            rel = item.relative_to(libvips)
            binaries.append((str(item), str(Path("tools/libvips") / rel.parent).replace("\\", "/")))

a = Analysis(
    [str(SRC / "inyfinn_resizer" / "main.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
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
a.binaries = _filter_binaries(a.binaries)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="InyfinnPhotoResizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.is_file() else None,
)
