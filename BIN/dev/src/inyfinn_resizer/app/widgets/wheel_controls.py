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


class WheelSlider(QSlider):
    """Suwak — scroll nad polem zmienia wartość (Ctrl = większy krok)."""

    def wheelEvent(self, event: QWheelEvent) -> None:
        direction = _wheel_delta(event)
        if direction == 0:
            event.ignore()
            return
        span = self.maximum() - self.minimum()
        step = max(1, span // 100)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step = max(step, span // 20)
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
        step: int = 1,
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
        step = self._step
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step *= 10
        val = max(self._min_val, min(self._max_val, val + direction * step))
        self.setText(str(val))
        event.accept()


class WheelSpinBox(QSpinBox):
    """SpinBox z domyślnym wheelEvent (Qt już wspiera — jawna klasa na przyszłość)."""

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self.isEnabled():
            event.ignore()
            return
        super().wheelEvent(event)
