"""Karta sekcji zwijana z podsumowaniem (design system DK 26.3).

Biała karta (L2) na szarym panelu (L1): nagłówek (tytuł Mindset, akcja karty, strzałka), pod nim treść. Klik w nagłówek
albo w strzałkę zwija kartę do tytułu i jednej linii podsumowania (np. „Tło zostaje · segreguj do podfolderów”).
Stan zwinięcia zgłasza sygnał ``collapsedChanged``; zapamiętuje go okno główne (``user_settings``).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from inyfinn_resizer.app.widgets.layout_helpers import set_themed_icon
from inyfinn_resizer.app.widgets.tool_icons import icon_chevron_down, icon_chevron_up

CHEVRON_SIDE = 32


class _ClickableHeader(QWidget):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCardHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SectionCard(QFrame):
    """Karta z nagłówkiem. ``body`` to widżet na treść (``body_layout`` — jego układ pionowy)."""

    collapsedChanged = Signal(bool)

    def __init__(
        self,
        key: str,
        title: str,
        *,
        tooltip: str = "",
        collapsible: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        self.key = key
        self._collapsed = False
        self._summary_text = ""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        if tooltip:
            self.setToolTip(tooltip)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(24, 18, 24, 20)
        self._outer.setSpacing(10)

        self.header = _ClickableHeader(self)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(12)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionCardTitle")
        self.header_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addStretch(1)
        self.chevron = QPushButton()
        self.chevron.setObjectName("cardChevron")
        self.chevron.setFixedSize(CHEVRON_SIDE, CHEVRON_SIDE)
        self.chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chevron.setAccessibleName(f"{title}: zwiń albo rozwiń")
        self.chevron.clicked.connect(self.toggle)
        self.header_layout.addWidget(self.chevron, 0, Qt.AlignmentFlag.AlignVCenter)
        self.header.clicked.connect(self.toggle)
        self.collapsible = collapsible
        if not collapsible:  # np. okno Opcje zaawansowane: karta z przełącznikiem, bez zwijania
            self.chevron.setVisible(False)
            self.header.setCursor(Qt.CursorShape.ArrowCursor)
        self._outer.addWidget(self.header)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("sectionCardSummary")
        self.summary_label.setWordWrap(True)
        self.summary_label.setVisible(False)
        self._outer.addWidget(self.summary_label)

        self.body = QWidget(self)
        self.body.setObjectName("sectionCardBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        self._outer.addWidget(self.body)
        self._sync_chevron()

    # ——— akcje w nagłówku ———
    def add_header_action(self, widget: QWidget) -> None:
        """Akcja karty (np. „Ustawienia…”) stoi przed strzałką, równo z tytułem."""
        self.header_layout.insertWidget(self.header_layout.count() - 1, widget, 0, Qt.AlignmentFlag.AlignVCenter)

    # ——— stan ———
    def is_collapsed(self) -> bool:
        return self._collapsed

    def set_collapsed(self, collapsed: bool, *, emit: bool = True) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.body.setVisible(not collapsed)
        self._sync_summary()
        self._sync_chevron()
        self.updateGeometry()
        if emit:
            self.collapsedChanged.emit(collapsed)

    def toggle(self) -> None:
        if self.collapsible:
            self.set_collapsed(not self._collapsed)

    def set_summary(self, text: str) -> None:
        # ostatnie słowo przywiązane twardą spacją — bez wdowy w ostatnim wierszu (S45)
        head, sep, tail = text.rpartition(" ")
        self._summary_text = f"{head} {tail}" if sep else text
        self._sync_summary()

    def summary(self) -> str:
        return self._summary_text

    def _sync_summary(self) -> None:
        self.summary_label.setText(self._summary_text)
        self.summary_label.setVisible(self._collapsed and bool(self._summary_text))

    def _sync_chevron(self) -> None:
        set_themed_icon(self.chevron, icon_chevron_down if self._collapsed else icon_chevron_up)
        self.chevron.setToolTip("Rozwiń sekcję" if self._collapsed else "Zwiń sekcję")

    def apply_padding(self, pad: int, pad_top: int, pad_bottom: int | None = None, gap: int | None = None) -> None:
        """Wypełnienie i odstęp nagłówek → treść wg gęstości okna (``window_fit.DENSITIES``)."""
        self._outer.setContentsMargins(pad, pad_top, pad, pad if pad_bottom is None else pad_bottom)
        if gap is not None:
            self._outer.setSpacing(gap)
