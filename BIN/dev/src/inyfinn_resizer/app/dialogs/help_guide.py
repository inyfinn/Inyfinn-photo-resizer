"""Przewodnik użytkownika — Pomoc w menu aplikacji."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.widgets.layout_helpers import SECTION_GAP, make_section


def _help_sections() -> list[tuple[str, list[str]]]:
    return [
        (
            "Szybki start",
            [
                "Przeciągnij zdjęcia na listę po lewej lub użyj Dodaj pliki / Dodaj folder.",
                "Ustaw format i jakość, wybierz folder wyjściowy, kliknij Konwertuj.",
                "Prawy przycisk myszy na liście: konwersja wybranych, usuń, otwórz folder, kopiuj ścieżkę.",
            ],
        ),
        (
            "Lista plików",
            [
                "Dodaj pliki lub cały folder ze zdjęciami.",
                "Sortuj po nazwie lub rozmiarze.",
                "Podgląd zaznaczonego pliku w sekcji Więcej.",
            ],
        ),
        (
            "Format",
            [
                "Domyślnie WebP. Przy pierwszym dodanym pliku format dopasowuje się do niego (tylko raz na sesję).",
                "Po ręcznej zmianie ustawień format nie zmienia się automatycznie.",
                "WebP, JPG, PNG, AVIF, GIF i inne — jeden lub wiele naraz.",
                "Segreguj do podfolderów — osobne katalogi webp/, jpg/ przy wielu formatach.",
                "Sekwencja wizek — kompresja in-place XL/L/S/SKLEP w folderze źródłowym.",
            ],
        ),
        (
            "Kompresja",
            [
                "Jakość — suwak dla JPG, WebP i AVIF.",
                "Kolory PNG — auto z jakości: 256 przy 100%, 160 przy 50%, 24 przy 10% i mniej.",
                "Program wykrywa rzadkie akcenty (np. zieleń) i chroni je przed utratą.",
            ],
        ),
        (
            "Rozmiar i zapis",
            [
                "Preset rozmiaru — szybkie skalowanie bez otwierania Zaawansowane.",
                "Folder wyjściowy — pomijany przy sekwencji wizek.",
            ],
        ),
        (
            "Zaawansowane i nazwy",
            [
                "Zaawansowane — skalowanie, obrót, odbicia, EXIF, filtry.",
                "Zmiana nazw — szablon {name}_{counter:04d} w zakładce Zmiana nazw.",
            ],
        ),
        (
            "Menu",
            [
                "Plik — wczytaj / zapisz preset JSON.",
                "Narzędzia — motyw jasny / ciemny.",
                "Pomoc — ten przewodnik.",
            ],
        ),
    ]


class HelpGuideDialog(AppDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpGuideDialog")
        self.setWindowTitle("Pomoc — Inyfinn Photo Resizer")
        self.setMinimumSize(520, 460)
        self.resize(580, 520)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 12, 14, 12)

        intro = QLabel(
            f"Wsadowa konwersja i kompresja zdjęć. "
            f"Wersja {__version__}."
        )
        intro.setObjectName("helpGuideIntro")
        intro.setWordWrap(True)
        root.addWidget(intro)

        scroll = QScrollArea()
        scroll.setObjectName("helpGuideScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("helpGuideBody")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 4, 0)
        body_lay.setSpacing(SECTION_GAP)

        for title, bullets in _help_sections():
            box, lay = make_section(title)
            for line in bullets:
                item = QLabel(f"• {line}")
                item.setObjectName("helpGuideItem")
                item.setWordWrap(True)
                lay.addWidget(item)
            body_lay.addWidget(box)

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        polish_dialog_buttons(buttons)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)
        root.addWidget(buttons)


def show_help_guide(parent=None) -> None:
    HelpGuideDialog(parent).exec()
