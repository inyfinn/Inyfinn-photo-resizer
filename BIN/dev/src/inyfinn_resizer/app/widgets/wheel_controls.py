"""Kontrolki z obsługą kółka myszy (zwiększ / zmniejsz wartość)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QLineEdit, QSlider, QSpinBox


def _wheel_delta(event: QWheelEvent) -> int:
    dy = event.angleDelta().y()
    if dy == 0:
        return 0
    return 1 if dy > 0 else -1


def wheel_step_for_event(event: QWheelEvent, *, default: int = 10) -> int:
    """Domyślnie co 10; Shift = 100; Ctrl = 1."""
    mods = event.modifiers()
    if mods & Qt.KeyboardModifier.ControlModifier:
        return 1
    if mods & Qt.KeyboardModifier.ShiftModifier:
        return 100
    return default


class WheelSlider(QSlider):
    """Suwak — scroll nad polem zmienia wartość (domyślnie co 10)."""

    def __init__(self, *args, step: int = 10, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._wheel_step = step

    def wheelEvent(self, event: QWheelEvent) -> None:
        direction = _wheel_delta(event)
        if direction == 0:
            event.ignore()
            return
        step = wheel_step_for_event(event, default=self._wheel_step)
        self.setValue(
            max(self.minimum(), min(self.maximum(), self.value() + direction * step))
        )
        event.accept()


class WheelIntLineEdit(QLineEdit):
    """Pole liczby całkowitej — scroll zmienia wartość."""

    def __init__(
        self,
        *args,
        min_val: int = 1,
        max_val: int = 16384,
        step: int = 10,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._min_val = min_val
        self._max_val = max_val
        self._step = step

    def wheelEvent(self, event: QWheelEvent) -> None:
        direction = _wheel_delta(event)
        if direction == 0:
            event.ignore()
            return
        text = self.text().strip()
        try:
            val = int(text) if text else self._min_val
        except ValueError:
            val = self._min_val
        step = wheel_step_for_event(event, default=self._step)
        val = max(self._min_val, min(self._max_val, val + direction * step))
        self.setText(str(val))
        event.accept()


class WheelSpinBox(QSpinBox):
    """SpinBox — scroll z krokami 10 / Shift 100 / Ctrl 1."""

    def __init__(self, *args, wheel_step: int = 10, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._wheel_step = wheel_step

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self.isEnabled():
            event.ignore()
            return
        direction = _wheel_delta(event)
        if direction == 0:
            event.ignore()
            return
        step = wheel_step_for_event(event, default=self._wheel_step)
        self.setValue(
            max(self.minimum(), min(self.maximum(), self.value() + direction * step))
        )
        event.accept()
