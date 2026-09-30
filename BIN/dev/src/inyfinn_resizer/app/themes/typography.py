"""Typografia Dobra Kaloria, której QSS nie umie: wersaliki i odstęp liter.

QSS ustawia krój, rozmiar i kolor (app.qss). Filtr zdarzeń dokłada do czcionki etykiety:
- nagłówki (Mindset, wielkie litery) — obiekty z ``DISPLAY_OBJECTS``,
- etykiety sekcji / eyebrow (Lato Bold, wielkie litery, odstęp ~0,1 em) — ``EYEBROW_OBJECTS``.
Tekst etykiet się nie zmienia (tylko sposób rysowania), więc kod i testy widzą ten sam napis.
Sprawdzone: po zmianie motywu (setStyleSheet) wersaliki i krój zostają.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel

DISPLAY_OBJECTS = frozenset(
    {
        "panelTitle",
        "sectionStepTitle",
        "helpGuideTitle",
        "saveChoiceTitle",
        "conversionOverlayTitle",
        "appTitleLabel",
        "changelogVersion",
    }
)
EYEBROW_OBJECTS = frozenset({"sectionTitle", "formatChipCaption"})
EYEBROW_LETTER_SPACING = 110.0  # procent — ok. 0,1 em


class _TypographyFilter(QObject):
    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt API)
        if event.type() == QEvent.Type.Polish and isinstance(obj, QLabel):
            name = obj.objectName()
            if name in DISPLAY_OBJECTS or name in EYEBROW_OBJECTS:
                font = QFont(obj.font())
                font.setCapitalization(QFont.Capitalization.AllUppercase)
                if name in EYEBROW_OBJECTS:
                    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, EYEBROW_LETTER_SPACING)
                obj.setFont(font)
        return False


_FILTER: _TypographyFilter | None = None


def install_typography(app: QApplication) -> None:
    """Instaluje filtr raz na aplikację (wywołuje apply_theme)."""
    global _FILTER
    if _FILTER is None:
        _FILTER = _TypographyFilter(app)
        app.installEventFilter(_FILTER)


def styled_font(obj: QLabel) -> QFont:
    """Dla testów: czcionka po nałożeniu stylu."""
    obj.ensurePolished()
    return obj.font()
