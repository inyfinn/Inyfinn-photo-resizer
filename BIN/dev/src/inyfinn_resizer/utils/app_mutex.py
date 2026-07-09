"""Single-instance mutex — Inno Setup wykrywa ten sam mutex przy dezinstalacji."""

from __future__ import annotations

import sys

APP_MUTEX_NAME = "InyfinnPhotoResizerAppMutex"
_mutex_handle = None
_WINDOW_TITLES = ("Inyfinn Photo Resizer",)


def acquire_app_mutex() -> bool:
    """Zwraca False, gdy inna instancja aplikacji już działa."""
    global _mutex_handle
    if sys.platform != "win32":
        return True

    import ctypes

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    handle = kernel32.CreateMutexW(None, True, APP_MUTEX_NAME)
    last_error = kernel32.GetLastError()
    if not handle:
        return False
    if last_error == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    _mutex_handle = handle
    return True


def release_app_mutex() -> None:
    global _mutex_handle
    if sys.platform != "win32" or not _mutex_handle:
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.ReleaseMutex(_mutex_handle)
    kernel32.CloseHandle(_mutex_handle)
    _mutex_handle = None


def activate_existing_instance() -> bool:
    """Przenosi istniejące okno aplikacji na wierzch (drugi start skrótu)."""
    if sys.platform != "win32":
        return False

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found: list[int] = []

    def _callback(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        if any(marker in title for marker in _WINDOW_TITLES):
            found.append(hwnd)
        return True

    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(_callback)
    user32.EnumWindows(enum_proc, 0)
    if not found:
        return False

    hwnd = found[0]
    SW_RESTORE = 9
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    return True
