"""Symulowany postęp gdy brak sygnału z rembg — faktyczne zakończenie ma zawsze pierwszeństwo."""

from __future__ import annotations

import random
import time

from PySide6.QtCore import QObject, QTimer, Signal

BG_ESTIMATE_SEC: dict[str, float] = {
    "birefnet-general": 150.0,
    "birefnet-general-lite": 60.0,
}

DEFAULT_ESTIMATE_SEC = 45.0
SIM_CAP_PERCENT = 90


class FileProgressSimulator(QObject):
    """Podbija % w trakcie długich operacji; 100% tylko przez complete_file()."""

    tick = Signal(int, int, str)  # index, percent, phase

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._on_tick)
        self._index: int | None = None
        self._percent = 0
        self._started = 0.0
        self._estimate = DEFAULT_ESTIMATE_SEC
        self._ratio_to_90 = 1.0
        self._bg_removal = False
        self._real_done = False

    def start_file(
        self,
        index: int,
        *,
        bg_removal: bool,
        bg_model: str = "birefnet-general-lite",
    ) -> None:
        self._index = index
        self._percent = 5
        self._started = time.monotonic()
        self._bg_removal = bg_removal
        self._real_done = False
        if bg_removal:
            self._estimate = BG_ESTIMATE_SEC.get(bg_model, DEFAULT_ESTIMATE_SEC)
            self._ratio_to_90 = 0.70 if "lite" in bg_model else 1.0
        else:
            self._estimate = DEFAULT_ESTIMATE_SEC
            self._ratio_to_90 = 1.0
        self._timer.start()
        phase = "Usuwanie tła…" if bg_removal else "Przetwarzanie…"
        self.tick.emit(index, self._percent, phase)

    def complete_file(self, index: int) -> None:
        if self._index != index:
            return
        self._real_done = True
        self._percent = 100
        self._timer.stop()
        self.tick.emit(index, 100, "Gotowe")

    def stop(self) -> None:
        self._timer.stop()
        self._index = None
        self._real_done = False

    def estimate_remaining_sec(self) -> float | None:
        if self._index is None or self._real_done:
            return None
        elapsed = time.monotonic() - self._started
        target = self._estimate * self._ratio_to_90
        if elapsed >= target:
            return max(5.0, self._estimate - elapsed)
        progress = elapsed / max(0.1, target)
        total_guess = self._estimate if self._bg_removal else self._estimate
        return max(0.0, total_guess - elapsed)

    def _on_tick(self) -> None:
        if self._index is None or self._real_done:
            return
        elapsed = time.monotonic() - self._started
        target = self._estimate * self._ratio_to_90
        time_ratio = min(1.0, elapsed / max(1.0, target))
        simulated = int(5 + time_ratio * (SIM_CAP_PERCENT - 5))
        simulated = min(SIM_CAP_PERCENT, simulated + random.randint(0, 4))
        if simulated <= self._percent:
            simulated = min(SIM_CAP_PERCENT, self._percent + random.randint(1, 3))
        self._percent = simulated
        phase = "Usuwanie tła…" if self._bg_removal else "Kompresja…"
        self.tick.emit(self._index, self._percent, phase)
