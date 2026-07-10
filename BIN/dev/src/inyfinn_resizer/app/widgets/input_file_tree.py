"""Lista plików z obsługą drag & drop folderów i plików."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTreeWidget

if TYPE_CHECKING:
    from inyfinn_resizer.app.main_window import MainWindow


class InputFileTree(QTreeWidget):
    def __init__(self, window: "MainWindow", parent=None) -> None:
        super().__init__(parent)
        self._window = window
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self._window._handle_dropped_urls(event.mimeData().urls())
            event.acceptProposedAction()
            return
        super().dropEvent(event)
