"""Pigułki wyboru (design system DK, rozdz. 26.1): wybór wartości zamiast kolorowych kafli i list rozwijanych.

Pigułka niczego nie uruchamia — tylko zaznacza wartość. Jedna wartość (``multi=False``, np. format zapisu w trybie
prostym) albo kilka naraz (``multi=True``, np. rozszerzenia w trybie zaawansowanym; co najmniej jedna zostaje włączona).
Wygląd daje QSS: ``QPushButton[pigulka="true"]`` (zaznaczona = zielona, reszta cicha, bez obrysu).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from inyfinn_resizer.app.i18n_tooltips import (
    ALPHA_OUTPUT_FORMATS,
    FORMAT_ALPHA_TIPS,
    FORMAT_EXTENSION_TIPS,
)
from inyfinn_resizer.core.formats.registry import OUTPUT_FORMATS

PILL_H = 40  # DS 26.1: min-height pigułki (QSS ustawia to samo; liczy się wysokość zawartości, bez obrysu)
PILL_GAP = 6
ROW_GAP = 6
_ALPHA_NO_TRANSPARENCY_TIP = "To rozszerzenie nie obsługuje przezroczystości."

# (klucz, napis, podpowiedź) — jeden wiersz pigułek
PillSpec = tuple[str, str, str]


def make_pill(text: str, *, tooltip: str = "") -> QPushButton:
    """Pojedyncza pigułka do zaznaczania (``checkable``). Wygląd: QSS ``QPushButton[pigulka="true"]``."""
    btn = QPushButton(text)
    btn.setProperty("pigulka", True)
    btn.setCheckable(True)
    btn.setAutoDefault(False)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    btn.setFixedHeight(PILL_H)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


class PillGroup(QWidget):
    """Grupa pigułek w jednym lub kilku rzędach. ``multi=False`` — dokładnie jedna zaznaczona.

    ``more=("Inne", podpowiedź)``: rzędy po pierwszym chowają się pod pigułką „Inne” na końcu pierwszego rzędu
    (rzadkie wartości, DS 26.1). „Inne” nie jest wartością — tylko rozwija / zwija dalsze rzędy; rząd z zaznaczoną
    wartością zostaje rozwinięty (nie da się ukryć zaznaczenia).
    """

    changed = Signal()  # tylko po działaniu usera albo set_*(emit=True)
    expandedChanged = Signal(bool)  # zmiana rozwinięcia dalszych rzędów („Inne”)

    def __init__(
        self,
        rows: Sequence[Sequence[PillSpec]],
        *,
        multi: bool = False,
        more: tuple[str, str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._multi = multi
        self._buttons: dict[str, QPushButton] = {}
        self._order: list[str] = []
        self._extra_keys: set[str] = set()  # wartości w rzędach ukrywanych pod „Inne”
        self._syncing = False
        self._more_btn: QPushButton | None = None
        self._more_box: QWidget | None = None
        self._group = QButtonGroup(self)
        self._group.setExclusive(not multi)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(ROW_GAP)
        if more is not None and len(rows) > 1:
            self._more_box = QWidget(self)
            more_lay = QVBoxLayout(self._more_box)
            more_lay.setContentsMargins(0, 0, 0, 0)
            more_lay.setSpacing(ROW_GAP)
        for r, row in enumerate(rows):
            lay = QHBoxLayout()
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(PILL_GAP)
            for key, text, tip in row:
                btn = make_pill(text, tooltip=tip)
                btn.setProperty("pillKey", key)
                self._group.addButton(btn)
                self._buttons[key] = btn
                self._order.append(key)
                if r > 0 and self._more_box is not None:
                    self._extra_keys.add(key)
                lay.addWidget(btn)
                btn.toggled.connect(lambda checked, k=key: self._on_toggled(k, checked))
            if r == 0 and self._more_box is not None:
                self._more_btn = make_pill(more[0], tooltip=more[1])
                self._more_btn.setProperty("pillMore", True)
                self._more_btn.toggled.connect(self._on_more_toggled)
                lay.addWidget(self._more_btn)
            lay.addStretch(1)
            if r > 0 and self._more_box is not None:
                self._more_box.layout().addLayout(lay)
            else:
                outer.addLayout(lay)
        if self._more_box is not None:
            outer.addWidget(self._more_box)
            self._more_box.setVisible(False)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    # ——— „Inne”: rozwijanie dalszych rzędów ———
    def is_expanded(self) -> bool:
        return self._more_box is not None and not self._more_box.isHidden()

    def set_expanded(self, expanded: bool) -> None:
        """Rozwija / zwija dalsze rzędy; przy zaznaczonej wartości z tych rzędów zostają rozwinięte."""
        if self._more_box is None or self._more_btn is None:
            return
        if not expanded and any(self._buttons[k].isChecked() for k in self._extra_keys):
            expanded = True
        if self._more_btn.isChecked() != expanded:
            self._more_btn.blockSignals(True)
            self._more_btn.setChecked(expanded)
            self._more_btn.blockSignals(False)
        if self.is_expanded() != expanded:
            self._more_box.setVisible(expanded)
            self.updateGeometry()
            self.expandedChanged.emit(expanded)

    def _on_more_toggled(self, checked: bool) -> None:
        self.set_expanded(checked)

    def more_button(self) -> QPushButton | None:
        return self._more_btn

    # ——— odczyt i zapis ———
    def keys(self) -> list[str]:
        return list(self._order)

    def button(self, key: str) -> QPushButton:
        return self._buttons[key]

    def values(self) -> list[str]:
        """Zaznaczone klucze w kolejności grupy."""
        return [k for k in self._order if self._buttons[k].isChecked()]

    def value(self) -> str:
        sel = self.values()
        return sel[0] if sel else (self._order[0] if self._order else "")

    def set_values(self, keys: Iterable[str], *, emit: bool = False) -> None:
        wanted = [k for k in keys if k in self._buttons]
        if not wanted and self._order:
            wanted = [self._order[0]]
        if not self._multi:
            wanted = wanted[:1]
        self._syncing = True
        try:
            for key, btn in self._buttons.items():
                want = key in wanted
                if btn.isChecked() != want:
                    # QButtonGroup w trybie wyłącznym nie pozwala odznaczyć przez setChecked(False)
                    self._group.setExclusive(False)
                    btn.setChecked(want)
                    self._group.setExclusive(not self._multi)
        finally:
            self._syncing = False
        self.set_expanded(self.is_expanded())  # zaznaczona wartość z ukrytego rzędu rozwija go
        if emit:
            self.changed.emit()

    def set_value(self, key: str, *, emit: bool = False) -> None:
        self.set_values([key], emit=emit)

    def set_key_enabled(self, key: str, enabled: bool, tooltip: str | None = None) -> None:
        btn = self._buttons[key]
        btn.setEnabled(enabled)
        if tooltip is not None:
            btn.setToolTip(tooltip)

    # ——— reakcja na klik ———
    def _on_toggled(self, key: str, checked: bool) -> None:
        if self._syncing:
            return
        if self._multi and not checked and not self.values():
            # ostatniej pigułki nie da się wyłączyć (jak ostatniego formatu na liście rozwijanej)
            self._syncing = True
            try:
                self._buttons[key].setChecked(True)
            finally:
                self._syncing = False
            return
        if not self._multi and not checked:
            return  # w trybie wyłącznym liczy się zdarzenie nowo zaznaczonej
        if key in self._extra_keys:
            self.set_expanded(self.is_expanded())
        self.changed.emit()


# ——— rozszerzenia wyjściowe (tryb zaawansowany) ———
# Kolejność wyświetlania: najczęstsze w pierwszym rzędzie, rzadsze w drugim. Kolejność w ``selected_formats`` zostaje
# jak w dawnej liście rozwijanej (PRIMARY_FORMATS): to ona decyduje, który format jest „pierwszy” (okno Ustawienia…).
_FORMAT_ROWS: tuple[tuple[tuple[str, str], ...], ...] = (
    (("png", "PNG"), ("jpeg", "JPG"), ("webp", "WebP"), ("avif", "AVIF"), ("gif", "GIF")),
    (("tiff", "TIFF"), ("heic", "HEIC"), ("bmp", "BMP"), ("jp2", "JPEG 2000"), ("pdf", "PDF")),
)
PRIMARY_FORMATS = ("webp", "jpeg", "png", "avif", "gif", "tiff", "heic", "bmp", "jp2", "pdf")
FORMAT_PILL_LABELS: dict[str, str] = {key: label for row in _FORMAT_ROWS for key, label in row}


def canonical_format_key(fmt: str) -> str:
    key = fmt.lower().strip()
    return "jpeg" if key in ("jpg", "jpeg") else key


class FormatPills(QWidget):
    """Rozszerzenia zapisu jako pigułki wielokrotnego wyboru (10 formatów w dwóch rzędach).

    Ma ten sam interfejs co ``FormatMultiCombo`` (``selected_formats``, ``set_selected``, ``apply_format_state``,
    ``set_alpha_only_mode``, ``first_selected``, ``selectionChanged``), więc okno główne, sesja i presety nie wiedzą,
    którego z nich używają. Tryb „tylko z przezroczystością” (usuwanie tła): formaty bez alfa są wyłączone.
    """

    selectionChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("formatPills")
        rows: list[list[PillSpec]] = []
        for row in _FORMAT_ROWS:
            specs = [
                (key, label, FORMAT_EXTENSION_TIPS.get(key, label))
                for key, label in row
                if key in OUTPUT_FORMATS
            ]
            if specs:
                rows.append(specs)
        self._group = PillGroup(rows, multi=True, more=("Inne", "Rzadsze rozszerzenia: TIFF, HEIC, BMP, JPEG 2000, PDF"))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._group)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._alpha_only_mode = False
        self._formats_before_alpha: list[str] = []
        self._group.changed.connect(self.selectionChanged)
        self._group.set_values(["webp"])

    # ——— zgodność z FormatMultiCombo ———
    def selected_formats(self) -> list[str]:
        have = set(self._group.values())
        return [k for k in PRIMARY_FORMATS if k in have]

    def first_selected(self) -> str:
        sel = self.selected_formats()
        return sel[0] if sel else "jpeg"

    def set_selected(self, keys: list[str]) -> None:
        keys = [canonical_format_key(k) for k in keys if k] or ["webp"]
        if self._alpha_only_mode:
            keys = [k for k in keys if k in ALPHA_OUTPUT_FORMATS] or ["png"]
        self._group.set_values(keys)
        self.selectionChanged.emit()

    def set_alpha_only_mode(self, enabled: bool) -> None:
        """Ogranicza wybór do formatów z kanałem alpha (PNG/WebP/AVIF)."""
        if enabled == self._alpha_only_mode:
            self._apply_alpha_states()
            return
        self._alpha_only_mode = enabled
        if enabled:
            self._formats_before_alpha = self.selected_formats()
            allowed = [f for f in self._formats_before_alpha if f in ALPHA_OUTPUT_FORMATS] or ["png"]
            self.set_selected(allowed)
        else:
            self.set_selected(self._formats_before_alpha or ["webp"])
            self._formats_before_alpha = []
        self._apply_alpha_states()

    def apply_format_state(self, keys: list[str], *, alpha_only: bool) -> None:
        """Atomowo ustawia format i tryb alpha (presety — bez mieszania stanu); bez sygnału."""
        normalized = [canonical_format_key(k) for k in keys if k] or ["webp"]
        if alpha_only:
            normalized = [k for k in normalized if k in ALPHA_OUTPUT_FORMATS] or ["png"]
        self._alpha_only_mode = alpha_only
        self._formats_before_alpha = []
        self._group.set_values(normalized)
        self._apply_alpha_states()

    def _apply_alpha_states(self) -> None:
        for key in self._group.keys():
            if self._alpha_only_mode and key not in ALPHA_OUTPUT_FORMATS:
                self._group.set_key_enabled(key, False, _ALPHA_NO_TRANSPARENCY_TIP)
            else:
                tip = (
                    FORMAT_ALPHA_TIPS[key]
                    if self._alpha_only_mode and key in FORMAT_ALPHA_TIPS
                    else FORMAT_EXTENSION_TIPS.get(key, key.upper())
                )
                self._group.set_key_enabled(key, True, tip)

    def pill(self, key: str) -> QPushButton:
        """Pigułka formatu (testy i zrzuty)."""
        return self._group.button(canonical_format_key(key))
