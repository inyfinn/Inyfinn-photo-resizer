"""Wybór wielu formatów wyjściowych (checkboxy w siatce)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QGridLayout, QLabel, QVBoxLayout, QWidget

from inyfinn_resizer.app.i18n_pl import FORMAT_LABEL_PL
from inyfinn_resizer.core.formats.registry import OUTPUT_FORMATS

PRIMARY_FORMATS = ("webp", "jpeg", "png", "avif", "gif", "tiff", "heic", "bmp", "jxl", "jp2", "pdf")

# Krótkie etykiety w siatce — pełna nazwa w tooltip
SHORT_LABEL: dict[str, str] = {
    "jpeg": "JPEG",
    "png": "PNG",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
    "webp": "WebP",
    "avif": "AVIF",
    "heic": "HEIC",
    "jxl": "JPEG XL",
    "jp2": "JPEG2000",
    "pdf": "PDF",
}


class FormatSelector(QWidget):
    selectionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("formatSelector")
        self._boxes: dict[str, QCheckBox] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        hint = QLabel("Zaznacz jeden lub więcej formatów.")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        col_count = 3
        keys = [k for k in PRIMARY_FORMATS if k in OUTPUT_FORMATS]
        for i, key in enumerate(keys):
            full = FORMAT_LABEL_PL.get(key, key.upper())
            short = SHORT_LABEL.get(key, key.upper())
            cb = QCheckBox(short)
            cb.setToolTip(full)
            cb.setProperty("fmt", key)
            cb.setSizePolicy(cb.sizePolicy().horizontalPolicy(), cb.sizePolicy().verticalPolicy())
            cb.toggled.connect(self.selectionChanged.emit)
            self._boxes[key] = cb
            grid.addWidget(cb, i // col_count, i % col_count)
        root.addLayout(grid)

        self._boxes["webp"].setChecked(True)

    def selected_formats(self) -> list[str]:
        return [k for k, cb in self._boxes.items() if cb.isChecked()]

    def set_selected(self, formats: list[str]) -> None:
        for k, cb in self._boxes.items():
            cb.setChecked(k in formats)

    def first_selected(self) -> str:
        sel = self.selected_formats()
        return sel[0] if sel else "webp"
