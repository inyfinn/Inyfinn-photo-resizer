"""Dialog pobierania modelu usuwania tła (pierwsze użycie „Usuń tło”)."""

from __future__ import annotations

import time

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog
from inyfinn_resizer.core.transforms import rmbg_models


class _DownloadThread(QThread):
    failed = Signal(str)
    succeeded = Signal()

    def __init__(self, model_name: str) -> None:
        super().__init__()
        self._model_name = model_name
        self._cancel = False
        self.received = 0
        self.total = rmbg_models.get_spec(model_name).size
        self.setPriority(QThread.Priority.LowPriority)

    def request_cancel(self) -> None:
        self._cancel = True

    def _on_progress(self, received: int, total: int) -> None:
        self.received = received
        self.total = total

    def run(self) -> None:
        try:
            rmbg_models.download_model(
                self._model_name,
                progress=self._on_progress,
                cancelled=lambda: self._cancel,
            )
        except rmbg_models.ModelDownloadCancelled:
            return
        except Exception as exc:  # noqa: BLE001 — granica wątku
            self.failed.emit(str(exc) or exc.__class__.__name__)
            return
        self.succeeded.emit()


class ModelDownloadDialog(AppDialog):
    """Modalny dialog: pobiera model, UI odświeża się timerem (bez zalewu sygnałami)."""

    def __init__(self, model_name: str, parent=None) -> None:
        super().__init__(parent)
        spec = rmbg_models.get_spec(model_name)
        self.setWindowTitle("Pobieranie modelu usuwania tła")
        self.setMinimumWidth(460)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(12)

        self._status = QLabel(f"Pobieranie modelu „{spec.label}” ({spec.size_mb} MB)…")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        hint = QLabel(
            "Model pobiera się tylko raz i zostaje na tym komputerze. "
            "Po przerwaniu kolejna próba zacznie od miejsca, w którym skończyła."
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        root.addWidget(self._progress)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._cancel_btn = QPushButton("Anuluj")
        self.polish_button(self._cancel_btn)
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)
        root.addLayout(buttons)

        self._started = time.monotonic()
        self._error: str | None = None
        self._thread = _DownloadThread(model_name)
        self._thread.succeeded.connect(self.accept)
        self._thread.failed.connect(self._on_failed)

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._thread.start()

    @property
    def error(self) -> str | None:
        return self._error

    def _refresh(self) -> None:
        received, total = self._thread.received, self._thread.total
        if total <= 0:
            return
        pct = min(100, int(received * 100 / total))
        self._progress.setValue(pct)
        mb_r = received / (1024 * 1024)
        mb_t = total / (1024 * 1024)
        elapsed = max(0.001, time.monotonic() - self._started)
        speed = mb_r / elapsed
        text = f"Pobieranie modelu… {pct}% ({mb_r:.0f}/{mb_t:.0f} MB"
        if received >= total:
            text = "Sprawdzanie sumy kontrolnej…"
        elif speed > 0.1:
            text += f", {speed:.1f} MB/s)"
        else:
            text += ")"
        self._status.setText(text)

    def _on_failed(self, message: str) -> None:
        self._error = message
        self.reject()

    def done(self, result: int) -> None:  # noqa: D401 — nadpisanie QDialog
        self._timer.stop()
        if self._thread.isRunning():
            self._thread.request_cancel()
            self._status.setText("Przerywanie pobierania…")
            if not self._thread.wait(15000):
                # Zawieszony odczyt sieci — wątek nie może zostać zniszczony w trakcie pracy.
                _LINGERING.append(self._thread)
        super().done(result)


_LINGERING: list[_DownloadThread] = []
