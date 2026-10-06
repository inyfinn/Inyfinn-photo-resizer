"""Dopasowanie okna do ekranu (reguła G7 specyfikacji Runda 3, 2.6.5).

Okno przy starcie i przy zmianie trybu nigdy nie przekracza obszaru dostępnego ekranu (bez paska zadań),
a cała treść jest widoczna bez ręcznego powiększania. Gdy treść się nie mieści, program zagęszcza
odstępy (maks. dwa poziomy), a jeśli to nie wystarcza, przewija prawy panel — nigdy nie ucina dołu.

Ten moduł to czysta logika (bez widżetów): ``fit_window_size`` dostaje funkcję mierzącą potrzebny rozmiar
dla danego poziomu zagęszczenia i zwraca rozmiar okna, poziom, położenie. Pomiar i zastosowanie robi
``MainWindow`` (cienka warstwa Qt). Wszystkie wartości w pikselach logicznych (jak ``QScreen``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QMargins, QPoint, QRect, QSize

# Ramka okna Windows 10/11 w pikselach logicznych (AdjustWindowRectEx, 100% DPI): pasek tytułu 31, boki i dół 8.
# Używana, dopóki system nie poda prawdziwej ramki (okno bez natywnego uchwytu, offscreen, WA_DontShowOnScreen).
FALLBACK_FRAME = QMargins(8, 31, 8, 8)
# Pasek tytułu to co najmniej tyle — niższa górna ramka znaczy „system jej nie zna” (np. 2 px offscreen).
MIN_REAL_TITLE_H = 20


@dataclass(frozen=True)
class Density:
    """Zestaw odstępów: tylko odstępy i wypełnienia, wysokości kontrolek (36–48 px) się nie zmieniają."""

    level: int
    card_gap: int  # między kartami (lewa↔prawa kolumna, karty w kolumnie, tryb prosty)
    tile_pad: int  # wypełnienie karty z lewej, prawej i dołu
    tile_pad_top: int  # wypełnienie karty od góry (nagłówek stoi wyżej)
    tile_header_gap: int  # nagłówek → treść oraz ikona → tytuł
    tile_inner_gap: int  # między wierszami wewnątrz karty
    view_margin_v: int  # górny i dolny margines widoku pod paskiem menu


# Poziom 0 = wygląd domyślny (design system: odstęp między kartami 16 px). Poziomy 1–2 tylko gdy ekran jest niski.
DENSITIES: tuple[Density, ...] = (
    Density(0, 16, 20, 16, 10, 10, 12),
    Density(1, 12, 14, 12, 8, 8, 8),
    Density(2, 8, 10, 10, 6, 6, 4),
)


@dataclass(frozen=True)
class FitResult:
    level: int  # indeks w DENSITIES
    client: QSize  # rozmiar obszaru klienta okna (to, co przyjmuje resize())
    outer: QSize  # rozmiar z ramką i paskiem tytułu
    pos: QPoint  # lewy górny róg ramki okna (to, co przyjmuje move())
    scroll: bool  # nawet najbardziej zwarty poziom się nie mieści → prawy panel przewija się w pionie
    min_client: QSize  # minimum okna, nigdy większe niż dostępny obszar


def frame_margins(widget) -> QMargins:
    """Ramka okna w pikselach logicznych: prawdziwa z systemu albo oszacowana."""
    fg, g = widget.frameGeometry(), widget.geometry()
    measured = QMargins(g.left() - fg.left(), g.top() - fg.top(), fg.right() - g.right(), fg.bottom() - g.bottom())
    if widget.isVisible() and measured.top() >= MIN_REAL_TITLE_H:
        return measured
    return QMargins(FALLBACK_FRAME)


def inside(available: QRect, size: QSize, pos: QPoint) -> QPoint:
    """Najbliższe pos, przy którym prostokąt ``size`` leży w całości w ``available``."""
    max_x = available.x() + available.width() - size.width()
    max_y = available.y() + available.height() - size.height()
    x = max(available.x(), min(pos.x(), max_x))
    y = max(available.y(), min(pos.y(), max_y))
    return QPoint(x, y)


def fit_window_size(
    measure: Callable[[int], QSize],
    available: QRect,
    frame: QMargins,
    *,
    levels: int = len(DENSITIES),
    saved: QSize | None = None,
    preferred_w: int,
    min_client: QSize,
    pos: QPoint | None = None,
) -> FitResult:
    """Wybiera poziom zagęszczenia i rozmiar okna.

    ``measure(level)`` zwraca potrzebny rozmiar obszaru klienta (szerokość = minimum układu,
    wysokość = cała treść bez przewijania) przy danym poziomie.
    ``saved``: rozmiar klienta wybrany wcześniej przez usera (albo bieżący). Wymiar respektujemy tylko wtedy,
    gdy mieści się w ekranie; wysokość nigdy nie spada poniżej potrzebnej, gdy ekran ma miejsce.
    ``pos``: bieżące położenie ramki (zostaje, przesunięte tylko tyle, by okno leżało na ekranie);
    ``None`` = wyśrodkuj w dostępnym obszarze.
    """
    max_w = max(1, available.width() - frame.left() - frame.right())
    max_h = max(1, available.height() - frame.top() - frame.bottom())

    level = 0
    need = measure(0)
    while need.height() > max_h and level < levels - 1:
        level += 1
        need = measure(level)
    scroll = need.height() > max_h

    pref_w = preferred_w
    if saved is not None and 0 < saved.width() <= max_w:
        pref_w = saved.width()
    width = min(max(pref_w, need.width()), max_w)

    if scroll:
        height = max_h
    else:
        height = need.height()
        if saved is not None and need.height() <= saved.height() <= max_h:
            height = saved.height()

    # Minimum okna: preferowane (np. 1180×700), nie mniejsze niż minimum układu (need.width), nigdy większe niż ekran.
    min_c = QSize(min(max(min_client.width(), need.width()), max_w), min(min_client.height(), max_h))
    width = max(width, min_c.width())
    height = max(height, min_c.height())

    client = QSize(width, height)
    outer = QSize(width + frame.left() + frame.right(), height + frame.top() + frame.bottom())
    if pos is None:
        pos = QPoint(
            available.x() + (available.width() - outer.width()) // 2,
            available.y() + (available.height() - outer.height()) // 2,
        )
    return FitResult(level, client, outer, inside(available, outer, pos), scroll, min_c)
