"""Siatki, które same przestawiają się przy zmianie szerokości (design system DK 26.3 / 26.8).

Qt nie ma zapytań o szerokość kontenera (CSS ``@media``), więc przełączenie robi ``resizeEvent``: gdy jest miejsce,
układ szeroki, inaczej wąski. Próg to MINIMUM układu szerokiego, więc w żadnym stanie dzieci nie są ściskane poniżej
swojego minimum (nic nie nachodzi na siebie i nic nie jest ucięte). ``minimumSizeHint`` zwraca minimum układu
WĄSKIEGO, żeby okno dało się zwęzić do tej szerokości.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget

FORM_LABEL_W = 150  # DS 26.3: etykiety ~150 px, jedna kolumna
FORM_HGAP = 16
FORM_VGAP = 12
STACK_LABEL_GAP = 4


class FormGrid(QWidget):
    """Siatka ``etykieta | pole``; przy wąskiej szerokości etykieta stoi nad polem."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        label_w: int = FORM_LABEL_W,
        hgap: int = FORM_HGAP,
        vgap: int = FORM_VGAP,
        label_name: str = "fieldLabel",
    ) -> None:
        super().__init__(parent)
        self._label_name = label_name
        self._label_w = label_w
        self._hgap = hgap
        self._vgap = vgap
        self._rows: list[tuple[QLabel | None, QWidget]] = []  # etykieta None = wiersz na całą szerokość
        self._wide = True
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    # ——— budowa ———
    def add_row(self, label: str, field: QWidget, *, tooltip: str = "", top_pad: int = 0) -> QLabel:
        """Dodaje wiersz. ``top_pad`` > 0: etykieta stoi przy GÓRZE pola (np. rząd pigułek wielowierszowy), o tyle px niżej."""
        lbl = QLabel(label, self)
        lbl.setProperty("topPad", top_pad)
        lbl.setObjectName(self._label_name)
        lbl.setWordWrap(False)
        if tooltip:
            lbl.setToolTip(tooltip)
        if not label:
            lbl.setVisible(False)  # np. pole wyboru w kolumnie pól, bez nazwy
        field.setParent(self)
        self._rows.append((lbl, field))
        self._relayout()
        return lbl

    def add_span(self, widget: QWidget) -> None:
        """Wiersz na całą szerokość (np. tytuł podsekcji, linia)."""
        widget.setParent(self)
        self._rows.append((None, widget))
        self._relayout()

    def set_row_visible(self, field: QWidget, visible: bool) -> None:
        for lbl, f in self._rows:
            if f is field:
                if lbl is not None and lbl.text():
                    lbl.setVisible(visible)
                f.setVisible(visible)
        self._relayout()

    def is_wide(self) -> bool:
        return self._wide

    def set_gaps(self, *, vgap: int | None = None, hgap: int | None = None) -> None:
        """Odstępy z gęstości okna (``window_fit.DENSITIES``): wiersze bliżej siebie na niskim ekranie."""
        if vgap is not None:
            self._vgap = vgap
        if hgap is not None:
            self._hgap = hgap
        self._relayout()

    # ——— przełączanie układu ———
    def _field_min_w(self) -> int:
        return max((f.minimumSizeHint().width() for _l, f in self._rows), default=0)

    def _label_min_w(self) -> int:
        return max((lbl.sizeHint().width() for lbl, _f in self._rows if lbl is not None and lbl.text()), default=0)

    def wide_threshold(self) -> int:
        """Najmniejsza szerokość, przy której układ szeroki mieści pola bez ściskania."""
        return max(self._label_w, self._label_min_w()) + self._hgap + self._field_min_w()

    def minimumSizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return QSize(max(self._field_min_w(), self._label_min_w()), self._narrow_height())

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return QSize(self.wide_threshold(), self._grid.sizeHint().height())

    def _narrow_height(self) -> int:
        return self._grid.minimumSize().height()

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        wide = self.width() >= self.wide_threshold()
        if wide != self._wide:
            self._wide = wide
            self._relayout()

    def _relayout(self) -> None:
        grid = self._grid
        for _lbl, field in self._rows:
            grid.removeWidget(field)
        for lbl, _field in self._rows:
            if lbl is not None:
                grid.removeWidget(lbl)
        for i in range(grid.rowCount() + 1):
            grid.setRowMinimumHeight(i, 0)
        for i in range(grid.columnCount() + 1):
            grid.setColumnMinimumWidth(i, 0)
            grid.setColumnStretch(i, 0)
        visible = [(l, f) for l, f in self._rows if not f.isHidden()]
        if self._wide:
            grid.setHorizontalSpacing(self._hgap)
            grid.setVerticalSpacing(self._vgap)
            grid.setColumnMinimumWidth(0, max(self._label_w, self._label_min_w()))
            grid.setColumnStretch(1, 1)
            for r, (lbl, field) in enumerate(visible):
                if lbl is None:
                    grid.addWidget(field, r, 0, 1, 2)
                    continue
                pad = int(lbl.property("topPad") or 0)
                lbl.setContentsMargins(0, pad, 0, 0)
                align = Qt.AlignmentFlag.AlignTop if pad else Qt.AlignmentFlag.AlignVCenter
                grid.addWidget(lbl, r, 0, align | Qt.AlignmentFlag.AlignLeft)
                grid.addWidget(field, r, 1)
        else:
            grid.setHorizontalSpacing(0)
            grid.setVerticalSpacing(STACK_LABEL_GAP)
            grid.setColumnStretch(0, 1)
            for r, (lbl, field) in enumerate(visible):
                base = r * 3
                if lbl is not None:
                    lbl.setContentsMargins(0, 0, 0, 0)
                    grid.addWidget(lbl, base, 0, Qt.AlignmentFlag.AlignLeft)
                grid.addWidget(field, base + 1, 0)
                # odstęp między parami: pionowy odstęp siatki to tylko mały odstęp etykieta→pole
                grid.setRowMinimumHeight(base + 2, max(0, self._vgap - 2 * STACK_LABEL_GAP) if r < len(visible) - 1 else 0)
        grid.invalidate()
        self.updateGeometry()


