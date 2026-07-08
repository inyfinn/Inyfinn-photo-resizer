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

BTN_H = 32
ROW_GAP = 8
FIELD_GAP = 4
SECTION_GAP = 6


def hint_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hintLabel")
    lbl.setWordWrap(True)
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    return lbl


def field_label(text: str, tooltip: str = "") -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    if tooltip:
        lbl.setToolTip(tooltip)
    return lbl


def field_group(label: str, control: QWidget, hint: str = "") -> QWidget:
    """Etykieta + kontrolka; podpowiedź tylko w tooltipie."""
    wrap = QWidget()
    wrap.setObjectName("fieldGroup")
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(FIELD_GAP)
    lbl = field_label(label, hint)
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if hint:
        control.setToolTip(hint)
    lay.addWidget(lbl)
    lay.addWidget(control)
    return wrap


def compact_row(label: str, control: QWidget, *, tooltip: str = "") -> QWidget:
    """Jeden wiersz: etykieta | kontrolka (kompaktowy formularz)."""
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    lbl = field_label(label, tooltip)
    lbl.setMinimumWidth(88)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    if tooltip:
        control.setToolTip(tooltip)
    row.addWidget(lbl)
    row.addWidget(control, stretch=1)
    return wrap


def slider_control(
    slider: QSlider,
    value_label: QLabel,
    *,
    value_width: int = 36,
    tooltip: str = "",
) -> QWidget:
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    value_label.setObjectName("qualityValue")
    value_label.setMinimumWidth(value_width)
    value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if tooltip:
        slider.setToolTip(tooltip)
        value_label.setToolTip(tooltip)
    row.addWidget(slider, stretch=1)
    row.addWidget(value_label)
    return wrap


def make_section(title: str, tooltip: str = "") -> tuple[QFrame, QVBoxLayout]:
    box = QFrame()
    box.setObjectName("sectionBox")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(10, 8, 10, 8)
    lay.setSpacing(6)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    if tooltip:
        hdr.setToolTip(tooltip)
        box.setToolTip(tooltip)
    lay.addWidget(hdr)
    return box, lay


def make_settings_grid() -> QGridLayout:
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
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
    grid = QGridLayout()
    grid.setHorizontalSpacing(6)
    grid.setVerticalSpacing(6)
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
    btn.setMinimumHeight(36 if object_name == "primaryBtn" else BTN_H)
    btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    if object_name == "primaryBtn":
        btn.setMinimumWidth(110)
    btn.clicked.connect(slot)
    return btn


def form_label(text: str) -> QLabel:
    return field_label(text)


def add_form_row(grid: QGridLayout, row: int, label: str, widget: QWidget, *, span: int = 1) -> None:
    wrap = field_group(label, widget)
    grid.addWidget(wrap, row, 0, 1, span)
