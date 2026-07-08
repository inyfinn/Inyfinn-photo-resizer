"""Pomocniki układu — siatka i sekcje jak CSS Grid / Flex."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

BTN_H = 36
ROW_GAP = 12
FIELD_GAP = 6
SECTION_GAP = 10


def hint_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hintLabel")
    lbl.setWordWrap(True)
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    return lbl


def field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return lbl


def field_group(label: str, control: QWidget, hint: str = "") -> QWidget:
    """Pionowy blok pola: etykieta → kontrolka → podpowiedź (jak HTML form-group)."""
    wrap = QWidget()
    wrap.setObjectName("fieldGroup")
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(FIELD_GAP)
    lay.addWidget(field_label(label))
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    lay.addWidget(control)
    if hint:
        lay.addWidget(hint_label(hint))
    return wrap


def slider_control(
    slider: QSlider,
    value_label: QLabel,
    *,
    value_width: int = 40,
) -> QWidget:
    """Suwak + wartość w jednym wierszu (flex row)."""
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    value_label.setObjectName("qualityValue")
    value_label.setMinimumWidth(value_width)
    value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    row.addWidget(slider, stretch=1)
    row.addWidget(value_label)
    return wrap


def make_section(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    box = QFrame()
    box.setObjectName("sectionBox")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(8)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    lay.addWidget(hdr)
    if subtitle:
        lay.addWidget(hint_label(subtitle))
    return box, lay


def make_settings_grid() -> QGridLayout:
    """Siatka 2-kolumnowa: pola obok siebie na szerszym panelu."""
    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(ROW_GAP)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    return grid


def add_grid_field(grid: QGridLayout, row: int, col: int, field: QWidget) -> None:
    grid.addWidget(field, row, col)


def add_grid_span(grid: QGridLayout, row: int, widget: QWidget) -> None:
    grid.addWidget(widget, row, 0, 1, 2)


def tool_button_row(
    specs: list[tuple[str, Callable[[], None]]],
    parent: QWidget | None = None,
) -> QGridLayout:
    """Przyciski w siatce 2×2 — nie ucinają się na wąskim panelu."""
    grid = QGridLayout()
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(8)
    grid.setContentsMargins(0, 0, 0, 0)
    for idx, (text, slot) in enumerate(specs):
        btn = QPushButton(text, parent)
        btn.setObjectName("toolBtn")
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(BTN_H)
        btn.clicked.connect(slot)
        grid.addWidget(btn, idx // 2, idx % 2)
    for c in range(2):
        grid.setColumnStretch(c, 1)
    return grid


def action_button(text: str, object_name: str, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName(object_name)
    btn.setMinimumHeight(BTN_H if object_name != "primaryBtn" else 40)
    btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    if object_name == "primaryBtn":
        btn.setMinimumWidth(120)
    btn.clicked.connect(slot)
    return btn


# Zachowanie kompatybilności ze starym API
def form_label(text: str) -> QLabel:
    return field_label(text)


def add_form_row(grid: QGridLayout, row: int, label: str, widget: QWidget, *, span: int = 1) -> None:
    wrap = field_group(label, widget)
    grid.addWidget(wrap, row, 0, 1, span)
