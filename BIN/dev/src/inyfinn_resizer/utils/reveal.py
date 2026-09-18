"""Pokaż plik w Eksploratorze (zaznaczony) albo otwórz folder."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def reveal_in_explorer(path: Path) -> bool:
    """Plik → Eksplorator z zaznaczeniem; folder → otwarty folder. False, gdy nic nie istnieje."""
    target = Path(path)
    if not target.exists():
        target = target.parent
        if not target.is_dir():
            return False
    if sys.platform == "win32":
        if target.is_file():
            # EXE windowed nie ma std handles — bez DEVNULL Popen rzuca WinError 6.
            subprocess.Popen(
                ["explorer", f"/select,{target}"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.startfile(str(target))  # noqa: S606
        return True
    folder = target if target.is_dir() else target.parent
    subprocess.Popen(["xdg-open", str(folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True
