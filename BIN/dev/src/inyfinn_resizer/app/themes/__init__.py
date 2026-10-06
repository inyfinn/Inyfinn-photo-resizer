"""Theme loader — wspólna struktura + zamiana kolorów.

Od 2.6.1 wygląd = design system Dobra Kaloria (ten sam co program „Stwórz prezentację”).
Dwa niezależne wybory:
- **styl kolorów** (menu Narzędzia → Styl kolorów): „Dobra Kaloria 1 · zieleń” albo „Dobra Kaloria 2 · krem”,
- **tryb** (suwak słońce/księżyc): jasny albo ciemny.
Razem cztery motywy o id ``dobra-kaloria-<styl>-<tryb>`` (jak ``themes-list`` w tokens.json 1.3.0).
Dawne nazwy („light”, „dark”, „dobra-kaloria”, „dobra-kaloria-ciemny”) mapuje ``resolve_theme``.
Jeden arkusz ``app.qss`` ze znacznikami ``@NAZWA@``; każdy motyw definiuje każdy znacznik.
Nagłówki: Mindset wielkimi literami, etykiety sekcji: Lato Bold wersalikami (``typography.py``).
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.themes.palettes import LADDER, ROLES, SHAPE, TAGS

STYLE_ZIELEN = "zielen"
STYLE_KREM = "krem"
MODE_LIGHT = "jasny"
MODE_DARK = "ciemny"
STYLES: tuple[str, ...] = (STYLE_ZIELEN, STYLE_KREM)
MODES: tuple[str, ...] = (MODE_LIGHT, MODE_DARK)
STYLE_LABELS: dict[str, str] = {
    STYLE_ZIELEN: "Dobra Kaloria 1 · zieleń",
    STYLE_KREM: "Dobra Kaloria 2 · krem",
}
MODE_LABELS: dict[str, str] = {MODE_LIGHT: "Tryb jasny", MODE_DARK: "Tryb ciemny"}
DEFAULT_STYLE = STYLE_ZIELEN
DEFAULT_MODE = MODE_LIGHT


def theme_id(style: str, mode: str) -> str:
    return f"dobra-kaloria-{style}-{mode}"


def split_theme(theme: str) -> tuple[str, str]:
    """'dobra-kaloria-krem-ciemny' → ('krem', 'ciemny')."""
    style, mode = resolve_theme(theme).rsplit("-", 2)[-2:]
    return style, mode


THEMES: tuple[str, ...] = tuple(theme_id(s, m) for s in STYLES for m in MODES)
DEFAULT_THEME = theme_id(DEFAULT_STYLE, DEFAULT_MODE)

# Nazwy zapisane przez starsze wersje. Nic nie wraca do wyglądu indygo.
_LEGACY_THEMES: dict[str, str] = {
    "dark": theme_id(STYLE_ZIELEN, MODE_DARK),
    "dobra-kaloria-ciemny": theme_id(STYLE_ZIELEN, MODE_DARK),
    "dobra-kaloria": theme_id(STYLE_KREM, MODE_LIGHT),
    "dobra-kaloria-krem": theme_id(STYLE_KREM, MODE_DARK),
}

def _px(value: str) -> float:
    return float(value.removesuffix("px"))


# Kształt z design systemu (palettes.SHAPE ← tokens_qt.py): promienie, obrysy, fokus, pole wyboru.
# Obrys przycisku drugorzędnego (1 px zamiast dawnych 2 px): QSS min/max-height nie liczy ramki ani dopełnienia,
# więc dopełnienie pionowe = 2 px (dawny obrys) − obrys: wysokość całkowita przycisku bez zmian.
BTN2_BORDER_PX = int(_px(SHAPE["btn2_border_width"]))
BTN2_LEGACY_RIM_PX = 2
# Pole wyboru: bok wskaźnika w interfejsie (generate_check_icons.LOGICAL musi się zgadzać; test pilnuje).
CHECK_SIZE_PX = int(_px(SHAPE["check_size"]))
# Pole tekstowe: obrys i fokus; dopełnienie przy fokusie jest mniejsze o różnicę (app.qss), żeby tekst się nie ruszał.
FIELD_BORDER_PX = int(_px(SHAPE["field_border"]))
FOCUS_BORDER_PX = int(_px(SHAPE["focus_border"]))
CHIP_H_PX = 48  # chip formatu = wysokość przycisku Konwertuj
CHIP_PAD_PX = 12
# Suwak (wzorzec): tor 8 px, uchwyt 24 px łącznie z obrysem 2 px (QSS width/height nie liczy obrysu)
SLIDER_TRACK_PX = 8
SLIDER_THUMB_PX = 24
SLIDER_THUMB_BORDER_PX = int(_px(SHAPE["slider_thumb_border_width"]))

_SHAPE: dict[str, str] = {
    "@BTN2_BORDER_W@": f"{BTN2_BORDER_PX}px",
    "@BTN2_PAD_V@": f"{BTN2_LEGACY_RIM_PX - BTN2_BORDER_PX}px",
    "@QUIET_PAD_V@": f"{BTN2_LEGACY_RIM_PX}px",  # przycisk cichy: brak obrysu, więc całe dawne 2 px idzie w dopełnienie
    "@CHECK_SIZE@": f"{CHECK_SIZE_PX}px",
    "@FIELD_BORDER_W@": SHAPE["field_border"],
    "@FOCUS_W@": SHAPE["focus_border"],
    # chip formatu: 48 px wysokości bez obrysu; przy fokusie obrys odejmujemy od wysokości i dopełnienia
    "@SLIDER_TRACK_H@": f"{SLIDER_TRACK_PX}px",
    "@SLIDER_THUMB_INNER@": f"{SLIDER_THUMB_PX - 2 * SLIDER_THUMB_BORDER_PX}px",
    "@SLIDER_THUMB_BORDER_W@": f"{SLIDER_THUMB_BORDER_PX}px",
    "@SLIDER_THUMB_MARGIN@": f"-{(SLIDER_THUMB_PX - SLIDER_TRACK_PX) // 2}px",
    "@CHIP_H@": f"{CHIP_H_PX}px",
    "@CHIP_PAD@": f"{CHIP_PAD_PX}px",
    "@CHIP_FOCUS_H@": f"{CHIP_H_PX - 2 * FOCUS_BORDER_PX}px",
    "@CHIP_FOCUS_PAD@": f"{CHIP_PAD_PX - FOCUS_BORDER_PX}px",
    "@FONT_FAMILY@": '"Lato", "Segoe UI", sans-serif',
    "@FONT_DISPLAY@": '"Mindset", "Lato", "Segoe UI", sans-serif',
    "@RADIUS_BTN@": SHAPE["radius_btn"],
    "@RADIUS_FIELD@": SHAPE["radius_field"],
    "@RADIUS_CARD@": SHAPE["radius_card"],
    "@RADIUS_DROP@": SHAPE["radius_drop"],
    "@FS_BTN@": SHAPE["fs_btn"],
    "@FS_BTN_PRIMARY@": SHAPE["fs_btn_primary"],
}


TAG_COUNT = 8

# Tagi DS 2.0.5 to 8 różnych barw w jasnych motywach (1 zieleń, 2 limonka, 3 żółć, 4 pomarańcz, 5 czerwień, 6 róż,
# 7 turkus, 8 błękit). Każdy format ma własną barwę, ta sama wszędzie (chip trybu prostego, znacznik w oknie
# konwersji). Trzy główne formaty są wyraźnie różne: PNG zielony, JPG pomarańczowy, AVIF błękitny.
# Kategorię niesie też napis na tagu, nie sam kolor.
_FORMAT_TAG: dict[str, int] = {
    "png": 1,
    "jpeg": 4,
    "jpg": 4,
    "avif": 8,
    "webp": 3,
    "gif": 5,
    "tif": 6,
    "tiff": 6,
    "jp2": 7,
    "heic": 7,
    "heif": 7,
}
DEFAULT_TAG = 2  # inne rozszerzenia: limonka


def format_tag(fmt: str | None) -> int:
    """Numer tagu (1..TAG_COUNT) dla rozszerzenia — ten sam kolor formatu w całym programie."""
    return _FORMAT_TAG.get(str(fmt or "").lower().lstrip("."), DEFAULT_TAG)


def _tag_tokens(tags: list[tuple[str, str, str]]) -> dict[str, str]:
    """(tło, ramka, tekst) tagów 1..TAG_COUNT → znaczniki @TAG<n>_BG@ / _BORDER@ / _FG@."""
    assert len(tags) == TAG_COUNT, len(tags)
    out: dict[str, str] = {}
    for n, (bg, border, fg) in enumerate(tags, start=1):
        out[f"@TAG{n}_BG@"] = bg
        out[f"@TAG{n}_BORDER@"] = border
        out[f"@TAG{n}_FG@"] = fg
    return out


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    rgb = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _readable_on(background: str, *candidates: str) -> str:
    """Z kandydatów ten o największym kontraście względem tła (księżyc na gałce przełącznika)."""
    lb = _luminance(background)

    def ratio(c: str) -> float:
        lc = _luminance(c)
        return (max(lb, lc) + 0.05) / (min(lb, lc) + 0.05)

    return max(candidates, key=ratio)


# Obrazy pola wyboru (icons/cb-<klucz>-<stan>.png, rb-… dla radio): stan → (najechanie, fokus, zaznaczone, wyłączone).
CHECK_STATES: dict[str, tuple[bool, bool, bool, bool]] = {
    "off": (False, False, False, False),
    "off-hover": (True, False, False, False),
    "off-focus": (False, True, False, False),
    "on": (False, False, True, False),
    "on-hover": (True, False, True, False),
    "on-focus": (False, True, True, False),
    "off-dis": (False, False, False, True),
    "on-dis": (False, False, True, True),
}


def check_image_names(key: str) -> list[str]:
    return [f"{kind}-{key}-{state}.png" for kind in ("cb", "rb") for state in CHECK_STATES]


def _tokens(r: dict[str, str], *, window: str, panel: str, panel_alt: str, field: str,
            hover: str, scrim: str, menu_bg: str, l3: str, l4: str,
            tags: list[tuple[str, str, str]]) -> dict[str, str]:
    """Znaczniki app.qss z ról design systemu (nazwy ról jak w tokens_qt.py).

    Drabina powierzchni (design system 2.0 „sklep”; głębokość = rodzic + 1): L0 ``window`` (biel) → L1 ``panel``
    (sekcja, bez obrysu) → L2 ``field``/``panel_alt`` (biała karta, pole, lista, tabela — W panelu) → L3 ``l3``
    (kafel w karcie) → L4 ``l4`` (kafel w kaflu). Nakładki (menu, popup, podpowiedź, toast, karta overlay) to rola
    ``color_overlay`` + ramka 1 px ``border``, nie L4.
    """
    return {
        "@BG_WINDOW@": window,
        "@BG_PANEL@": panel,
        "@BG_PANEL_ALT@": panel_alt,
        "@BG_INPUT@": field,
        "@BG_BUTTON@": field,
        "@BG_L3@": l3,
        "@BG_L4@": l4,
        "@BG_HOVER@": hover,
        **_tag_tokens(tags),
        # Każdy kolor to rola z palettes.py (generowane z design systemu przez scripts/sync_design_tokens.py):
        # akcent, ikony, kontrolki z ról accent / icon / check / slider / switch / btn2 / step. Role color_brand*
        # (logo, kafle KPI, kropka „online”) nie są tu używane. Wartości zmienia sync, nie ten plik.
        "@BG_OVERLAY@": r["color_overlay"],  # menu, popup, podpowiedź, toast, karta okna konwersji
        "@BG_STRIP@": r["color_strip"],  # pasek menu
        "@BG_ZEBRA@": r["color_zebra"],  # pasy tabeli i listy
        "@BRAND_SOFT@": r["color_brand_soft"],  # najechanie na wiersz, zaznaczenie w menu i popupie
        "@PRIMARY_BG@": r["color_brand"],  # przycisk główny (zielony pełny)
        "@PRIMARY_HOVER@": r["color_brand_hover"],
        "@PRIMARY_TEXT@": r["color_on_brand"],
        "@PROGRESS@": r["color_progress"],  # pasek postępu (na torze slider-track)
        "@FG_TITLE@": r["color_heading"],  # tytuł karty / okna (Mindset)
        "@FG_HEADING_ACCENT@": r["color_heading_accent"],  # tytuł widoku, nadtytuł sekcji, aktywna zakładka
        "@FG_TEXT@": r["color_text"],
        "@FG_MUTED@": r["color_text_muted"],
        "@FG_LABEL@": r["color_label"],
        "@FG_ACCENT@": r["color_accent"],  # link, licznik, tytuł akcentowy, aktywna zakładka
        "@ACCENT@": r["color_slider_fill"],  # wypełnienia (pasek postępu)
        "@ACCENT_HOVER@": r["color_accent_hover"],
        "@ON_ACCENT@": r["color_on_accent"],
        "@ACCENT_GRAD_END@": r["color_accent_hover"],
        "@ICON@": r["color_icon"],
        "@ICON_BG@": r["color_icon_bg"],
        "@BTN2_BG@": r["color_btn2_bg"],
        "@BTN2_TEXT@": r["color_btn2_text"],
        "@BTN2_BORDER@": r["color_btn2_border"],
        "@BTN2_HOVER@": r["color_btn2_hover_bg"],
        "@BTN2_PRESSED@": r["color_brand_soft_strong"],  # S14: bez L3/ecru jako wypełnienia stanu
        "@SELECT_BG@": r["color_step_active_bg"],  # tylko aktywny przełącznik-segment (cropAnchorBtn:checked)
        "@SELECT_FG@": r["color_step_active_text"],
        # zaznaczony wiersz (drzewo, lista, tabela): brand-soft-strong + tekst text (pogrubienie robi delegat); najechanie: brand-soft
        "@ROW_SELECTED_BG@": r["color_brand_soft_strong"],
        "@ROW_SELECTED_FG@": r["color_text"],
        "@ROW_HOVER@": r["color_brand_soft"],
        # zaznaczenie w nakładkach (menu, lista rozwijana): zawsze brand-soft — w ciemnych motywach nakładka
        # (overlay) ma kolor L4, więc ROW_SELECTED (L4) zlałby się z jej tłem
        "@POPUP_SELECTED_BG@": r["color_brand_soft"],
        "@BRAND_SOFT_STRONG@": r["color_brand_soft_strong"],
        "@SLIDER_TRACK@": r["color_slider_track"],
        "@SLIDER_FILL@": r["color_slider_fill"],
        "@SLIDER_THUMB@": r["color_slider_thumb"],
        "@SLIDER_THUMB_BORDER@": r["color_slider_thumb_border"],
        "@SWITCH_OFF@": r["color_switch_off"],
        "@SWITCH_OFF_BORDER@": r["color_switch_off_border"],
        "@SWITCH_ON@": r["color_switch_on"],
        "@SWITCH_KNOB@": r["color_switch_knob"],
        "@SWITCH_SUN@": r["color_switch_on"],  # słońce na gałce w jasnym trybie
        "@SWITCH_MOON@": _readable_on(r["color_switch_knob"], r["color_text"], r["color_on_accent"]),
        "@BORDER@": r["color_border_strong"],
        "@SEP@": r["color_border"],
        "@FIELD_BORDER@": r["color_field_border"],
        "@BORDER_FOCUS@": r["color_focus"],
        "@COMBO_BORDER@": r["color_border"],
        "@DISABLED_BG@": r["color_disabled_bg"],
        # DS 2.0 (S2): sekcja = panel L1 bez obrysu i bez cienia; linia 1 px roli border tylko tam, gdzie karta leży
        # wprost na tle okna (to robi QSS przy konkretnej karcie).
        "@CARD_BORDER@": "none",
        "@LINE@": f"1px solid {r['color_border']}",
        "@MENU_STRIP_BG@": menu_bg,
        "@MENU_STRIP_BORDER@": f"1px solid {r['color_border']}",
        "@DROP_BORDER@": f"1px dashed {r['color_field_border']}",  # wzorzec: cienka przerywana ramka pola
        "@CTA_BG@": r["color_cta"],
        "@CTA_HOVER@": r["color_cta_hover"],
        "@CTA_TEXT@": r["color_on_cta"],
        "@FOOTER_CLOSE_BG@": "transparent",
        "@FOOTER_CLOSE_HOVER@": hover,
        "@FOOTER_CLOSE_BORDER@": "transparent",
        "@UPDATE_TOAST_BG@": r["color_overlay"],
        "@UPDATE_TOAST_BORDER@": r["color_border"],
        "@UPDATE_TOAST_TITLE@": r["color_heading"],
        "@UPDATE_TOAST_TEXT@": r["color_text_muted"],
        "@UPDATE_TOAST_PROGRESS@": r["color_text_muted"],
        "@UPDATE_TOAST_INSTALL_BG@": r["color_brand"],
        "@UPDATE_TOAST_INSTALL_HOVER@": r["color_brand_hover"],
        "@UPDATE_TOAST_INSTALL_TEXT@": r["color_on_brand"],
        "@UPDATE_TOAST_LATER_BG@": panel_alt,
        "@UPDATE_TOAST_LATER_HOVER@": hover,
        "@UPDATE_TOAST_LATER_TEXT@": r["color_text"],
        "@UPDATE_TOAST_LATER_BORDER@": r["color_border_strong"],
        "@OVERLAY_SCRIM@": scrim,
        "@OVERLAY_ABORT_COLOR@": r["color_danger"],
        "@OVERLAY_ABORT_BORDER@": r["color_border_strong"],
        "@OVERLAY_ABORT_HOVER_BG@": r["color_danger_soft"],
        "@OVERLAY_ABORT_PRESSED@": hover,
        "@OVERLAY_HINT@": r["color_text_muted"],
        **_SHAPE,
    }


def _qss_rgba(css_rgba: str) -> str:
    """rgba(59,42,32,.55) (CSS, alfa 0–1) → rgba(59, 42, 32, 140) (QSS, alfa 0–255)."""
    m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", css_rgba.strip())
    assert m, css_rgba
    r, g, b = (int(x) for x in m.groups()[:3])
    return f"rgba({r}, {g}, {b}, {round(float(m.group(4)) * 255)})"


# Zasłona okien modalnych: jasne motywy = ciepły brąz z DS (SHAPE shadow_scrim, rgba(59,42,32,.55)); ciemne zostają
# przy własnych, ciemniejszych wartościach (DS nie ma dla nich roli).
_SCRIM: dict[str, str] = {
    "zielen-jasny": _qss_rgba(SHAPE["scrim"]),
    "zielen-ciemny": "rgba(8, 18, 12, 0.62)",
    "krem-jasny": _qss_rgba(SHAPE["scrim"]),
    "krem-ciemny": "rgba(20, 16, 11, 0.62)",
}


def _theme_tokens(key: str) -> dict[str, str]:
    """Motyw ``<styl>-<tryb>`` z drabiny powierzchni L0…L4 i tagów design systemu (palettes.py)."""
    lad = LADDER[key]
    tokens = _tokens(
        ROLES[key],
        window=lad["surface_0"],
        panel=lad["surface_1"],
        menu_bg=lad["surface_0"],
        panel_alt=lad["surface_2"],
        field=lad["surface_2"],
        hover=ROLES[key]["color_surface_hover"],
        l3=lad["surface_3"],
        l4=lad["surface_4"],
        scrim=_SCRIM[key],
        tags=TAGS[key],
    )
    # TRYB (znana luka DS 2.0: brak roli „zaznaczony wiersz”). W motywach ciemnych brand_soft jest prawie tym samym
    # kolorem co tło listy i najechanie, więc zaznaczenie dostaje poziom L4 drabiny, a najechanie L3 (głębiej =
    # jaśniej). W jasnych zostaje brand_soft / surface_hover z roli.
    if key.endswith("-ciemny"):
        tokens["@ROW_SELECTED_BG@"] = lad["surface_4"]
        tokens["@ROW_HOVER@"] = lad["surface_3"]
    return tokens


_THEME_TOKENS: dict[str, dict[str, str]] = {
    theme_id(s, m): _theme_tokens(f"{s}-{m}") for s in STYLES for m in MODES
}

_CURRENT_THEME = DEFAULT_THEME

# Krój interfejsu. Pliki w themes/fonts/: Lato (OFL 1.1), Mindset (licencja komercyjna firmy).
FONT_TEXT = "Lato"
FONT_DISPLAY = "Mindset"
_FALLBACK_FONT_FAMILY = "Segoe UI"
_FONT_PIXEL_SIZE = 15  # DS 1.5.0 qt.fs-body (program: 16 px)
_FONT_FILES = ("Lato-Regular.ttf", "Lato-Bold.ttf", "Mindset.otf")
_LOADED_FAMILIES: set[str] | None = None


def resolve_theme(theme: str | None) -> str:
    """Dowolna zapisana wartość → jeden z czterech motywów DK (nieznana → domyślny)."""
    if theme in _THEME_TOKENS:
        return theme  # type: ignore[return-value]
    return _LEGACY_THEMES.get(str(theme), DEFAULT_THEME)


normalize_theme = resolve_theme


def current_theme() -> str:
    return _CURRENT_THEME


def is_dark_theme(theme: str | None = None) -> bool:
    return split_theme(theme if theme is not None else _CURRENT_THEME)[1] == MODE_DARK


def theme_token(name: str, theme: str | None = None) -> str:
    """Wartość znacznika (np. "@ACCENT@") — dla kodu, który rysuje sam (QPainter)."""
    return _THEME_TOKENS[resolve_theme(theme if theme is not None else _CURRENT_THEME)][name]


def fonts_dir() -> Path:
    return Path(__file__).resolve().parent / "fonts"


def register_fonts() -> set[str]:
    """Rejestruje czcionki z paczki (raz na proces). Zwraca nazwy wczytanych rodzin."""
    global _LOADED_FAMILIES
    if _LOADED_FAMILIES is not None:
        return _LOADED_FAMILIES
    families: set[str] = set()
    for name in _FONT_FILES:
        path = fonts_dir() / name
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families.update(QFontDatabase.applicationFontFamilies(font_id))
    _LOADED_FAMILIES = families
    return families


def theme_font_family(theme: str | None = None) -> str:
    """Krój tekstu: Lato z paczki, Segoe UI tylko gdy plików zabrakło."""
    return FONT_TEXT if FONT_TEXT in register_fonts() else _FALLBACK_FONT_FAMILY


def display_font_family() -> str:
    """Krój nagłówków: Mindset z paczki, inaczej krój tekstu."""
    return FONT_DISPLAY if FONT_DISPLAY in register_fonts() else theme_font_family()


def _icon_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "icons" / name


def _themed_icon(prefix: str, theme: str) -> Path:
    style, mode = split_theme(theme)
    return _icon_path(f"{prefix}-{style}-{mode}.png")


# Przyciski ciche (S13): bez obrysu. Wypełnienie zależy od tego, na czym leżą: domyślnie icon-bg (na białym oknie),
# na panelu / pasku menu / zakładce dialogu = L2 (biel). Reguły dla przodka mają wyższą specyficzność niż domyślne,
# więc każdy stan jest powtórzony dla każdego przodka — generujemy je tutaj, żeby nie utrzymywać ich ręcznie.
QUIET_BUTTONS: tuple[str, ...] = ("QPushButton#toolBtn", "QPushButton#btnUpdatePath", 'QPushButton[quiet="true"]')
QUIET_PANELS: tuple[str, ...] = (
    "QFrame#bentoTile", "QFrame#sectionBox", "QFrame#dialogPanel", "QTabWidget#dialogTabs",
)
# kafelek variant="plain" leży na białym oknie (jak pasek menu) — tam przycisk cichy ma wypełnienie icon-bg
QUIET_PLAIN: tuple[str, ...] = ('QFrame#bentoTile[variant="plain"]',)


def _quiet_rules() -> str:
    def group(state: str = "", *, panels: bool = False) -> str:
        names = [f"{p} {b}" for p in QUIET_PANELS for b in QUIET_BUTTONS] if panels else list(QUIET_BUTTONS)
        return ",\n".join(f"{n}{state}" for n in names)

    def rule(sel: str, body: str) -> str:
        return f"{sel} {{\n    {body}\n}}\n"

    out = [
        rule(group(), "background-color: @ICON_BG@; border: none; color: @FG_TEXT@;"),
        rule(group(panels=True), "background-color: @BG_INPUT@;"),
        # po regułach panelu (ta sama specyficzność, wygrywa późniejsza), przed stanami hover / pressed / disabled
        rule(",\n".join(f"{p} {b}" for p in QUIET_PLAIN for b in QUIET_BUTTONS), "background-color: @ICON_BG@;"),
    ]
    hover = "background-color: @BRAND_SOFT@; color: @FG_TEXT@;"
    for state in (":hover", ":focus"):
        out.append(rule(group(state), hover))
        out.append(rule(group(state, panels=True), hover))
    out.append(rule(group(":focus"), "text-decoration: underline;"))
    out.append(rule(group(":focus", panels=True), "text-decoration: underline;"))
    pressed = "background-color: @BRAND_SOFT_STRONG@;"
    out.append(rule(group(":pressed"), pressed))
    out.append(rule(group(":pressed", panels=True), pressed))
    dis = "background-color: @DISABLED_BG@; color: @FG_MUTED@;"
    out.append(rule(group(":disabled"), dis))
    out.append(rule(group(":disabled", panels=True), dis))
    return "\n".join(out)


def render_qss(theme: str) -> str:
    """Arkusz z podstawionymi znacznikami (bez nakładania na aplikację)."""
    theme = resolve_theme(theme)
    qss = (Path(__file__).resolve().parent / "app.qss").read_text(encoding="utf-8")
    qss = qss.replace("@QUIET_RULES@", _quiet_rules())
    tokens = dict(_THEME_TOKENS[theme])
    if theme_font_family() != FONT_TEXT:
        tokens["@FONT_FAMILY@"] = f'"{_FALLBACK_FONT_FAMILY}", sans-serif'
    if display_font_family() != FONT_DISPLAY:
        tokens["@FONT_DISPLAY@"] = tokens["@FONT_FAMILY@"]
    for token, value in tokens.items():
        qss = qss.replace(token, value)

    # Pole wyboru: gotowe obrazy stanów (icons/cb-<klucz>-<stan>.png, rb-…) — jedyny sposób na obrys 1,5 px.
    qss = qss.replace("@ICON_DIR@", _icon_path("").as_posix().rstrip("/"))
    qss = qss.replace("@THEME_KEY@", "-".join(split_theme(theme)))

    combo_arrow = _themed_icon("combo-down", theme)
    if combo_arrow.is_file():
        qss = qss.replace("@COMBO_ARROW@", combo_arrow.as_posix())
    return qss


def apply_theme(app: QApplication, theme: str = DEFAULT_THEME) -> None:
    global _CURRENT_THEME
    from inyfinn_resizer.app.themes.typography import install_typography

    _CURRENT_THEME = resolve_theme(theme)
    install_typography(app)
    font = QFont(app.font())
    font.setFamily(theme_font_family())
    font.setPixelSize(_FONT_PIXEL_SIZE)
    app.setFont(font)
    # styl Windows rysuje menu czcionką klasy, nie widżetu
    app.setFont(font, "QMenuBar")
    app.setFont(font, "QMenu")
    app.setStyleSheet(render_qss(_CURRENT_THEME))
