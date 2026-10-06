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
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

DISPLAY_OBJECTS = frozenset(
    {
        "panelTitle",
        "sectionStepTitle",
        "helpGuideTitle",
        "saveChoiceTitle",
        "conversionOverlayTitle",
        "appTitleLabel",
        "changelogVersion",
        "updateToastTitle",
        "stepNumber",
        "dropEmptyTitle",
    }
)
EYEBROW_OBJECTS = frozenset({"sectionTitle", "formatChipCaption"})
EYEBROW_LETTER_SPACING_EM = 0.09  # wzorzec (program „Stwórz prezentację”): ok. 0,08–0,1 em
EYEBROW_FALLBACK_PX = 14  # rozmiar, gdy czcionka nie ma jeszcze pikseli (QSS nadaje 14 px)
# DS 2.0.6 (S18): WERSALIKI tylko na przycisku głównym (zielonym) i na jednym drugorzędnym z obrysem w grupie.
# Cichy przycisk, żółty CTA („Konwertuj”), linki i przyciski-ikony: zwykła wielkość liter (Lato 700). QSS nie ma
# text-transform, więc robi to filtr zdarzeń — decyzja zapada w CHWILI zdarzenia z BIEŻĄCEGO stanu przycisku
# (nazwa obiektu i właściwość ``quiet`` zmieniają się w trakcie życia: rząd nad listą plików przełącza ``toolBtn`` ↔
# ``iconBtn``, ``mark_quiet`` bywa wołane po zbudowaniu), a przycisk, który przestał się kwalifikować, TRACI wersaliki.
#
# Nie-wersalikowe po nazwie obiektu: linki (S12), chipy formatu (PNG, JPG… to nazwy), przyciski-znaki (kotwice kadru,
# ✕), żółty CTA, przyciski ciche z QSS (toolBtn, btnUpdatePath — zgodne z themes.QUIET_BUTTONS) i przyciski-ikony.
# Zielone główne (primaryBtn, footerPrimary, saveChoicePrimary, updateDialogAction, updateToastInstall,
# updateStatusInstall) i wszystko, co zostaje (btnSecondary, btnBrowse, overlayAbortBtn…, o ile nie ``quiet``): wersaliki.
BUTTON_NO_UPPERCASE = frozenset(
    {
        "btnLink", "footerClose", "updateToastLater", "updateStatusCancel",  # linki
        "formatChip", "cropAnchorBtn", "iconBtn",  # chipy, znaki, same ikony
        "footerConvert",  # żółty CTA
        "toolBtn", "btnUpdatePath",  # ciche po nazwie (QSS)
    }
)
QUIET_PROPERTY = "quiet"


def _is_quiet(btn: QPushButton) -> bool:
    value = btn.property(QUIET_PROPERTY)
    return value is True or str(value).lower() == "true"


def wants_uppercase(btn: QPushButton) -> bool:
    """Czy napis przycisku ma być wersalikami — z jego BIEŻĄCEGO stanu (nazwa obiektu, właściwość ``quiet``)."""
    return btn.objectName() not in BUTTON_NO_UPPERCASE and not _is_quiet(btn)


class _TypographyFilter(QObject):
    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt API)
        # Polish = pierwsze nałożenie stylu; Show = powtórka po pokazaniu. FontChange: ponowne nałożenie arkusza
        # (zmiana motywu w działającym programie: unpolish/polish) przywraca widocznym widżetom czcionkę sprzed
        # naszej zmiany i gubi wersaliki, a nie wysyła ani Polish, ani Show (2.6.5: „Tryb prosty”, „Przywróć preset”
        # i nadtytuł „Kolory” traciły wersaliki po kliknięciu przełącznika). DynamicPropertyChange: ``quiet`` ustawione
        # po zbudowaniu przycisku. _apply / _apply_button nic nie robią, gdy stan już się zgadza, więc setFont z tego
        # miejsca się nie zapętla.
        kind = event.type()
        if kind in (QEvent.Type.Polish, QEvent.Type.Show, QEvent.Type.FontChange):
            if isinstance(obj, QLabel):
                name = obj.objectName()
                if name in DISPLAY_OBJECTS or name in EYEBROW_OBJECTS:
                    self._apply(obj, letter_spacing=name in EYEBROW_OBJECTS)
            elif isinstance(obj, QPushButton):
                self._apply_button(obj)
        elif kind == QEvent.Type.DynamicPropertyChange and isinstance(obj, QPushButton):
            if bytes(event.propertyName()).decode("utf-8", "ignore") == QUIET_PROPERTY:
                self._apply_button(obj)
        return False

    @staticmethod
    def _apply_button(btn: QPushButton) -> None:
        want = QFont.Capitalization.AllUppercase if wants_uppercase(btn) else QFont.Capitalization.MixedCase
        if btn.font().capitalization() == want:
            return
        font = QFont(btn.font())
        font.setCapitalization(want)
        btn.setFont(font)

    @staticmethod
    def _apply(obj, *, letter_spacing: bool) -> None:
        if obj.font().capitalization() == QFont.Capitalization.AllUppercase:
            return
        font = QFont(obj.font())
        font.setCapitalization(QFont.Capitalization.AllUppercase)
        if letter_spacing:
            px = font.pixelSize() if font.pixelSize() > 0 else EYEBROW_FALLBACK_PX
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, EYEBROW_LETTER_SPACING_EM * px)
        obj.setFont(font)


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
