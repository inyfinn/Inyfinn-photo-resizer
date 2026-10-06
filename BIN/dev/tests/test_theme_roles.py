"""Warstwa motywu = role z palettes.py (generowane z design systemu). Testy nie znają wartości kolorów:
sprawdzają strukturę (komplet znaczników, brak dryfu względem ról, kształt pola wyboru, stałe wysokości)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QPushButton

from inyfinn_resizer.app import themes
from inyfinn_resizer.app.themes import palettes
from inyfinn_resizer.app.themes.icons import generate_check_icons

ZJ = "dobra-kaloria-zielen-jasny"
ZC = "dobra-kaloria-zielen-ciemny"
KJ = "dobra-kaloria-krem-jasny"
KC = "dobra-kaloria-krem-ciemny"
ALL = (ZJ, ZC, KJ, KC)
THEMES_DIR = Path(themes.__file__).parent
ICONS_DIR = THEMES_DIR / "icons"


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def _key(theme: str) -> str:
    return "-".join(themes.split_theme(theme))


def _lum(hex_color: str) -> float:
    c = QColor(hex_color)

    def ch(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _hex(pixel) -> str:
    return "#%02X%02X%02X" % tuple(pixel[:3])


def test_palettes_declare_a_design_system_version():
    head = (THEMES_DIR / "palettes.py").read_text(encoding="utf-8")[:300]
    assert re.search(r"Dobra Kaloria \d+\.\d+\.\d+", head)


def test_every_theme_defines_every_marker_and_roles_are_complete():
    keys = [set(t) for t in themes._THEME_TOKENS.values()]
    assert all(k == keys[0] for k in keys)
    roles = [set(r) for r in palettes.ROLES.values()]
    assert all(r == roles[0] for r in roles)
    for needed in ("color_accent", "color_icon", "color_check_bg", "color_slider_fill", "color_btn2_border",
                   "color_switch_on", "color_step_active_bg"):
        assert needed in roles[0], needed


@pytest.mark.parametrize("theme", ALL)
def test_rendered_qss_has_no_unresolved_marker(app, theme):
    qss = themes.render_qss(theme)
    assert re.findall(r"@[A-Z_0-9]+@", qss) == []
    assert "QLabel#workflowHint" not in qss


def test_qss_source_has_no_color_literals():
    """Kolory tylko przez znaczniki (wartości przychodzą z palettes.py)."""
    qss = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    assert re.findall(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", qss) == []


@pytest.mark.parametrize("theme", ALL)
def test_markers_equal_palette_roles(theme):
    """Znaczniki kontrolek = role design systemu, jakiekolwiek są wartości (brak dryfu)."""
    t = themes._THEME_TOKENS[theme]
    r = palettes.ROLES[_key(theme)]
    expected = {
        "@BTN2_BG@": "color_btn2_bg", "@BTN2_TEXT@": "color_btn2_text", "@BTN2_BORDER@": "color_btn2_border",
        "@BTN2_HOVER@": "color_btn2_hover_bg", "@SLIDER_TRACK@": "color_slider_track",
        "@SLIDER_FILL@": "color_slider_fill", "@SLIDER_THUMB@": "color_slider_thumb",
        "@SLIDER_THUMB_BORDER@": "color_slider_thumb_border", "@SWITCH_OFF@": "color_switch_off",
        "@SWITCH_OFF_BORDER@": "color_switch_off_border", "@SWITCH_ON@": "color_switch_on",
        "@SWITCH_KNOB@": "color_switch_knob", "@SELECT_BG@": "color_step_active_bg",
        "@SELECT_FG@": "color_step_active_text", "@ICON@": "color_icon", "@ICON_BG@": "color_icon_bg",
        "@ROW_SELECTED_FG@": "color_text", "@POPUP_SELECTED_BG@": "color_brand_soft",
        "@BRAND_SOFT_STRONG@": "color_brand_soft_strong",
        "@FG_ACCENT@": "color_accent", "@ACCENT_HOVER@": "color_accent_hover", "@ON_ACCENT@": "color_on_accent",
        "@ACCENT@": "color_slider_fill", "@FG_LABEL@": "color_label", "@BORDER_FOCUS@": "color_focus",
        "@UPDATE_TOAST_BORDER@": "color_btn2_border", "@CTA_BG@": "color_cta", "@CTA_TEXT@": "color_on_cta",
        "@FG_TEXT@": "color_text", "@FG_MUTED@": "color_text_muted", "@FG_TITLE@": "color_heading",
        "@FG_HEADING_ACCENT@": "color_heading_accent", "@BG_OVERLAY@": "color_overlay",
        "@BG_STRIP@": "color_strip", "@BG_ZEBRA@": "color_zebra", "@PROGRESS@": "color_progress",
        "@PRIMARY_BG@": "color_brand", "@PRIMARY_HOVER@": "color_brand_hover", "@PRIMARY_TEXT@": "color_on_brand",
        "@BRAND_SOFT@": "color_brand_soft",
        "@UPDATE_TOAST_BG@": "color_overlay", "@UPDATE_TOAST_BORDER@": "color_border",
    }
    for marker, role in expected.items():
        assert t[marker] == r[role], (theme, marker, role)
    assert t["@DROP_BORDER@"] == f"1px dashed {r['color_field_border']}"
    lad = palettes.LADDER[_key(theme)]
    assert t["@BG_WINDOW@"] == lad["surface_0"] and t["@BG_PANEL@"] == lad["surface_1"]
    assert t["@BG_INPUT@"] == t["@BG_PANEL_ALT@"] == lad["surface_2"]
    assert t["@BG_L3@"] == lad["surface_3"] and t["@BG_L4@"] == lad["surface_4"]
    assert t["@BTN2_PRESSED@"] == r["color_brand_soft_strong"]


def test_shape_markers_equal_palette_shape():
    """Promienie, obrysy i rozmiary czcionek przycisków pochodzą z palettes.SHAPE (DS), nie z literałów."""
    s = palettes.SHAPE
    sh = themes._SHAPE
    assert sh["@RADIUS_CARD@"] == s["radius_card"]
    assert sh["@RADIUS_FIELD@"] == s["radius_field"]
    assert sh["@RADIUS_BTN@"] == s["radius_btn"]
    assert sh["@RADIUS_DROP@"] == s["radius_drop"]
    assert sh["@FOCUS_W@"] == s["focus_border"] and sh["@FIELD_BORDER_W@"] == s["field_border"]
    assert sh["@FS_BTN@"] == s["fs_btn"] and sh["@FS_BTN_PRIMARY@"] == s["fs_btn_primary"]
    # S15 (DS 2.0.3): fokus pola = cienki obrys tej samej grubości co obrys pola — bez kompensowania dopełnienia
    assert themes.FOCUS_BORDER_PX == themes.FIELD_BORDER_PX == 1
    src = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", src)
    focus_rules = [b for s, b in rules if ":focus" in s and re.search(r"QLineEdit|QSpinBox|QComboBox", s)]
    assert focus_rules
    assert all("padding" not in b for b in focus_rules)  # geometria nie przesuwa się przy fokusie
    assert any("@FOCUS_W@" in b for b in focus_rules)  # grubość z markera (SHAPE focus_border), nie literał
    assert not re.search(r":focus[^{]*\{[^}]*border:\s*\d+px", src)  # żadnego literału grubości w regułach fokusu


@pytest.mark.parametrize("theme", ALL)
def test_s14_s15_no_dark_fills_and_no_ecru_levels_in_qss(theme):
    """Brak ciemnych wypełnień z ról tekstu jako TŁA (S15) i brak L3/L4 w arkuszu (S14: beż tylko na prawdziwym
    3. poziomie, a aplikacja go nie używa)."""
    src = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    assert not re.search(r"background(-color)?:\s*@(FG_TEXT|FG_TITLE|BTN2_TEXT|CTA_TEXT|FG_MUTED)@", src)
    assert "@BG_L3@" not in src and "@BG_L4@" not in src
    t = themes._THEME_TOKENS[theme]
    qss = themes.render_qss(theme)
    assert "border_subtle" not in qss  # ramki subtelne (beżowe) nie są używane jako obrys
    assert t["@BTN2_PRESSED@"] == palettes.ROLES[_key(theme)]["color_brand_soft_strong"]


def test_primary_is_green_brand_and_only_convert_is_cta():
    """S6: przyciski główne = marker PRIMARY (brand), żółty CTA wyłącznie footerConvert."""
    qss = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", qss)
    for name in ("primaryBtn", "footerPrimary", "saveChoicePrimary", "updateDialogAction"):
        assert any(
            f"QPushButton#{name}" in sel.replace(":hover", "x") and "@PRIMARY_BG@" in body for sel, body in rules
        ), name
    cta_rules = [m.group(0) for m in re.finditer(r"[^}]*\{[^}]*@CTA_BG@[^}]*\}", qss)]
    assert len(cta_rules) == 1 and "footerConvert" in cta_rules[0], cta_rules
    assert "@UPDATE_TOAST_INSTALL_BG@" in qss  # zainstaluj w toaście: zielony główny (marker mapowany na brand)


def test_buttons_are_uppercase_except_links_and_chips(app):
    from PySide6.QtGui import QFont

    themes.apply_theme(app, ZJ)
    upper = QPushButton("Dodaj")
    upper.ensurePolished()
    assert upper.font().capitalization() == QFont.Capitalization.AllUppercase
    assert upper.text() == "Dodaj"  # tekst w kodzie bez zmian
    for name in ("btnLink", "formatChip", "footerClose"):
        b = QPushButton("Zamknij")
        b.setObjectName(name)
        b.ensurePolished()
        assert b.font().capitalization() != QFont.Capitalization.AllUppercase, name


@pytest.mark.parametrize("theme", ALL)
def test_check_images_exist_for_every_state(theme):
    for name in themes.check_image_names(_key(theme)):
        path = ICONS_DIR / name
        assert path.is_file(), name
        assert Image.open(path).size == (80, 80)


@pytest.mark.parametrize("theme", ALL)
@pytest.mark.parametrize("kind", ("cb", "rb"))
def test_checked_image_is_not_a_filled_box(theme, kind):
    """G1: zaznaczone pole ma wnętrze = rola check_bg (znak zajmuje mały ułamek), nie wypełniony kwadrat."""
    key = _key(theme)
    r = palettes.ROLES[key]
    on = Image.open(ICONS_DIR / f"{kind}-{key}-on.png").convert("RGBA")
    inside = [on.getpixel((x, y)) for x in range(16, 64) for y in range(16, 64)]
    interior = sum(1 for p in inside if _hex(p) == r["color_check_bg"].upper())
    mark = sum(1 for p in inside if _hex(p) == r["color_check_mark"].upper())
    # ptaszek ~15 % środka, kropka radio ~40 %; wypełniony kwadrat miałby znak ≈ 100 %
    assert interior > mark, (interior, mark, len(inside))
    assert mark / len(inside) < 0.5
    off = Image.open(ICONS_DIR / f"{kind}-{key}-off.png").convert("RGBA")
    assert _hex(off.getpixel((40, 40))) == r["color_check_bg"].upper()
    assert _hex(off.getpixel((40, 2))) == r["color_check_border"].upper()  # obrys ~1,5 px
    assert off.getpixel((0, 0))[3] == 0  # narożnik poza zaokrągleniem przezroczysty


@pytest.mark.parametrize("theme", ALL)
def test_checkbox_qss_uses_images_not_filled_background(app, theme):
    key = _key(theme)
    qss = themes.render_qss(theme)
    rule = re.search(r"QCheckBox::indicator:checked \{([^}]*)\}", qss).group(1)
    assert f"cb-{key}-on.png" in rule and "background" not in rule
    base = re.search(r"QCheckBox::indicator, QRadioButton::indicator \{([^}]*)\}", qss).group(1)
    assert "border: none" in base
    assert f"width: {themes.CHECK_SIZE_PX}px" in base and f"height: {themes.CHECK_SIZE_PX}px" in base
    assert re.search(r"QRadioButton::indicator:checked \{ image: url\([^)]*rb-" + re.escape(key) + r"-on\.png", qss)
    assert re.search(r"QMenu::indicator:non-exclusive:checked \{ image: url\([^)]*cb-" + re.escape(key), qss)


def test_generator_size_matches_marker():
    assert generate_check_icons.LOGICAL == themes.CHECK_SIZE_PX
    assert generate_check_icons.FINAL == 4 * generate_check_icons.LOGICAL


def test_secondary_button_rule_uses_border_width_marker():
    src = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    rule = re.search(r"\nQPushButton \{([^}]*)\}", src).group(1)
    assert "@BTN2_BORDER_W@ solid @BTN2_BORDER@" in rule
    assert "@BTN2_PAD_V@" in rule
    assert themes.BTN2_BORDER_PX + int(themes._SHAPE["@BTN2_PAD_V@"][:-2]) == themes.BTN2_LEGACY_RIM_PX


@pytest.mark.parametrize("theme", ALL)
def test_button_total_heights_unchanged(app, theme):
    """Obrys cieńszy z dopełnieniem pionowym: wysokości całkowite jak w 2.6.4."""
    themes.apply_theme(app, theme)
    for name, text, want in ((None, "Dodaj pliki", 36), ("footerConvert", "Konwertuj", 48), ("primaryBtn", "OK", 40)):
        btn = QPushButton(text)
        if name:
            btn.setObjectName(name)
        btn.ensurePolished()
        assert btn.sizeHint().height() == want, (theme, name)


@pytest.mark.parametrize("theme", ALL)
def test_cta_uses_cta_roles(theme):
    r = palettes.ROLES[_key(theme)]
    qss = themes.render_qss(theme)
    assert re.search(r"QPushButton#footerConvert \{[^}]*background-color: " + re.escape(r["color_cta"]), qss)


@pytest.mark.parametrize("theme", ALL)
def test_text_contrast_of_role_pairs(theme):
    t = themes._THEME_TOKENS[theme]
    assert _contrast(t["@BTN2_TEXT@"], t["@BTN2_BG@"]) >= 4.5
    assert _contrast(t["@BTN2_TEXT@"], t["@BTN2_HOVER@"]) >= 4.5
    assert _contrast(t["@SELECT_FG@"], t["@SELECT_BG@"]) >= 4.5
    assert _contrast(t["@FG_ACCENT@"], t["@BG_PANEL@"]) >= 4.5


@pytest.mark.parametrize("theme", ALL)
def test_selected_rows_are_distinct_from_list_and_hover(theme):
    """Zaznaczony wiersz ≠ tło listy ≠ najechanie; tekst text ≥ 4,5:1 na zaznaczeniu.

    Jasne: brand_soft / surface_hover z ról. Ciemne (znana luka DS, tryb w themes._theme_tokens): L4 / L3 drabiny,
    kontrast zaznaczenia do tła listy ≥ 1,15.
    """
    t = themes._THEME_TOKENS[theme]
    key = _key(theme)
    r, lad = palettes.ROLES[key], palettes.LADDER[key]
    list_bg = t["@BG_PANEL_ALT@"]
    assert _contrast(t["@ROW_SELECTED_FG@"], t["@ROW_SELECTED_BG@"]) >= 4.5
    assert len({t["@ROW_SELECTED_BG@"], list_bg, t["@ROW_HOVER@"], t["@BG_ZEBRA@"]}) == 4  # zaznaczony ≠ lista ≠ najechanie ≠ pas
    assert t["@ROW_SELECTED_BG@"] != t["@SELECT_BG@"]  # nie pełna zieleń kroku (SELECT_* tylko dla przełącznika-segmentu)
    if themes.is_dark_theme(theme):
        assert t["@ROW_SELECTED_BG@"] == lad["surface_4"] and t["@ROW_HOVER@"] == lad["surface_3"]
        assert _contrast(t["@ROW_SELECTED_BG@"], list_bg) >= 1.15
    else:
        assert t["@ROW_SELECTED_BG@"] == r["color_brand_soft_strong"] and t["@ROW_HOVER@"] == r["color_brand_soft"]
    # nakładki: zaznaczenie w menu i popupie odróżnia się od tła nakładki
    assert t["@POPUP_SELECTED_BG@"] != t["@BG_OVERLAY@"]


@pytest.mark.parametrize("theme", ALL)
def test_s13_no_outline_on_tags_chips_panels_icon_buttons(app, theme):
    """S13: obrys tylko na polach, polu wyboru, jednym przycisku drugorzędnym w grupie, karcie na białym oknie i
    fokusie. Tagi, chipy, panele, przyciski ikonowe i ciche: bez obrysu (fokus wyłączony z kontroli)."""
    qss = themes.render_qss(theme)
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", qss)
    names = ("#formatChip", "#fileProgressExt", "#iconBtn", "#toolBtn", '[quiet="true"]', "#bentoTile",
             "#dialogPanel", "#btnUpdatePath", "#overlayAbortBtn")
    seen = set()
    for sel, body in rules:
        for name in names:
            if name not in sel or ":focus" in sel or "variant=\"drop\"" in sel:  # drop = pole z przerywaną ramką
                continue
            seen.add(name)
            for m in re.finditer(r"(?<![-\w])border\s*:\s*([^;]+);", body):
                value = m.group(1).strip()
                assert value == "none" or value.startswith("0"), (theme, sel.strip(), value)
    assert seen == set(names), set(names) - seen


@pytest.mark.parametrize("theme", ALL)
def test_quiet_buttons_fill_depends_on_ancestor(app, theme):
    t = themes._THEME_TOKENS[theme]
    qss = themes.render_qss(theme)
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", qss)
    base = [b for s, b in rules if s.strip().endswith('QPushButton[quiet="true"]') and "QFrame" not in s.split("*/")[-1]
            and "QWidget" not in s.split("*/")[-1] and "QTab" not in s.split("*/")[-1]]
    assert any(f"background-color: {t['@ICON_BG@']}" in b for b in base)
    on_panel = [b for s, b in rules if "QFrame#bentoTile QPushButton#toolBtn" in s and ":hover" not in s
                and ":focus" not in s and ":pressed" not in s and ":disabled" not in s]
    assert any(f"background-color: {t['@BG_INPUT@']}" in b for b in on_panel)
    hover = [b for s, b in rules if "QFrame#bentoTile QPushButton#toolBtn:hover" in s]
    assert any(f"background-color: {t['@BRAND_SOFT@']}" in b for b in hover)


def test_item_views_use_row_markers_not_step_active():
    src = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", src)
    for sel_name in ("simpleFileList::item:selected", "inputList::item:selected", "resultsTable::item:selected",
                     "QAbstractItemView {", "QComboBox QAbstractItemView::item:selected"):
        hits = [(s, b) for s, b in rules if sel_name.rstrip(" {") in s]
        assert hits, sel_name
        for _s, b in hits:
            assert "@SELECT_BG@" not in b and "@SELECT_FG@" not in b, sel_name
    toggles = [b for s, b in rules if "cropAnchorBtn:checked" in s]
    assert toggles and "@SELECT_BG@" in toggles[0]


def test_overlay_with_three_files_shows_all_cards_without_scrollbar(app):
    """Regresja: układ okna aktywował ukryty układ nakładki, QScrollArea zapamiętał pustą podpowiedź (0, 0) i
    lista kurczyła się do 54 px z suwakiem. 3 pliki w oknie 1280×920 muszą być widoczne w całości."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QScrollArea

    from inyfinn_resizer.app.main_window import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH, MainWindow

    themes.apply_theme(app, ZJ)
    w = MainWindow()
    try:
        w.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        w.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        w.show()
        app.processEvents()
        ov = w._conversion_overlay
        ov.start_batch([("A.png", "png"), ("B.jpg", "jpg"), ("C.jpg", "jpg")])
        app.processEvents()
        scroll = ov.findChild(QScrollArea)
        panel = ov._panel
        assert not scroll.verticalScrollBar().isVisible()
        assert scroll.viewport().height() >= scroll.widget().sizeHint().height()
        for card in ov._cards:
            top_left = card.mapTo(panel, card.rect().topLeft())
            bottom = card.mapTo(panel, card.rect().bottomLeft()).y()
            assert panel.rect().contains(top_left) and bottom <= panel.height()
            # karta w całości w widoku listy (nie ucięta)
            vp = card.mapTo(scroll.viewport(), card.rect().bottomLeft()).y()
            assert vp <= scroll.viewport().height(), (vp, scroll.viewport().height())
    finally:
        w.close()


