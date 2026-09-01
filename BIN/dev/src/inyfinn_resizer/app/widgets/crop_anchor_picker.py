"""9-punktowy wybór kotwicy przycięcia (róża wiatrów)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QSizePolicy, QWidget

_BTN_SIZE = 28
_GRID_GAP = 3
_PICKER_SIZE = 3 * _BTN_SIZE + 2 * _GRID_GAP  # 90

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

ANCHOR_TOOLTIPS: dict[str, str] = {
    "top-left": "Lewy górny róg zdjęcia — kadr utrzyma tę część, resztę przytnie",
    "top": "Górna krawędź zdjęcia — kadr utrzyma górę, przytnie boki i dół",
    "top-right": "Prawy górny róg zdjęcia — kadr utrzyma tę część, resztę przytnie",
    "left": "Lewa krawędź zdjęcia — kadr utrzyma lewą stronę, przytnie resztę",
    "center": "Środek zdjęcia — kadr utrzyma środek, przytnie równo ze wszystkich stron",
    "right": "Prawa krawędź zdjęcia — kadr utrzyma prawą stronę, przytnie resztę",
    "bottom-left": "Lewy dolny róg zdjęcia — kadr utrzyma tę część, resztę przytnie",
    "bottom": "Dolna krawędź zdjęcia — kadr utrzyma dół, przytnie boki i górę",
    "bottom-right": "Prawy dolny róg zdjęcia — kadr utrzyma tę część, resztę przytnie",
}


class CropAnchorPicker(QWidget):
    anchorChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cropAnchorPicker")
        self.setFixedSize(_PICKER_SIZE, _PICKER_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._value = "center"
        self._buttons: dict[str, QPushButton] = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(_GRID_GAP)
        for index, key in enumerate(ANCHOR_KEYS):
            btn = QPushButton(ANCHOR_LABELS[key])
            btn.setObjectName("cropAnchorBtn")
            btn.setCheckable(True)
            btn.setFixedSize(_BTN_SIZE, _BTN_SIZE)
            btn.setToolTip(ANCHOR_TOOLTIPS[key])
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
