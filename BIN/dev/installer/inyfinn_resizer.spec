# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — EXE na zewnątrz, biblioteki w _internal/."""

import os
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
ICON = ROOT / "assets" / "icon.ico"
PQ = TOOLS / "pngquant" / "pngquant.exe"
GIF = TOOLS / "gifsicle" / "gifsicle.exe"

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


def _collect_tool_binaries():
    out = []
    if PQ.is_file():
        out.append((str(PQ), os.path.join("tools", "pngquant")))
    if GIF.is_file():
        out.append((str(GIF), os.path.join("tools", "gifsicle")))
    for folder, arc_prefix in [
        ("cwebp", "tools/cwebp"),
        ("oxipng", "tools/oxipng"),
        ("avifenc", "tools/avifenc"),
    ]:
        tool_dir = TOOLS / folder
        if not tool_dir.is_dir():
            continue
        for item in tool_dir.iterdir():
            if item.is_file():
                out.append((str(item), arc_prefix))
    libvips = TOOLS / "libvips"
    if libvips.is_dir():
        for item in libvips.rglob("*"):
            if item.is_file():
                rel = item.relative_to(libvips)
                out.append(
                    (str(item), str(Path("tools/libvips") / rel.parent).replace("\\", "/"))
                )
    return out


def _collect_imagecodecs_binaries():
    """PyInstaller nie zbiera .pyd imagecodecs — bez tego brak lzw_decode dla TIFF."""
    out = []
    try:
        import imagecodecs

        pkg = Path(imagecodecs.__file__).resolve().parent
        for pyd in pkg.glob("*.pyd"):
            out.append((str(pyd), "imagecodecs"))
    except ImportError:
        pass
    return out


binaries = _collect_tool_binaries() + _collect_imagecodecs_binaries()

a = Analysis(
    [str(SRC / "inyfinn_resizer" / "main.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=[
        (str(SRC / "inyfinn_resizer" / "app" / "themes"), "inyfinn_resizer/app/themes"),
    ],
    hiddenimports=[
        "pyvips",
        "PIL",
        "piexif",
        "watchdog",
        "inyfinn_resizer",
        "numpy",
        "tifffile",
        "imagecodecs",
        "imagecodecs._imcd",
        "imagecodecs._tiff",
        "imagecodecs._shared",
        "pillow_heif",
    ],
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
    [],
    exclude_binaries=True,
    name="InyfinnPhotoResizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="InyfinnPhotoResizer",
)
