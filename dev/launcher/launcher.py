"""Minimalny launcher w korzeniu — uruchamia BIN\\InyfinnPhotoResizer.exe."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _error(text: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, text, "Inyfinn Photo Resizer", 0x10)
    except Exception:
        print(text, file=sys.stderr)


def main() -> int:
    root = Path(sys.executable).resolve().parent
    bin_dir = root / "BIN"
    app_exe = bin_dir / "InyfinnPhotoResizer.exe"
    internal = bin_dir / "_internal"

    if not app_exe.is_file():
        _error(f"Brak programu:\n{app_exe}\n\nUruchom BIN\\build.bat aby przebudować.")
        return 1
    if not internal.is_dir():
        _error(f"Brak folderu:\n{internal}\n\nUruchom BIN\\build.bat aby przebudować.")
        return 1

    os.chdir(bin_dir)
    os.execv(str(app_exe), [str(app_exe), *sys.argv[1:]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
