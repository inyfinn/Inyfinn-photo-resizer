"""Wykrywanie katalogu instalacji (portable: launcher + BIN/, flat: EXE + _internal)."""

from __future__ import annotations

import sys
from pathlib import Path


def install_root() -> Path | None:
    if not getattr(sys, "frozen", False):
        return None

    exe = Path(sys.executable).resolve()
    exe_dir = exe.parent

    if exe_dir.name.upper() == "BIN":
        root = exe_dir.parent
        if (root / "BIN" / "_internal").is_dir():
            return root

    if (exe_dir / "BIN" / "_internal").is_dir():
        return exe_dir

    if (exe_dir / "_internal").is_dir():
        return exe_dir

    return None


def install_layout() -> str:
    """portable | flat | unknown"""
    root = install_root()
    if root is None:
        return "unknown"

    if (root / "BIN" / "_internal").is_dir():
        return "portable"

    if (root / "_internal").is_dir():
        return "flat"

    return "unknown"


def launcher_executable() -> Path | None:
    root = install_root()
    if root is None:
        return None

    layout = install_layout()
    if layout == "portable":
        candidate = root / "InyfinnPhotoResizer.exe"
        if candidate.is_file():
            return candidate
        return root / "BIN" / "InyfinnPhotoResizer.exe"

    return root / "InyfinnPhotoResizer.exe"
