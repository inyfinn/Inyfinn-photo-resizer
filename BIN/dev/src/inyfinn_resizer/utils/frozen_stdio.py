"""PyInstaller windowed EXE sets sys.stdout/stderr to None — patch before rembg/onnx."""

from __future__ import annotations

import os
import sys


def _debug_log_target():
    """INYFINN_STDERR_FILE=<plik> — diagnostyka EXE (komunikaty Qt/Pythona zamiast devnull)."""
    path = os.environ.get("INYFINN_STDERR_FILE")
    if not path:
        return None
    try:
        handle = open(path, "a", encoding="utf-8", errors="replace", buffering=1)  # noqa: SIM115
    except OSError:
        return None
    try:
        import faulthandler

        faulthandler.enable(handle)
    except Exception:
        pass
    return handle


def ensure_stdio() -> None:
    """Gdy stdout/stderr są None (console=False), przekieruj na devnull."""
    debug = _debug_log_target()
    if debug is not None:
        if sys.stdout is None or getattr(sys.stdout, "name", "") == os.devnull:
            sys.stdout = debug
        if sys.stderr is None or getattr(sys.stderr, "name", "") == os.devnull:
            sys.stderr = debug
        return
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
