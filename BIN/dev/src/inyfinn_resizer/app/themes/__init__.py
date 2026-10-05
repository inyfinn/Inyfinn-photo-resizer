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

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.themes.palettes import LADDER, ROLES, TAGS

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

_SHAPE: dict[str, str] = {
    "@FONT_FAMILY@": '"Lato", "Segoe UI", sans-serif',
    "@FONT_DISPLAY@": '"Mindset", "Lato", "Segoe UI", sans-serif',
    "@RADIUS_BTN@": "4px",
    "@RADIUS_FIELD@": "8px",
    "@RADIUS_CARD@": "12px",
    "@RADIUS_DROP@": "16px",
}


TAG_COUNT = 8

# Kolejność kategorii tagów (formaty plików). Kategorię niesie też napis na tagu, nie sam kolor.
_FORMAT_TAG: dict[str, int] = {
    "png": 1,
    "jpeg": 2,
    "jpg": 2,
    "avif": 3,
    "webp": 4,
    "gif": 5,
    "tif": 6,
    "tiff": 6,
    "jp2": 7,
    "heic": 7,
    "heif": 7,
}


def format_tag(fmt: str | None) -> int:
    """Numer tagu (1..TAG_COUNT) dla rozszerzenia — ten sam kolor formatu w całym programie."""
    return _FORMAT_TAG.get(str(fmt or "").lower().lstrip("."), TAG_COUNT)


def _tag_tokens(tags: list[tuple[str, str, str]]) -> dict[str, str]:
    """(tło, ramka, tekst) tagów 1..TAG_COUNT → znaczniki @TAG<n>_BG@ / _BORDER@ / _FG@."""
    assert len(tags) == TAG_COUNT, len(tags)
    out: dict[str, str] = {}
    for n, (bg, border, fg) in enumerate(tags, start=1):
        out[f"@TAG{n}_BG@"] = bg
        out[f"@TAG{n}_BORDER@"] = border
        out[f"@TAG{n}_FG@"] = fg
    return out


def _tokens(r: dict[str, str], *, window: str, panel: str, panel_alt: str, field: str,
            hover: str, scrim: str, menu_bg: str, l3: str, l4: str,
            tags: list[tuple[str, str, str]]) -> dict[str, str]:
    """Znaczniki app.qss z ról design systemu (nazwy ról jak w tokens_qt.py).

    Drabina powierzchni (design system 1.4.0): L0 ``window`` → L1 ``panel`` (karta, pasek menu, okno
    dialogu) → L2 ``field``/``panel_alt`` (rubryki: pola, listy, tabela, podgląd, zakładki) → L3 ``l3``
    (element w rubryce: co drugi wiersz, pole na zakładce, najechanie w liście) → L4 ``l4`` (menu,
    rozwinięta lista, podpowiedź).
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
        "@BRAND_SOFT@": r["color_brand_soft"],
        "@FG_TITLE@": r["color_text"],
        "@FG_TEXT@": r["color_text"],
        "@FG_MUTED@": r["color_text_muted"],
        "@FG_LABEL@": r["color_label"],
        "@FG_ACCENT@": r["color_brand"],
        "@ACCENT@": r["color_brand"],
        "@ACCENT_HOVER@": r["color_brand_hover"],
        "@ON_ACCENT@": r["color_on_brand"],
        "@ACCENT_GRAD_END@": r["color_brand_hover"],
        "@BORDER@": r["color_border_strong"],
        "@SEP@": r["color_border"],
        "@FIELD_BORDER@": r["color_field_border"],
        "@BORDER_FOCUS@": r["color_focus"],
        "@COMBO_BORDER@": r["color_border"],
        "@DISABLED_BG@": r["color_disabled_bg"],
        # DS 1.5.0: karta jak w programie (.hints/.found) — kremowa L1 na białym L0, cienka ramka roli border.
        "@CARD_BORDER@": f"1px solid {r['color_border']}",
        "@MENU_STRIP_BG@": menu_bg,
        "@MENU_STRIP_BORDER@": f"1px solid {r['color_border']}",
        "@DROP_BORDER@": f"2px dashed {r['color_label']}",
        "@CTA_BG@": r["color_cta"],
        "@CTA_HOVER@": r["color_cta_hover"],
        "@CTA_TEXT@": r["color_on_cta"],
        "@FOOTER_CLOSE_BG@": "transparent",
        "@FOOTER_CLOSE_HOVER@": hover,
        "@FOOTER_CLOSE_BORDER@": "transparent",
        "@UPDATE_TOAST_BG@": panel,
        "@UPDATE_TOAST_BORDER@": r["color_brand"],
        "@UPDATE_TOAST_TITLE@": r["color_text"],
        "@UPDATE_TOAST_TEXT@": r["color_text_muted"],
        "@UPDATE_TOAST_PROGRESS@": r["color_text_muted"],
        "@UPDATE_TOAST_INSTALL_BG@": r["color_cta"],
        "@UPDATE_TOAST_INSTALL_HOVER@": r["color_cta_hover"],
        "@UPDATE_TOAST_INSTALL_TEXT@": r["color_on_cta"],
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


_SCRIM: dict[str, str] = {
    "zielen-jasny": "rgba(23, 41, 29, 0.42)",
    "zielen-ciemny": "rgba(8, 18, 12, 0.62)",
    "krem-jasny": "rgba(59, 42, 32, 0.42)",
    "krem-ciemny": "rgba(20, 16, 11, 0.62)",
}


def _theme_tokens(key: str) -> dict[str, str]:
    """Motyw ``<styl>-<tryb>`` z drabiny powierzchni L0…L4 i tagów design systemu (palettes.py)."""
    lad = LADDER[key]
    return _tokens(
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


def render_qss(theme: str) -> str:
    """Arkusz z podstawionymi znacznikami (bez nakładania na aplikację)."""
    theme = resolve_theme(theme)
    qss = (Path(__file__).resolve().parent / "app.qss").read_text(encoding="utf-8")
    tokens = dict(_THEME_TOKENS[theme])
    if theme_font_family() != FONT_TEXT:
        tokens["@FONT_FAMILY@"] = f'"{_FALLBACK_FONT_FAMILY}", sans-serif'
    if display_font_family() != FONT_DISPLAY:
        tokens["@FONT_DISPLAY@"] = tokens["@FONT_FAMILY@"]
    for token, value in tokens.items():
        qss = qss.replace(token, value)

    check = _themed_icon("check", theme)
    if check.is_file():
        qss = qss.replace("@CHECK_ICON@", check.as_posix())

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