@pytest.mark.parametrize("theme", ALL)
def test_message_box_warning_icon_is_yellow_square_with_dark_glyph(app, theme):
    """DS 2.0.4: ostrzeżenie = żółty kwadrat (cta) z ciemnym znakiem, nie systemowy trójkąt / brązowy tekst."""
    from inyfinn_resizer.app.widgets.section_icons import message_box_pixmap

    themes.apply_theme(app, theme)
    t = themes._THEME_TOKENS[theme]
    img = message_box_pixmap("warning").toImage()
    assert not img.isNull() and img.width() == 32
    fill = img.pixelColor(4, 16)  # lewa krawędź kwadratu, poza znakiem
    assert fill.name().upper() == t["@CTA_BG@"].upper()
    dark = [img.pixelColor(x, y) for x in range(10, 22) for y in range(6, 26)]
    assert any(c.name().upper() == t["@CTA_TEXT@"].upper() for c in dark)  # ciemny znak „!”
    for kind in ("critical", "question", "information"):
        assert not message_box_pixmap(kind).isNull()


@pytest.mark.parametrize("theme", ALL)
def test_bento_tile_variants(app, theme):
    """Wzorzec: wariant panel (szary L1), plain (bez tła i obrysu — treść na białym), drop (L1 + przerywana ramka)."""
    t = themes._THEME_TOKENS[theme]
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", themes.render_qss(theme))

    def body(selector_part: str) -> str:
        found = [b for s, b in rules if s.strip().endswith(selector_part)]
        assert found, selector_part
        return found[0]

    panel = body('QFrame#bentoTile[variant="panel"]')
    assert t["@BG_PANEL@"] in panel and "border-radius" in panel
    plain = body('QFrame#bentoTile[variant="plain"]')
    assert "background-color: transparent" in plain and "border: none" in plain and "border-radius: 0" in plain
    drop = body('QFrame#bentoTile[variant="drop"]')
    assert t["@BG_PANEL@"] in drop and t["@DROP_BORDER@"] in drop and "dashed" in t["@DROP_BORDER@"]
    # kafelek bez właściwości = panel
    assert any(s.strip() == "QFrame#bentoTile," or s.strip().startswith("QFrame#bentoTile,") for s, _ in rules) or any(
        "QFrame#bentoTile," in s for s, _ in rules
    )
    sep = body("QFrame#groupSep")
    assert t["@SEP@"] in sep and "min-height: 1px" in sep and "max-height: 1px" in sep


