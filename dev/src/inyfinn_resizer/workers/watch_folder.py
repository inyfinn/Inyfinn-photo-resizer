"""Watch folder — auto-queue new images."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from inyfinn_resizer.core.formats.registry import is_image_file

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class _Handler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if is_image_file(path):
            self._callback(path)


class WatchFolderService(QObject):
    file_detected = Signal(str)

    def __init__(self, folder: Path, recursive: bool = True):
        super().__init__()
        self.folder = folder
        self.recursive = recursive
        self._observer = None

    def start(self) -> bool:
        if not HAS_WATCHDOG or not self.folder.is_dir():
            return False
        handler = _Handler(lambda p: self.file_detected.emit(str(p)))
        self._observer = Observer()
        self._observer.schedule(handler, str(self.folder), recursive=self.recursive)
        self._observer.start()
        return True

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