class SplitRow(QWidget):
    """Lewa część rośnie, prawa ma szerokość treści; przy wąskiej szerokości prawa schodzi pod lewą."""

    def __init__(self, left: QWidget, right: QWidget, parent: QWidget | None = None, *, gap: int = 16,
                 left_cap: int = 420) -> None:
        super().__init__(parent)
        self._left, self._right = left, right
        self._gap = gap
        self._left_cap = left_cap
        self._wide = True
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(gap)
        left.setParent(self)
        right.setParent(self)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._relayout()

    def wide_threshold(self) -> int:
        return min(self._left.sizeHint().width(), self._left_cap) + self._gap + self._right.minimumSizeHint().width()

    def minimumSizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return QSize(max(self._left.minimumSizeHint().width(), self._right.minimumSizeHint().width()), 0)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        wide = self.width() >= self.wide_threshold()
        if wide != self._wide:
            self._wide = wide
            self._relayout()

    def _relayout(self) -> None:
        grid = self._grid
        grid.removeWidget(self._left)
        grid.removeWidget(self._right)
        for i in range(3):
            grid.setColumnStretch(i, 0)
        if self._wide:
            grid.addWidget(self._left, 0, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(self._right, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            grid.setColumnStretch(0, 1)
        else:
            grid.addWidget(self._left, 0, 0)
            grid.addWidget(self._right, 1, 0, Qt.AlignmentFlag.AlignLeft)
            grid.setColumnStretch(0, 1)
        grid.invalidate()
        self.updateGeometry()


class ActionRow(QWidget):
    """Wiersz z jedną główną akcją: przy szerokim oknie przycisk po prawej (stała szerokość), przy wąskim na całą szerokość."""

    def __init__(self, button: QWidget, parent: QWidget | None = None, *, wide_w: int = 240, narrow_below: int = 640) -> None:
        super().__init__(parent)
        self.button = button
        self._wide_w = wide_w
        self._narrow_below = narrow_below
        self._wide: bool | None = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._lay = lay
        lay.addStretch(1)
        lay.addWidget(button)
        self._apply(True)

    def _apply(self, wide: bool) -> None:
        if wide == self._wide:
            return
        self._wide = wide
        if wide:
            self.button.setMinimumWidth(self._wide_w)
            self.button.setMaximumWidth(self._wide_w)
            self._lay.setStretch(0, 1)
        else:
            self.button.setMinimumWidth(0)
            self.button.setMaximumWidth(16777215)
            self._lay.setStretch(0, 0)
        self._lay.invalidate()
        self.updateGeometry()

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        self._apply(self.width() >= self._narrow_below)