@pytest.mark.parametrize("theme", ALL)
def test_menu_strip_is_the_window_surface_with_a_line(app, theme):
    t = themes._THEME_TOKENS[theme]
    lad = palettes.LADDER[_key(theme)]
    assert t["@MENU_STRIP_BG@"] == lad["surface_0"] == t["@BG_WINDOW@"]
    assert t["@MENU_STRIP_BORDER@"].startswith("1px solid")


def test_slider_matches_the_reference_sizes(app):
    """Tor 8 px, uchwyt 24 px łącznie z obrysem 2 px, wycentrowany na torze."""
    qss = themes.render_qss(ZJ)
    groove = re.search(r"QSlider::groove:horizontal \{([^}]*)\}", qss).group(1)
    handle = re.search(r"QSlider::handle:horizontal \{([^}]*)\}", qss).group(1)
    assert "height: 8px" in groove
    inner = int(re.search(r"width: (\d+)px", handle).group(1))
    border = int(re.search(r"border: (\d+)px solid", handle).group(1))
    margin = int(re.search(r"margin: (-?\d+)px", handle).group(1))
    assert inner + 2 * border == 24 and border == 2
    assert 2 * (-margin) + 8 == 24  # uchwyt wystaje równo nad i pod torem
    assert themes.SLIDER_THUMB_PX == 24 and themes.SLIDER_TRACK_PX == 8


