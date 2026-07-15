"""Przewodnik użytkownika — Pomoc w menu aplikacji."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.widgets.layout_helpers import SECTION_GAP
from inyfinn_resizer.app.widgets.section_icons import help_section_pixmap


def _help_sections() -> list[tuple[str, str, list[str]]]:
    return [
        (
            "start",
            "Szybki start",
            [
                "Przeciągnij zdjęcia na listę po lewej lub użyj Dodaj pliki / Dodaj folder.",
                "Ustaw format, jakość i wymiary, wybierz folder wyjściowy, kliknij Konwertuj.",
                "Prawy przycisk myszy na liście: konwersja wybranych, usuń, otwórz folder, kopiuj ścieżkę.",
                "Motyw jasny / ciemny przełączasz w prawym górnym rogu okna.",
            ],
        ),
        (
            "list",
            "Lista plików",
            [
                "Dodaj pojedyncze pliki lub cały folder ze zdjęciami.",
                "Sortuj po nazwie lub rozmiarze pliku.",
                "Zaznacz wiersz, aby zobaczyć podgląd i metadane w panelu pod listą.",
                "Przy wielu folderach źródłowych program zapyta, gdzie zapisać wyniki.",
            ],
        ),
        (
            "format",
            "Format i jakość",
            [
                "Domyślnie WebP. Przy pierwszym dodanym pliku format dopasowuje się do niego (tylko raz na sesję).",
                "Po ręcznej zmianie ustawień format nie zmienia się automatycznie.",
                "WebP, JPG, PNG, AVIF, GIF i inne — jeden format lub wiele naraz.",
                "Segreguj do podfolderów tworzy osobne katalogi webp/, jpg/ przy wielu formatach.",
                "Sekwencja wizek (XL/L/S/SKLEP) kompresuje pliki w miejscu w folderze źródłowym.",
                "Usuń tło — opcjonalna separacja tła z wyborem modelu jakości lub szybkości.",
                "Ustawienia… otwiera szczegóły formatu: PNG-8/24, tło JPG, GIF, kadrowanie.",
            ],
        ),
        (
            "compression",
            "Kompresja",
            [
                "Jakość — suwak dla JPG, WebP i AVIF (scroll myszy: co 10, Shift co 100, Ctrl co 1).",
                "Kolory PNG — auto z jakości: 256 przy 100%, 160 przy 50%, 24 przy 10% i mniej.",
                "Program wykrywa rzadkie akcenty (np. zieleń) i chroni je przed utratą.",
            ],
        ),
        (
            "dimensions",
            "Wymiary",
            [
                "Skala — procent oryginalnego rozmiaru.",
                "Min. najdłuższa krawędź — ogranicza dłuższy bok po skalowaniu.",
                "Preset formatu — szybkie proporcje (np. kwadrat, 4:5) bez otwierania Zaawansowane.",
                "Zaawansowane — obrót, odbicia, EXIF, filtry i dokładne kadrowanie.",
            ],
        ),
        (
            "save",
            "Zapis plików",
            [
                "Zapisz do folderu wyjściowego — wyniki trafiają do wskazanego katalogu.",
                "Aktualizuj ścieżkę proponuje folder obok plików źródłowych po dodaniu listy.",
                "Zachowaj strukturę folderów — odtwarza podfoldery względem wspólnego korzenia.",
                "Zachowaj datę i godzinę — kopiuje znaczniki czasu z pliku źródłowego.",
                "Pytaj przed nadpisaniem — ostrzeżenie, gdy plik docelowy już istnieje.",
                "Wiele plików naraz — równoległa konwersja wsadowa (szybsza na wielu plikach).",
                "Folder wyjściowy jest pomijany w trybie sekwencji wizek.",
            ],
        ),
        (
            "advanced",
            "Presety i nazwy",
            [
                "Plik — wczytaj / zapisz preset JSON ze wszystkimi ustawieniami.",
                "Zmiana nazw — szablon {name}_{counter:04d} w oknie Zmiana nazw.",
                "Własne presety wymiarów zapisujesz z listy Format w sekcji Wymiary.",
            ],
        ),
        (
            "update",
            "Aktualizacje",
            [
                "Program sprawdza nową wersję automatycznie po starcie (w wersji EXE).",
                "Pobieranie aktualizacji działa w tle — postęp widać w lewym dolnym rogu okna.",
                "Po pobraniu kliknij Zainstaluj — program zapyta o potwierdzenie i pokaże okno instalacji.",
                "Ręczne sprawdzenie: Pomoc → Sprawdź aktualizacje…",
            ],
        ),
        (
            "menu",
            "Menu",
            [
                "Plik — wczytaj / zapisz preset JSON, zamknij aplikację.",
                "Narzędzia — motyw, zaawansowane, zmiana nazw, sprawdź aktualizacje.",
                "Pomoc — ten przewodnik i informacje o wersji.",
            ],
        ),
    ]


def _make_help_section(section_key: str, title: str, bullets: list[str]) -> QFrame:
    box = QFrame()
    box.setObjectName("helpGuideSection")
    outer = QVBoxLayout(box)
    outer.setContentsMargins(12, 10, 12, 10)
    outer.setSpacing(8)

    header = QWidget()
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(10)

    icon = QLabel()
    icon.setPixmap(help_section_pixmap(section_key, size=32))
    icon.setFixedSize(32, 32)
    header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

    title_lbl = QLabel(title)
    title_lbl.setObjectName("helpGuideTitle")
    title_lbl.setWordWrap(True)
    header_row.addWidget(title_lbl, stretch=1)
    outer.addWidget(header)

    for line in bullets:
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(42, 0, 0, 0)
        row_lay.setSpacing(8)
        dot = QLabel("•")
        dot.setFixedWidth(10)
        dot.setObjectName("helpGuideBullet")
        item = QLabel(line)
        item.setObjectName("helpGuideItem")
        item.setWordWrap(True)
        row_lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        row_lay.addWidget(item, stretch=1)
        outer.addWidget(row)

    return box


class HelpGuideDialog(AppDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpGuideDialog")
        self.setWindowTitle("Pomoc — Inyfinn Photo Resizer")
        self.setMinimumSize(560, 520)
        self.resize(640, 680)

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

        for section_key, title, bullets in _help_sections():
            body_lay.addWidget(_make_help_section(section_key, title, bullets))

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
