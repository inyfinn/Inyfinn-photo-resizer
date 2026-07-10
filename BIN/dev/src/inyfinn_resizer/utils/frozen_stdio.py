"""PyInstaller windowed EXE sets sys.stdout/stderr to None — patch before rembg/onnx."""

from __future__ import annotations

import os
import sys


def ensure_stdio() -> None:
    """Gdy stdout/stderr są None (console=False), przekieruj na devnull."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")  # noqa: SIM115
    elif hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")  # noqa: SIM115
    elif hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
