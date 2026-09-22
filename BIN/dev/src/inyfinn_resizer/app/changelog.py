"""Wbudowany changelog — Pomoc → Changelog (zawsze w EXE)."""

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
from inyfinn_resizer.app.widgets.layout_helpers import SECTION_GAP

# Najnowsza wersja pierwsza. Aktualizuj przy każdym wydaniu.
CHANGELOG: list[tuple[str, str, list[str]]] = [
    (
        "2.5.2",
        "2026-09-22",
        [
            "GIF z filmu bierze wymiary z filmu. Zamiast szerokości w pikselach jest „Rozmiar” od 1% do 100% — 100% to oryginał, 50% z filmu 1000 px daje 500 px. Program nigdy nie powiększa.",
            "Nowe ustawienie „Klatki na sekundę” — tempo gotowego GIF-a. Zastępuje mylce „próbkowanie filmu”.",
            "ULTRA ma własne pole „liczba zatrzymań”, a limit klatek trybu równomiernego nie przycina już po cichu dłuższych filmów.",
            "Tryb prosty pyta o jedną liczbę zależnie od trybu: klatki na sekundę albo liczbę zatrzymań.",
        ],
    ),
    (
        "2.5.1",
        "2026-09-21",
        [
            "Tryb prosty obsługuje filmy: wrzuć MP4, MOV albo WebM i naciśnij Konwertuj — wyjdzie GIF.",
            "Gdy na liście jest film, pojawia się kafelek „Film → GIF” z wyborem trybu (płynnie albo ULTRA) i liczby klatek. Przy samych zdjęciach kafelek jest schowany.",
            "Film ma na liście własną ikonę, więc nie myli się ze zdjęciem.",
        ],
    ),
    (
        "2.5.0",
        "2026-09-21",
        [
            "Filmy → GIF. Wrzuć MP4, MOV, WebM, MKV lub AVI — program zrobi z nich GIF-a.",
            "Tryb ULTRA: fragmenty, w których obraz stoi, stają się jedną klatką trzymaną tyle samo czasu. Długość animacji zostaje bez zmian, a plik jest wielokrotnie mniejszy.",
            "W Ustawieniach GIF: liczba klatek, szerokość i tryb (równomiernie albo ULTRA).",
        ],
    ),
    (
        "2.4.12",
        "2026-09-18",
        [
            "PNG → JPG: czerwienie i drobny kolorowy tekst nie bledną — od jakości 70% JPG zapisuje kolor w pełnej dokładności (4:4:4). Wymiary obrazu bez zmian.",
            "JPG zapisuje się raz — wcześniej był kodowany ponownie kilka razy, a każde kodowanie traciło jakość.",
            "Suwak jakości znów działa dla zdjęć z zielonymi detalami poniżej 70% (wcześniej zawsze wychodziło 92%).",
            "Ustawienia JPG → „Dokładność koloru”: automatycznie / pełny kolor / oszczędny.",
            "Lista plików: zaznaczanie z Ctrl i Shift, usuwanie klawiszem Delete, ikoną ✕ przy pliku i z menu pod prawym przyciskiem.",
            "Tryb prosty nie wpisuje już sam folderu z poprzedniej sesji. Bez wybranego folderu program pyta, gdzie zapisać.",
            "Okno wyników pokazuje, gdzie zapisano pliki, i ma przycisk „Pokaż w folderze”.",
            "Wybór folderu otwiera się przy zdjęciach, a nie w folderze programu.",
        ],
    ),
    (
        "2.4.11",
        "2026-09-18",
        [
            "Tryb prosty: przyciski mają równą wysokość — Konwertuj i PNG/JPG/AVIF po 36 px w jednej linii, pozostałe kontrolki po 32 px.",
            "Pole ścieżki i „Wybierz folder…” mają tę samą wysokość, a ścieżka jest czytelniejsza.",
        ],
    ),
    (
        "2.4.10",
        "2026-09-18",
        [
            "Program nie zamyka się już nagle podczas pobierania aktualizacji (zdarzało się przy wolnym łączu).",
            "To samo zabezpieczenie po anulowaniu konwersji — przerwana konwersja nie może zamknąć programu.",
            "Diagnostyka: zmienna INYFINN_STDERR_FILE zapisuje komunikaty błędów do pliku.",
        ],
    ),
    (
        "2.4.9",
        "2026-09-18",
        [
            "Bez zmian w programie — wydanie sprawdzające, czy aktualizacja instaluje się sama.",
        ],
    ),
    (
        "2.4.8",
        "2026-09-17",
        [
            "Instalator ma ~200 MB zamiast 2 GB. Model usuwania tła pobiera się raz, przy pierwszym użyciu „Usuń tło” (Szybko 214 MB, Najlepsza jakość 928 MB), z paskiem postępu i kontrolą sumy SHA256.",
            "Naprawione usuwanie tła na nowym komputerze: w paczce były uszkodzone pliki modeli, przez co program po cichu pobierał 1 GB przy pierwszym użyciu.",
            "Aktualizacja sprawdza sumę kontrolną pobranej paczki i zamyka tylko tę kopię aplikacji, którą aktualizuje.",
            "Animacje: GIF → WebP, animowany WebP → GIF/WebP i GIF ze zmianą wymiaru zachowują wszystkie klatki i czasy (wcześniej zostawała jedna klatka).",
            "Suwak Skali działa także dla GIF — wcześniej plik był tylko kopiowany bez zmiany wymiaru.",
            "JPEG2000: plik .jp2 jest prawdziwym JPEG2000 (wcześniej był to zwykły JPEG ze złym rozszerzeniem).",
            "Dezinstalator usuwa folder logs — koniec komunikatu „niektóre elementy nie mogły zostać usunięte”.",
        ],
    ),
    (
        "2.4.7",
        "2026-09-15",
        [
            "Instalator podpisany Authenticode (wydawca Inyfinn) — bez „Nieznany wydawca” na stacji z certyfikatem.",
            "Stare setup.exe są usuwane przy nowym buildzie, żeby nie odpalać 2.4.2 zamiast bieżącej wersji.",
        ],
    ),
    (
        "2.4.6",
        "2026-09-15",
        [
            "Usuwanie tła: sieć na wymiarze wyjścia (max 2560 px), nie na pełnym 20 MP.",
            "Alpha matting tylko do 1600 px — na większych wieszało partię.",
            "Kompresja PNG szybsza: pngquant bez trybu 1, oxipng -o 1 --fast, bez Pillow optimize.",
            "EXE nie serializuje już całej konwersji jedną kłódką — tylko sam inference rembg.",
        ],
    ),
    (
        "2.4.5",
        "2026-09-14",
        [
            "Anulowanie konwersji działa: kolejka odpada od razu, overlay znika po Tak.",
            "Dialog „Przerwać konwersję?” nie chowa się pod overlayem.",
        ],
    ),
    (
        "2.4.4",
        "2026-09-14",
        [
            "Overlay konwersji: czytelne nazwy plików, bez nachodzących liter i zlepionego „PNG” z nazwą.",
            "Pasek postępu na kafelku ma własny tor — widać go od pierwszych procentów.",
        ],
    ),
    (
        "2.4.3",
        "2026-09-14",
        [
            "Naprawiony start: ucięty results_dialog i śmieci na końcu main_window nie blokują już splasha.",
            "Gdy uruchomienie się wywali, widać komunikat z błędem zamiast wiecznego kółka.",
        ],
    ),
    (
        "2.4.2",
        "2026-09-10",
        [
            "Tryb prosty bez folderu: pytanie, czy nadpisać oryginały, czy zapisać obok z dopiskiem _conv.",
            "PNG poniżej 70% jakości schodzi z PNG-24 na PNG-8 (paleta) — dużo mniejszy plik, przezroczystość zostaje.",
            "PNG bez tła zostaje PNG bez tła. Format wyjścia = format oryginału, chyba że wybierzesz inny.",
            "Obok Konwertuj: trzy przyciski w obrysie PNG / JPG / AVIF — konwersja do innego formatu.",
            "Dopracowane okna postępu i wyników (pełne nazwy, czytelna oszczędność, bez mylącego „Kompresja 100%”).",
            "Pomoc → Changelog — lista zmian każdej wersji.",
        ],
    ),
    (
        "2.3.1",
        "2026-09-01",
        [
            "Domyślny start w trybie prostym.",
            "Poprawki układu kafelków i nagłówka.",
        ],
    ),
    (
        "2.3.0",
        "2026-09-01",
        [
            "Tryb prosty i zaawansowany (przełącznik w nagłówku).",
            "Prosty przepływ: wrzuć zdjęcia → jakość → folder → Konwertuj.",
        ],
    ),
    (
        "2.2.0",
        "2026-09-01",
        [
            "Nowy układ kafelków Bento.",
            "Jeden arkusz stylów z tokenami jasnego i ciemnego motywu.",
        ],
    ),
]


class ChangelogDialog(AppDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("helpGuideDialog")
        self.setWindowTitle("Changelog — Inyfinn Photo Resizer")
        self.setMinimumSize(520, 480)
        self.resize(600, 620)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 12, 14, 12)

        intro = QLabel(
            f"Co nowego w kolejnych wydaniach. Teraz masz wersję {__version__}."
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

        for version, date, bullets in CHANGELOG:
            body_lay.addWidget(_version_block(version, date, bullets))

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


def _version_block(version: str, date: str, bullets: list[str]) -> QFrame:
    box = QFrame()
    box.setObjectName("helpGuideSection")
    outer = QVBoxLayout(box)
    outer.setContentsMargins(12, 10, 12, 10)
    outer.setSpacing(8)

    title = QLabel(f"v{version}  ·  {date}")
    title.setObjectName("changelogVersion")
    title.setWordWrap(True)
    outer.addWidget(title)

    for line in bullets:
        item = QLabel(f"•  {line}")
        item.setObjectName("helpGuideItem")
        item.setWordWrap(True)
        outer.addWidget(item)
    return box


def show_changelog(parent=None) -> None:
    ChangelogDialog(parent).exec()
