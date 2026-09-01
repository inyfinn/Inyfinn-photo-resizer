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

BTN_H = 26
FOOTER_BTN_H = 32
ROW_GAP = 6
FIELD_GAP = 4
SECTION_GAP = 6
TILE_PADDING = 22
TILE_PADDING_TOP = TILE_PADDING - 8  # nagłówki 8 px wyżej w kafelku
TILE_HEADER_SPACING = 6
TILE_INNER_SPACING = 6
TILE_TITLE_HEIGHT = 18
CROP_PICKER_HEIGHT = 90
STEP_ICON_SIZE = 24
COMPACT_LABEL_W = 78
COMPACT_SLIDER_ROW_H = 28
COMPACT_CONTROL_ROW_H = 28


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


def stacked_field(label: str, control: QWidget, *, tooltip: str = "") -> QWidget:
    """Etykieta nad kontrolką (siatka 2-kolumnowa)."""
    wrap = QWidget()
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(FIELD_GAP)
    lbl = field_label(label, tooltip)
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if tooltip:
        control.setToolTip(tooltip)
    lay.addWidget(lbl)
    lay.addWidget(control)
    return wrap


def make_tile(
    title: str,
    subtitle: str = "",
    *,
    icon_key: str = "",
    tooltip: str = "",
    compact: bool = False,
    compact_content_h: int = 0,
) -> tuple[QFrame, QVBoxLayout]:
    """Płaski kafelek Bento — jednolite tło, bez ramek."""
    from inyfinn_resizer.app.widgets.section_icons import step_pixmap

    box = QFrame()
    box.setObjectName("bentoTile")
    v_policy = QSizePolicy.Policy.Fixed if compact else QSizePolicy.Policy.Expanding
    box.setSizePolicy(QSizePolicy.Policy.Expanding, v_policy)
    outer = QVBoxLayout(box)
    outer.setContentsMargins(TILE_PADDING, TILE_PADDING_TOP, TILE_PADDING, TILE_PADDING)
    outer.setSpacing(TILE_HEADER_SPACING)

    header = QWidget()
    header.setObjectName("sectionStepHeader")
    header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(TILE_HEADER_SPACING)

    if icon_key:
        icon = QLabel()
        icon.setObjectName(f"sectionIcon{icon_key.capitalize()}")
        icon.setPixmap(step_pixmap(icon_key))
        icon.setFixedSize(STEP_ICON_SIZE, STEP_ICON_SIZE)
        header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        box.setProperty("stepKey", icon_key)
        box._step_icon_label = icon  # type: ignore[attr-defined]
        box._step_key = icon_key  # type: ignore[attr-defined]

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
    outer.addWidget(header, 0, Qt.AlignmentFlag.AlignTop)

    content = QWidget()
    content.setSizePolicy(
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Maximum if compact else QSizePolicy.Policy.Expanding,
    )
    inner = QVBoxLayout(content)
    inner.setContentsMargins(0, 0, 0, 0)
    inner.setSpacing(TILE_INNER_SPACING)
    outer.addWidget(content, 0 if compact else 1)

    if compact and compact_content_h > 0:
        header_h = STEP_ICON_SIZE if icon_key else TILE_TITLE_HEIGHT
        box.setFixedHeight(
            TILE_PADDING_TOP
            + header_h
            + TILE_HEADER_SPACING
            + compact_content_h
            + TILE_PADDING
        )

    if tooltip:
        box.setToolTip(tooltip)
        title_lbl.setToolTip(tooltip)
    return box, inner


def make_bento_column() -> tuple[QWidget, QVBoxLayout]:
    """Pionowa kolumna Bento — kafelki sklejają się bez pustych przerw między wierszami siatki."""
    col = QWidget()
    col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(SECTION_GAP)
    return col, lay


def make_settings_grid() -> QGridLayout:
    grid = QGridLayout()
    grid.setHorizontalSpacing(ROW_GAP)
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
    btn.setFixedHeight(FOOTER_BTN_H)
    btn.setMinimumWidth(140 if primary else 108)
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
