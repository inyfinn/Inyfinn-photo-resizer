"""Dyskretny wskaźnik pobierania aktualizacji w lewym dolnym rogu (status bar)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


_SPINNER_FRAMES = ("◐", "◓", "◑", "◒")


class UpdateStatusBar(QFrame):
    cancel_requested = Signal()
    install_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("updateStatusBar")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.hide()

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 0, 8, 0)
        root.setSpacing(6)

        self._spinner = QLabel(_SPINNER_FRAMES[0])
        self._spinner.setObjectName("updateStatusSpinner")
        self._spinner.setFixedWidth(14)
        self._spinner.setAlignment(Qt.AlignCenter)
        root.addWidget(self._spinner)

        self._label = QLabel("")
        self._label.setObjectName("updateStatusLabel")
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        root.addWidget(self._label)

        self._cancel_btn = QPushButton("✕")
        self._cancel_btn.setObjectName("updateStatusCancel")
        self._cancel_btn.setFixedSize(22, 22)
        self._cancel_btn.setToolTip("Anuluj pobieranie aktualizacji")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        root.addWidget(self._cancel_btn)

        self._install_btn = QPushButton("Zainstaluj")
        self._install_btn.setObjectName("updateStatusInstall")
        self._install_btn.setFixedHeight(22)
        self._install_btn.hide()
        self._install_btn.clicked.connect(self.install_requested.emit)
        root.addWidget(self._install_btn)

        self._spin_idx = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(140)
        self._spin_timer.timeout.connect(self._tick_spinner)
        self._version = ""

    def _tick_spinner(self) -> None:
        self._spin_idx = (self._spin_idx + 1) % len(_SPINNER_FRAMES)
        self._spinner.setText(_SPINNER_FRAMES[self._spin_idx])

    def _start_spinner(self) -> None:
        self._spin_idx = 0
        self._spinner.setText(_SPINNER_FRAMES[0])
        self._spinner.show()
        self._spin_timer.start()

    def _stop_spinner(self) -> None:
        self._spin_timer.stop()
        self._spinner.hide()

    def set_checking(self) -> None:
        self._version = ""
        self._install_btn.hide()
        self._cancel_btn.hide()
        self._start_spinner()
        self._label.setText("Sprawdzanie aktualizacji…")
        self.show()

    def set_downloading(self, version: str, received: int, total: int) -> None:
        self._version = version
        self._install_btn.hide()
        self._cancel_btn.show()
        self._start_spinner()
        if total > 0:
            pct = min(100, int(received * 100 / total))
            mb_r = received / (1024 * 1024)
            mb_t = total / (1024 * 1024)
            self._label.setText(
                f"Pobieranie w tle v{version}… {pct}% ({mb_r:.0f}/{mb_t:.0f} MB)"
            )
        else:
            mb_r = received / (1024 * 1024)
            self._label.setText(f"Pobieranie w tle v{version}… {mb_r:.0f} MB")
        self.show()

    def set_ready(self, version: str) -> None:
        self._version = version
        self._stop_spinner()
        self._cancel_btn.hide()
        self._install_btn.show()
        self._label.setText(f"Dostępna aktualizacja v{version}")
        self.show()

    def hide_bar(self) -> None:
        self._stop_spinner()
        self._install_btn.hide()
        self.hide()
