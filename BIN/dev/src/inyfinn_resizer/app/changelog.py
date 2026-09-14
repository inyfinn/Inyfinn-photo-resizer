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
