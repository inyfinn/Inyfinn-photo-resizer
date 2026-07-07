"""Single-instance mutex — Inno Setup wykrywa ten sam mutex przy dezinstalacji."""

from __future__ import annotations

import sys

APP_MUTEX_NAME = "InyfinnPhotoResizerAppMutex"
_mutex_handle = None


def acquire_app_mutex() -> bool:
    """Zwraca False, gdy inna instancja aplikacji już działa."""
    global _mutex_handle
    if sys.platform != "win32":
        return True

    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
    if not handle:
        return False
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return False
    _mutex_handle = handle
    return True
