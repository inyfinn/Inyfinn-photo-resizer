"""Drabina powierzchni L0…L4 i tagi z design systemu Dobra Kaloria (1.4.0 w 2.6.3, 1.5.0 w 2.6.4).

L0 tło okna → L1 karta → L2 rubryka (pola, listy, tabela, podgląd) → L3 element w rubryce → L4 nakładka.
Jasny: głębiej = ciemniej, ciemny: głębiej = jaśniej. Rubryki minimalnie ciemniejsze niż w 2.6.2.
Tagi (chipy formatu, znaczniki w oknie konwersji) = odcień stylu, bez obcych stałych barw.
"""

from __future__ import annotations

import math
import re

import pytest
from PySide6.QtGui import QColor

from inyfinn_resizer.app import themes
from inyfinn_resizer.app.themes import palettes

ZJ = "dobra-kaloria-zielen-jasny"
ZC = "dobra-kaloria-zielen-ciemny"
KJ = "dobra-kaloria-krem-jasny"
KC = "dobra-kaloria-krem-ciemny"
ALL = (ZJ, ZC, KJ, KC)

# Tło pól (@BG_INPUT@) w 2.6.2 — punkt odniesienia dla „minimalnie ciemniej”.
FIELD_262 = {ZJ: "#FFFFFF", ZC: "#1D3526", KJ: "#FBF3E0", KC: "#302A21"}


def _lum(hex_color: str) -> float:
    c = QColor(hex_color)

    def ch(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.fixture()
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _key(theme: str) -> str:
    return "-".join(themes.split_theme(theme))


@pytest.mark.parametrize("theme", ALL)
def test_ladder_has_one_direction(theme):
    lad = palettes.LADDER[_key(theme)]
    lums = [_lum(lad[f"surface_{n}"]) for n in range(5)]
    steps = [b - a for a, b in zip(lums, lums[1:])]
    if themes.is_dark_theme(theme):
        assert all(s > 0 for s in steps), lums  # ciemny: głębiej = jaśniej
    else:
        assert all(s < 0 for s in steps), lums  # jasny: głębiej = ciemniej


@pytest.mark.parametrize("theme", ALL)
def test_white_only_as_light_window(theme):
    """DS 1.5.0: jasne style = biała kartka programu (L0), karty i głębiej kremowe; ciemne bez bieli."""
    lad = palettes.LADDER[_key(theme)]
    levels = [lad[f"surface_{n}"].upper() for n in range(5)]
    if themes.is_dark_theme(theme):
        assert "#FFFFFF" not in levels
    else:
        assert levels[0] == "#FFFFFF"
        assert "#FFFFFF" not in levels[1:]
        assert levels[1] == "#FDF8ED"  # kremowa karta programu (.hints / .found)


@pytest.mark.parametrize("theme", ALL)
def test_card_border_is_subtle(theme):
    """2.6.4: karta bez ciężkiego obrysu — 1 px w roli border (jak w programie), nie border-strong."""
    t = themes._THEME_TOKENS[theme]
    assert t["@CARD_BORDER@"] == f"1px solid {t['@SEP@']}"


@pytest.mark.parametrize("theme", ALL)
def test_containers_use_ladder_levels(theme):
    t = themes._THEME_TOKENS[theme]
    lad = palettes.LADDER[_key(theme)]
    assert t["@BG_WINDOW@"] == lad["surface_0"]
    assert t["@BG_PANEL@"] == lad["surface_1"]
    assert t["@BG_INPUT@"] == t["@BG_PANEL_ALT@"] == lad["surface_2"]
    assert t["@BG_L3@"] == lad["surface_3"]
    assert t["@BG_L4@"] == lad["surface_4"]


@pytest.mark.parametrize("theme", ALL)
def test_fields_minimally_darker_than_262(theme):
    now = themes._THEME_TOKENS[theme]["@BG_INPUT@"]
    before = FIELD_262[theme]
    assert _lum(now) < _lum(before), (now, before)
    # „minimalnie”: nie więcej niż ~15% luminancji względnej różnicy
    assert _lum(before) - _lum(now) < 0.15 * max(_lum(before), 0.02) + 0.02, (now, before)


@pytest.mark.parametrize("theme", ALL)
def test_text_readable_on_every_level(theme):
    t = themes._THEME_TOKENS[theme]
    for level in ("@BG_WINDOW@", "@BG_PANEL@", "@BG_INPUT@", "@BG_L3@", "@BG_L4@"):
        assert _contrast(t["@FG_TEXT@"], t[level]) >= 4.5, level
        assert _contrast(t["@FG_MUTED@"], t[level]) >= 4.5, level


def _oklch(hex_color: str) -> tuple[float, float, float]:
    """sRGB → OKLCH (L 0..1, C, h w stopniach) — ta sama przestrzeń co generator design systemu."""
    c = QColor(hex_color)

    def lin(v: float) -> float:
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = lin(c.redF()), lin(c.greenF()), lin(c.blueF())
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


@pytest.mark.parametrize("theme", ALL)
def test_tags_are_tints_of_the_style(theme):
    t = themes._THEME_TOKENS[theme]
    hues = []
    for n in range(1, themes.TAG_COUNT + 1):
        bg, fg = t[f"@TAG{n}_BG@"], t[f"@TAG{n}_FG@"]
        assert _contrast(fg, bg) >= 4.5, (n, fg, bg)
        _L, chroma, hue = _oklch(bg)
        assert chroma < 0.08, (n, bg, chroma)  # delikatny odcień, nie jaskrawa stała barwa
        hues.append(hue)
    # Przesunięcia barwy tagów to małe kroki (±12°, ±24°…, najwyżej 48°) wokół barwy stylu.
    ref = hues[0]
    for h in hues:
        d = min(abs(h - ref), 360 - abs(h - ref))
        assert d <= 55, (hues, theme)


def test_format_tag_mapping():
    assert themes.format_tag("png") == 1
    assert themes.format_tag("JPEG") == themes.format_tag(".jpg") == 2
    assert themes.format_tag("avif") == 3
    assert themes.format_tag("webp") == 4
    assert themes.format_tag("xyz") == themes.TAG_COUNT
    assert themes.format_tag(None) == themes.TAG_COUNT


@pytest.mark.parametrize("theme", ALL)
def test_chips_and_ext_badges_use_tag_tokens(app, theme):
    qss = themes.render_qss(theme)
    t = themes._THEME_TOKENS[theme]
    assert re.search(r'QPushButton#formatChip\[tag="2"\][^}]*' + re.escape(t["@TAG2_BG@"]), qss)
    assert re.search(r'QLabel#fileProgressExt\[tag="3"\][^}]*' + re.escape(t["@TAG3_BG@"]), qss)
