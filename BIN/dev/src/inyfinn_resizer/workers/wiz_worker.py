"""Worker sekwencji wizek — przetwarzanie folderów in-place."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from inyfinn_resizer.core.wiz_sequence import WizFolderResult, process_wiz_folder, ui_quality_to_wiz_slider


class WizWorker(QObject):
    progress = Signal(int, int, str)
    folder_done = Signal(object)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, folders: list[Path], quality_0_100: int):
        super().__init__()
        self.folders = folders
        self.slider_val = ui_quality_to_wiz_slider(quality_0_100)

    def run(self) -> None:
        results: list[WizFolderResult] = []
        total = len(self.folders)
        for i, folder in enumerate(self.folders):
            self.progress.emit(i, total, folder.name)
            try:
                result = process_wiz_folder(folder, self.slider_val)
                results.append(result)
                self.folder_done.emit(result)
            except Exception as e:
                self.error.emit(f"{folder}: {e}")
            self.progress.emit(i + 1, total, folder.name)
        self.finished.emit(results)


class WizThread(QThread):
    def __init__(self, worker: WizWorker):
        super().__init__()
        self._worker = worker
        worker.moveToThread(self)

    def run(self) -> None:
        self._worker.run()
