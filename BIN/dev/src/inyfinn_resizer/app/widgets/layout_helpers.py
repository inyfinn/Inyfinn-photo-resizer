"""Pomocniki układu — siatka i sekcje jak CSS Grid / Flex."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
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

BTN_H = 28
FOOTER_BTN_H = 32
ROW_GAP = 2
FIELD_GAP = 1
SECTION_GAP = 8
STEP_ICON_SIZE = 40
COMPACT_LABEL_W = 78
COMPACT_SLIDER_ROW_H = 32
COMPACT_CONTROL_ROW_H = 32


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


def compact_row(
    label: str,
    control: QWidget,
    *,
    tooltip: str = "",
    tight: bool = False,
    height: int | None = None,
) -> QWidget:
    """Jeden wiersz: etykieta | kontrolka (kompaktowy formularz)."""
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    row.setAlignment(Qt.AlignVCenter)
    lbl = field_label(label, tooltip)
    lbl.setMinimumWidth(COMPACT_LABEL_W)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    if tooltip:
        control.setToolTip(tooltip)
    row.addWidget(lbl, 0, Qt.AlignVCenter)
    row.addWidget(control, stretch=1, alignment=Qt.AlignVCenter)
    row_h = height
    if row_h is None and tight:
        row_h = COMPACT_SLIDER_ROW_H
    if row_h is not None:
        wrap.setMinimumHeight(row_h)
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
    slider.setMinimumHeight(20)
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
    lay.setContentsMargins(8, 4, 8, 6)
    lay.setSpacing(4)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    if tooltip:
        hdr.setToolTip(tooltip)
        box.setToolTip(tooltip)
    lay.addWidget(hdr)
    return box, lay


def make_step_section(
    title: str,
    subtitle: str,
    *,
    step_key: str,
    tooltip: str = "",
) -> tuple[QFrame, QVBoxLayout]:
    """Sekcja kroku z kolorową ikoną (format / dimensions / save)."""
    from inyfinn_resizer.app.widgets.section_icons import step_pixmap

    object_names = {
        "format": "sectionBoxStep1",
        "dimensions": "sectionBoxStep2",
        "save": "sectionBoxStep3",
    }
    box = QFrame()
    box.setObjectName(object_names.get(step_key, "sectionBox"))
    box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    outer = QVBoxLayout(box)
    outer.setContentsMargins(10, 8, 12, 10)
    outer.setSpacing(6)

    header = QWidget()
    header.setObjectName("sectionStepHeader")
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(10)

    icon = QLabel()
    icon.setObjectName(f"sectionIcon{step_key.capitalize()}")
    icon.setPixmap(step_pixmap(step_key))
    icon.setFixedSize(STEP_ICON_SIZE, STEP_ICON_SIZE)
    header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

    text_col = QVBoxLayout()
    text_col.setContentsMargins(0, 0, 0, 0)
    text_col.setSpacing(1)
    title_lbl = QLabel(title)
    title_lbl.setObjectName("sectionStepTitle")
    text_col.addWidget(title_lbl)
    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("sectionStepHint")
        sub_lbl.setWordWrap(True)
        text_col.addWidget(sub_lbl)
    header_row.addLayout(text_col, stretch=1)
    outer.addWidget(header)

    content_wrap = QFrame()
    content_wrap.setObjectName(f"sectionInner{step_key.capitalize()}")
    content_wrap.setFrameShape(QFrame.Shape.NoFrame)
    inner = QVBoxLayout(content_wrap)
    inner.setContentsMargins(2, 0, 2, 2)
    inner.setSpacing(6)
    outer.addWidget(content_wrap)

    if tooltip:
        box.setToolTip(tooltip)
        title_lbl.setToolTip(tooltip)
    return box, inner


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
    specs: list[tuple[str, Callable[[], None], QIcon]],
    parent: QWidget | None = None,
) -> QHBoxLayout:
    """Jeden poziomy rząd przycisków z ikonami."""
    row = QHBoxLayout()
    row.setSpacing(6)
    row.setContentsMargins(0, 0, 0, 0)
    icon_size = QSize(16, 16)
    for text, slot, icon in specs:
        btn = QPushButton(text, parent)
        btn.setObjectName("toolBtn")
        btn.setIcon(icon)
        btn.setIconSize(icon_size)
        btn.setToolTip(text)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.setMinimumHeight(BTN_H)
        btn.clicked.connect(slot)
        row.addWidget(btn)
    row.addStretch()
    return row


def style_dropdown(combo: QComboBox) -> QComboBox:
    """Niebieski obrys + strzałka listy rozwijanej (QSS)."""
    combo.setMinimumHeight(BTN_H)
    combo.setMaximumHeight(COMPACT_CONTROL_ROW_H)
    return combo


def footer_button(text: str, *, primary: bool, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("footerPrimary" if primary else "footerSecondary")
    btn.setFixedSize(108, FOOTER_BTN_H)
    btn.clicked.connect(slot)
    return btn


def action_button(text: str, object_name: str, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName(object_name)
    btn.setMinimumHeight(32 if object_name == "primaryBtn" else BTN_H)
    if object_name == "primaryBtn":
        btn.setMinimumWidth(116)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(88)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    btn.clicked.connect(slot)
    return btn


def h_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("hSeparator")
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    return line


def v_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("vSeparator")
    line.setFrameShape(QFrame.VLine)
    line.setFixedWidth(1)
    return line


def browse_button(text: str = "PRZEGLĄDAJ", *, tooltip: str = "", slot=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("btnBrowse")
    btn.setMinimumHeight(BTN_H)
    btn.setFixedHeight(BTN_H)
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    if tooltip:
        btn.setToolTip(tooltip)
    if slot:
        btn.clicked.connect(slot)
    return btn


def add_form_row(grid: QGridLayout, row: int, label: str, widget: QWidget, *, span: int = 1) -> None:
    wrap = field_group(label, widget)
    grid.addWidget(wrap, row, 0, 1, span)
