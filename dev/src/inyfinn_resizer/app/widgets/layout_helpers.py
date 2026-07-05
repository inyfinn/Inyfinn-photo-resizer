"""Pomocniki układu — wiersze/kolumny jak CSS Grid / Flex."""

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
    QVBoxLayout,
    QWidget,
)

# Stałe wymiary (design system)
BTN_H = 36
BTN_ACTION_W = 120
LABEL_W = 132
ROW_GAP = 10
SECTION_GAP = 14


def make_section(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Ramkowana sekcja z nagłówkiem."""
    box = QFrame()
    box.setObjectName("sectionBox")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(12, 10, 12, 12)
    lay.setSpacing(8)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    lay.addWidget(hdr)
    return box, lay


def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("formLabel")
    lbl.setMinimumWidth(LABEL_W)
    lbl.setMaximumWidth(LABEL_W)
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return lbl


def add_form_row(grid: QGridLayout, row: int, label: str, widget: QWidget, *, span: int = 1) -> None:
    grid.addWidget(form_label(label), row, 0, Qt.AlignTop)
    grid.addWidget(widget, row, 1, 1, span)


def tool_button_row(
    specs: list[tuple[str, Callable[[], None]]],
    parent: QWidget | None = None,
) -> QGridLayout:
    """Równa siatka przycisków narzędzi (1 wiersz, N kolumn)."""
    grid = QGridLayout()
    grid.setHorizontalSpacing(8)
    grid.setContentsMargins(0, 0, 0, 0)
    for col, (text, slot) in enumerate(specs):
        btn = QPushButton(text, parent)
        btn.setObjectName("toolBtn")
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(BTN_H)
        btn.clicked.connect(slot)
        grid.addWidget(btn, 0, col)
        grid.setColumnStretch(col, 1)
    return grid


def action_button(text: str, object_name: str, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName(object_name)
    btn.setFixedHeight(BTN_H)
    if object_name == "btnSecondary":
        btn.setFixedWidth(BTN_ACTION_W)
    elif object_name == "primaryBtn":
        btn.setMinimumWidth(148)
        btn.setFixedHeight(40)
    btn.clicked.connect(slot)
    return btn
