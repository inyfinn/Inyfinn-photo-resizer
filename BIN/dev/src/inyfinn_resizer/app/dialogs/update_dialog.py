"""Dialog ręcznego sprawdzania i instalacji aktualizacji."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog


class UpdateDialog(AppDialog):
    install_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Aktualizacje")
        self.setMinimumWidth(420)
        self.setModal(False)

        root = QVBoxLayout(self)
        root.setSpacing(12)

        self._status = QLabel("Sprawdzanie aktualizacji…")
        self._status.setWordWrap(True)
        self._status.setObjectName("updateDialogStatus")
        root.addWidget(self._status)

        self._hint = QLabel(
            "Pakiet pobiera się w tle — możesz normalnie korzystać z aplikacji. "
            "Instalacja nastąpi dopiero po kliknięciu „Zainstaluj” (aplikacja "
            "zostanie wtedy zamknięta i uruchomiona ponownie)."
        )
        self._hint.setWordWrap(True)
        self._hint.setObjectName("updateDialogHint")
        self._hint.hide()
        root.addWidget(self._hint)

        self._progress = QProgressBar()
        self._progress.setObjectName("updateDialogProgress")
        self._progress.setRange(0, 100)
        self._progress.hide()
        root.addWidget(self._progress)

        self._action_btn = QPushButton("Pobierz i zainstaluj")
        self.polish_button(self._action_btn, primary=True)
        self._action_btn.setObjectName("updateDialogAction")
        self._action_btn.hide()
        self._action_btn.clicked.connect(self.install_requested.emit)
        root.addWidget(self._action_btn, 0, Qt.AlignRight)

        self._close_btn = QPushButton("Zamknij")
        self.polish_button(self._close_btn)
        self._close_btn.clicked.connect(self.close)
        root.addWidget(self._close_btn, 0, Qt.AlignRight)

        self._ready_version: str | None = None

    def set_checking(self) -> None:
        self._status.setText("Sprawdzanie aktualizacji na GitHub…")
        self._hint.hide()
        self._progress.hide()
        self._action_btn.hide()
        self._action_btn.setEnabled(False)

    def set_up_to_date(self) -> None:
        self._status.setText(f"Masz najnowszą wersję ({__version__}).")
        self._hint.hide()
        self._progress.hide()
        self._action_btn.hide()

    def set_check_failed(self, message: str) -> None:
        self._status.setText(f"Nie udało się sprawdzić aktualizacji.\n{message}")
        self._hint.hide()
        self._progress.hide()
        self._action_btn.hide()

    def set_update_available(self, version: str, *, cached: bool) -> None:
        self._ready_version = version
        self._status.setText(
            f"Dostępna nowa wersja: {version}\n"
            f"Obecna wersja: {__version__}"
        )
        self._hint.show()
        self._progress.hide()
        self._action_btn.show()
        self._action_btn.setEnabled(True)
        if cached:
            self._action_btn.setText("Zainstaluj i uruchom ponownie")
        else:
            self._action_btn.setText("Pobierz i zainstaluj")

    def set_downloading(self, received: int, total: int) -> None:
        self._action_btn.setEnabled(False)
        self._progress.show()
        if total > 0:
            pct = min(100, int(received * 100 / total))
            self._progress.setValue(pct)
            mb_r = received / (1024 * 1024)
            mb_t = total / (1024 * 1024)
            self._status.setText(f"Pobieranie aktualizacji… {pct}% ({mb_r:.0f}/{mb_t:.0f} MB)")
        else:
            self._progress.setRange(0, 0)
            mb_r = received / (1024 * 1024)
            self._status.setText(f"Pobieranie aktualizacji… {mb_r:.0f} MB")

    def set_ready_to_install(self, version: str) -> None:
        self._ready_version = version
        self._progress.hide()
        self._progress.setRange(0, 100)
        self._status.setText(f"Pakiet v{version} jest gotowy do instalacji.")
        self._action_btn.setText("Zainstaluj i uruchom ponownie")
        self._action_btn.setEnabled(True)
        self._action_btn.show()

    def set_download_failed(self, message: str) -> None:
        self._progress.hide()
        self._status.setText(f"Pobieranie nie powiodło się.\n{message}")
        if self._ready_version:
            self._action_btn.setText("Pobierz i zainstaluj")
            self._action_btn.setEnabled(True)
            self._action_btn.show()

    @property
    def target_version(self) -> str | None:
        return self._ready_version
