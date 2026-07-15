"""Toast aktualizacji — lewy dolny róg okna."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class UpdateToast(QFrame):
    install_requested = Signal()
    dismiss_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("updateToast")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        self._title = QLabel("Dostępna aktualizacja")
        self._title.setObjectName("updateToastTitle")
        root.addWidget(self._title)

        self._message = QLabel("")
        self._message.setObjectName("updateToastMessage")
        self._message.setWordWrap(True)
        root.addWidget(self._message)

        self._progress = QLabel("")
        self._progress.setObjectName("updateToastProgress")
        self._progress.hide()
        root.addWidget(self._progress)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._install_btn = QPushButton("Zainstaluj")
        self._install_btn.setObjectName("updateToastInstall")
        self._install_btn.setMinimumHeight(32)
        self._install_btn.clicked.connect(self.install_requested.emit)
        btn_row.addWidget(self._install_btn)

        self._later_btn = QPushButton("Później")
        self._later_btn.setObjectName("updateToastLater")
        self._later_btn.setMinimumHeight(32)
        self._later_btn.clicked.connect(self.dismiss_requested.emit)
        btn_row.addWidget(self._later_btn)
        root.addLayout(btn_row)

    def set_version(self, version: str) -> None:
        self._message.setText(f"Wersja {version} jest gotowa. Zainstalować teraz?")

    def set_downloading(self, received: int, total: int) -> None:
        self._progress.show()
        if total > 0:
            pct = min(100, int(received * 100 / total))
            mb_r = received / (1024 * 1024)
            mb_t = total / (1024 * 1024)
            self._progress.setText(f"Pobieranie… {pct}% ({mb_r:.0f}/{mb_t:.0f} MB)")
        else:
            mb_r = received / (1024 * 1024)
            self._progress.setText(f"Pobieranie… {mb_r:.0f} MB")
        self._install_btn.setEnabled(False)

    def set_ready(self, version: str) -> None:
        self._progress.hide()
        self._install_btn.setEnabled(True)
        self.set_version(version)

    def hide_toast(self) -> None:
        self.hide()

    def show_non_blocking(self) -> None:
        """Pokaż toast bez przejmowania fokusu — aplikacja pozostaje w pełni używalna."""
        self.adjustSize()
        self.show()
        self.raise_()

    def reposition(self, host: QWidget) -> None:
        if not self.isVisible():
            return
        margin = 16
        self.adjustSize()
        x = margin
        y = host.height() - self.height() - margin
        self.move(x, max(margin, y))
        self.raise_()
