"""Bazowy dialog — polskie przyciski, spójny motyw, okno nigdy większe niż ekran."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QWidget

from inyfinn_resizer.app.widgets.layout_helpers import fit_title_heights, pin_button_min_widths
from inyfinn_resizer.app.window_fit import frame_margins, inside

# Odstępy okien dialogowych wg design systemu Dobra Kaloria 2.0 (qt.*): margines okna 20 px,
# między sekcjami 16 px, w stosie 12 px, w rzędzie 10 px.
DIALOG_MARGIN = 20
DIALOG_SECTION_GAP = 16
DIALOG_STACK_GAP = 12
DIALOG_ROW_GAP = 10


def apply_dialog_layout(layout, *, spacing: int = DIALOG_SECTION_GAP) -> None:
    """Korzeń okna dialogowego: margines 20 px i odstęp między sekcjami (domyślnie 16 px)."""
    layout.setContentsMargins(DIALOG_MARGIN, DIALOG_MARGIN, DIALOG_MARGIN, DIALOG_MARGIN)
    layout.setSpacing(spacing)


def polish_dialog_buttons(box: QDialogButtonBox) -> None:
    mapping = {
        QDialogButtonBox.Ok: "OK",
        QDialogButtonBox.Cancel: "Anuluj",
        QDialogButtonBox.Close: "Zamknij",
        QDialogButtonBox.Reset: "Resetuj",
        QDialogButtonBox.Apply: "Zastosuj",
        QDialogButtonBox.Save: "Zapisz",
        QDialogButtonBox.Open: "Otwórz",
    }
    for role, text in mapping.items():
        btn = box.button(role)
        if btn:
            btn.setText(text)
            if role == QDialogButtonBox.Ok:
                btn.setObjectName("primaryBtn")
            elif role in (QDialogButtonBox.Cancel, QDialogButtonBox.Close):
                btn.setObjectName("btnLink")  # anulowanie i powrót = link (design system)
            else:
                btn.setObjectName("btnSecondary")
    if box.layout() is not None:
        box.layout().setSpacing(DIALOG_ROW_GAP)  # przyciski obok siebie: odstęp ≥ 8 px (styl dawał 6)


class AppDialog(QDialog):
    """Dialog dziedziczący stylesheet aplikacji; przy pierwszym pokazaniu mieści się w dostępnym obszarze ekranu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appDialog")
        self._screen_fitted = False

    def polish_button(self, btn: QPushButton, *, primary: bool = False, link: bool = False) -> None:
        btn.setObjectName("primaryBtn" if primary else "btnLink" if link else "btnSecondary")
        btn.setMinimumHeight(36)

    def setVisible(self, visible: bool) -> None:  # noqa: N802 (Qt API)
        if visible and not self._screen_fitted:
            self._screen_fitted = True
            self.fit_to_screen()
        super().setVisible(visible)

    def fit_to_screen(self, available: QRect | None = None) -> None:
        """Okno (z paskiem tytułu i ramką) nie większe niż obszar ekranu bez paska zadań; minimum też.

        Treść, która się nie mieści, przewija się wewnątrz dialogu (obszary przewijania w dialogach) — tu tylko
        przycinamy rozmiar okna i minimum do ekranu. Napisy przycisków (wersaliki są szersze) nie są ściskane.
        """
        if available is None:
            parent = self.parentWidget()
            screen = (
                (parent.screen() if parent is not None else None)
                or QGuiApplication.screenAt(QCursor.pos())
                or QGuiApplication.primaryScreen()
            )
            available = screen.availableGeometry() if screen is not None else QRect(0, 0, 1366, 720)
        pin_button_min_widths(self)
        fit_title_heights(self.findChildren(QWidget))  # tytuły Mindset: miejsce na akcenty wersalików
        frame = frame_margins(self)
        max_w = max(200, available.width() - frame.left() - frame.right())
        max_h = max(200, available.height() - frame.top() - frame.bottom())
        if self.minimumWidth() > max_w or self.minimumHeight() > max_h:
            self.setMinimumSize(min(self.minimumWidth(), max_w), min(self.minimumHeight(), max_h))
        if not self.testAttribute(Qt.WidgetAttribute.WA_Resized):
            # Bez własnego rozmiaru dialog ma rozmiar z zawartości (adjustSize() ucina do 2/3 ekranu — tu cały dostępny obszar).
            hint = self.sizeHint().expandedTo(self.minimumSize())
            self.resize(hint)
        size = QSize(min(self.width(), max_w), min(self.height(), max_h))
        if size != self.size():
            self.resize(size)
        # Pozycja: środek rodzica (albo ekranu), w całości w dostępnym obszarze.
        parent = self.parentWidget()
        outer = QSize(size.width() + frame.left() + frame.right(), size.height() + frame.top() + frame.bottom())
        center = parent.frameGeometry().center() if parent is not None and parent.isVisible() else available.center()
        want = QPoint(center.x() - outer.width() // 2, center.y() - outer.height() // 2)
        self.move(inside(available, outer, want))