def test_file_icons_render_crisp_at_any_logical_size(app):
    from inyfinn_resizer.app.widgets import tool_icons

    themes.apply_theme(app, ZJ)
    want = QColor(themes.theme_token("@ICON@"))
    for factory in (tool_icons.icon_image_file, tool_icons.icon_video_file):
        big = factory(20).pixmap(20, 20)
        assert not big.isNull()
        assert big.deviceIndependentSize().toSize().width() == 20  # rozmiar logiczny 20 px
        assert QSize(40, 40) in factory(20).availableSizes()  # bufor 2× → ostre na HiDPI i przy skali 125 %
        img = big.toImage()
        ink = [img.pixelColor(x, y) for x in range(img.width()) for y in range(img.height()) if img.pixelColor(x, y).alpha() > 240]
        assert ink and all(abs(c.red() - want.red()) < 12 and abs(c.green() - want.green()) < 12 for c in ink[:50])


def test_splitter_handle_is_invisible_by_default():
    qss = (THEMES_DIR / "app.qss").read_text(encoding="utf-8")
    rule = re.search(r"QSplitter::handle \{([^}]*)\}", qss).group(1)
    assert "transparent" in rule and "width" not in rule


def test_update_toast_title_is_display_font():
    from inyfinn_resizer.app.themes import typography

    assert "updateToastTitle" in typography.DISPLAY_OBJECTS
