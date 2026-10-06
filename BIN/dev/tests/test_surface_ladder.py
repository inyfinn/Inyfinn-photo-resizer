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
    """Ciemne: głębiej = jaśniej. Jasne (DS 2.0): L2 (karta w panelu) jaśniejszy od panelu L1, od L2 w głąb ciemniej."""
    lad = palettes.LADDER[_key(theme)]
    lums = [_lum(lad[f"surface_{n}"]) for n in range(5)]
    steps = [b - a for a, b in zip(lums, lums[1:])]
    if themes.is_dark_theme(theme):
        assert all(s > 0 for s in steps), lums
    else:
        assert lums[0] >= lums[2] > lums[3] > lums[4], lums  # biel ≥ karta > kafel > kafel w kaflu
        assert lums[0] > lums[1], lums  # panel L1 ciemniejszy od okna


@pytest.mark.parametrize("theme", ALL)
def test_white_only_in_light_themes(theme):
    """Jasne style: okno L0 jest białe (bieli najwięcej), panel L1 nie; ciemne bez bieli."""
    lad = palettes.LADDER[_key(theme)]
    levels = [lad[f"surface_{n}"].upper() for n in range(5)]
    if themes.is_dark_theme(theme):
        assert "#FFFFFF" not in levels
    else:
        assert levels[0] == "#FFFFFF"
        assert levels[1] != "#FFFFFF"


@pytest.mark.parametrize("theme", ALL)
def test_section_tile_has_no_border(theme):
    """DS 2.0 (S2): sekcja = panel bez obrysu i bez cienia; linie 1 px roli border tylko jawnie (@LINE@)."""
    t = themes._THEME_TOKENS[theme]
    assert t["@CARD_BORDER@"] == "none"
    assert t["@LINE@"] == f"1px solid {t['@SEP@']}"


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
def test_field_is_a_card_inside_the_panel(theme):
    """Pole/lista w panelu = L2: w jasnych jaśniejsze od panelu (biała karta), w ciemnych odwrotnie."""
    t = themes._THEME_TOKENS[theme]
    if themes.is_dark_theme(theme):
        assert _lum(t["@BG_INPUT@"]) > _lum(t["@BG_PANEL@"])
    else:
        assert _lum(t["@BG_INPUT@"]) > _lum(t["@BG_PANEL@"])
        assert t["@BG_INPUT@"] == t["@BG_WINDOW@"]  # biała karta w panelu = to samo co tło okna


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
def test_tags_are_readable(theme):
    """Tekst każdego z 8 tagów ≥ 4,5:1 na jego tle (DS 2.0.5: tagi to wypełnienie, bez obrysu)."""
    t = themes._THEME_TOKENS[theme]
    for n in range(1, themes.TAG_COUNT + 1):
        bg, fg = t[f"@TAG{n}_BG@"], t[f"@TAG{n}_FG@"]
        assert _contrast(fg, bg) >= 4.5, (n, fg, bg)
        assert _oklch(bg)[1] < 0.2  # wypełnienie pastelowe, nie jaskrawe


@pytest.mark.parametrize("theme", (ZJ, KJ))
def test_eight_distinct_tag_hues_in_light_themes(theme):
    """Jasne motywy: 8 tagów w 8 wyraźnie różnych barwach; PNG, JPG i AVIF to trzy różne barwy."""
    t = themes._THEME_TOKENS[theme]
    hues = [_oklch(t[f"@TAG{n}_BG@"])[2] for n in range(1, themes.TAG_COUNT + 1)]
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            d = min(abs(hues[i] - hues[j]), 360 - abs(hues[i] - hues[j]))
            assert d >= 20, (i + 1, j + 1, hues)
    tag = {f: themes.format_tag(f) for f in ("png", "jpg", "avif")}
    assert len(set(tag.values())) == 3
    for a, b in (("png", "jpg"), ("png", "avif"), ("jpg", "avif")):
        ha, hb = hues[tag[a] - 1], hues[tag[b] - 1]
        assert min(abs(ha - hb), 360 - abs(ha - hb)) >= 60, (a, b, ha, hb)


def test_format_tag_mapping():
    assert themes.format_tag("png") == 1
    assert themes.format_tag("JPEG") == themes.format_tag(".jpg") == 4
    assert themes.format_tag("avif") == 8
    assert themes.format_tag("webp") == 3
    assert themes.format_tag("gif") == 5
    assert themes.format_tag("tiff") == themes.format_tag("tif") == 6
    assert themes.format_tag("heic") == themes.format_tag("jp2") == 7
    mapped = {themes.format_tag(f) for f in ("png", "jpg", "avif", "webp", "gif", "tiff", "jp2")}
    assert len(mapped) == 7  # każdy format ma własną barwę
    assert themes.format_tag("xyz") == themes.format_tag(None) == themes.DEFAULT_TAG


@pytest.mark.parametrize("theme", ALL)
def test_chips_and_ext_badges_use_tag_tokens(app, theme):
    qss = themes.render_qss(theme)
    t = themes._THEME_TOKENS[theme]
    assert re.search(r'QPushButton#formatChip\[tag="2"\][^}]*' + re.escape(t["@TAG2_BG@"]), qss)
    assert re.search(r'QLabel#fileProgressExt\[tag="3"\][^}]*' + re.escape(t["@TAG3_BG@"]), qss)
