"""9-punktowy wybór kotwicy przycięcia (róża wiatrów)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

ANCHOR_KEYS: tuple[str, ...] = (
    "top-left",
    "top",
    "top-right",
    "left",
    "center",
    "right",
    "bottom-left",
    "bottom",
    "bottom-right",
)

ANCHOR_LABELS: dict[str, str] = {
    "top-left": "↖",
    "top": "↑",
    "top-right": "↗",
    "left": "←",
    "center": "●",
    "right": "→",
    "bottom-left": "↙",
    "bottom": "↓",
    "bottom-right": "↘",
}


class CropAnchorPicker(QWidget):
    anchorChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cropAnchorPicker")
        self._value = "center"
        self._buttons: dict[str, QPushButton] = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(3)
        for index, key in enumerate(ANCHOR_KEYS):
            btn = QPushButton(ANCHOR_LABELS[key])
            btn.setObjectName("cropAnchorBtn")
            btn.setCheckable(True)
            btn.setFixedSize(28, 28)
            btn.setToolTip(key.replace("-", " "))
            btn.clicked.connect(lambda _checked=False, k=key: self._select(k))
            row, col = divmod(index, 3)
            grid.addWidget(btn, row, col)
            self._buttons[key] = btn
        self._select("center", emit=False)

    def _select(self, key: str, *, emit: bool = True) -> None:
        self._value = key
        for anchor_key, button in self._buttons.items():
            button.setChecked(anchor_key == key)
        if emit:
            self.anchorChanged.emit(key)

    def value(self) -> str:
        return self._value

    def set_value(self, anchor: str) -> None:
        if anchor in self._buttons:
            self._select(anchor, emit=False)
