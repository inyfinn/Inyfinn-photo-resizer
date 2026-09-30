"""Theme loader — wspólna struktura + zamiana kolorów.

Motywy: "dobra-kaloria" (domyślny od 2.6.0, design system Dobra Kaloria — ten sam wygląd co
program „Stwórz prezentację”), "light" (dawny domyślny, indygo) i "dark".
Jeden arkusz ``app.qss`` ze znacznikami ``@NAZWA@``; każdy motyw definiuje każdy znacznik.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_DK = "dobra-kaloria"
DEFAULT_THEME = THEME_DK
THEMES: tuple[str, ...] = (THEME_DK, THEME_LIGHT, THEME_DARK)
THEME_LABELS: dict[str, str] = {
    THEME_DK: "Motyw Dobra Kaloria",
    THEME_LIGHT: "Jasny motyw",
    THEME_DARK: "Ciemny motyw",
}

# Kształt i krój wspólne dla jasnego i ciemnego (wygląd sprzed 2.6.0 — bez zmian).
_CLASSIC_SHAPE: dict[str, str] = {
    "@FONT_FAMILY@": '"Segoe UI", system-ui, sans-serif',
    "@RADIUS_BTN@": "10px",
    "@RADIUS_FIELD@": "10px",
    "@RADIUS_CARD@": "16px",
    "@CARD_BORDER@": "none",
    "@MENU_STRIP_BG@": "transparent",
    "@MENU_STRIP_BORDER@": "none",
    "@DROP_BORDER@": "none",
    "@RADIUS_DROP@": "10px",
}

_THEME_TOKENS: dict[str, dict[str, str]] = {
    THEME_LIGHT: {
        "@BG_WINDOW@": "#EEF1F6",
        "@BG_PANEL@": "#FFFFFF",
        "@BG_PANEL_ALT@": "#F2F5F9",
        "@BG_INPUT@": "#F2F5F9",
        "@BG_BUTTON@": "#F2F5F9",
        "@BG_HOVER@": "#E8EDF5",
        "@FG_TITLE@": "#0F172A",
        "@FG_TEXT@": "#1F2937",
        "@FG_MUTED@": "#64748B",
        "@FG_ACCENT@": "#6366F1",
        "@ACCENT@": "#6366F1",
        "@ACCENT_HOVER@": "#4F46E5",
        "@BORDER@": "#E2E8F0",
        "@BORDER_FOCUS@": "#6366F1",
        "@COMBO_BORDER@": "#E2E8F0",
        "@SEP@": "#E8EDF5",
        "@FOOTER_CLOSE_BG@": "transparent",
        "@FOOTER_CLOSE_HOVER@": "#E8EDF5",
        "@FOOTER_CLOSE_BORDER@": "transparent",
        "@UPDATE_TOAST_BG@": "#FFFFFF",
        "@UPDATE_TOAST_BORDER@": "#6366F1",
        "@UPDATE_TOAST_TITLE@": "#0F172A",
        "@UPDATE_TOAST_TEXT@": "#475569",
        "@UPDATE_TOAST_PROGRESS@": "#64748B",
        "@UPDATE_TOAST_INSTALL_BG@": "#6366F1",
        "@UPDATE_TOAST_INSTALL_HOVER@": "#4F46E5",
        "@UPDATE_TOAST_INSTALL_TEXT@": "#FFFFFF",
        "@UPDATE_TOAST_LATER_BG@": "#F2F5F9",
        "@UPDATE_TOAST_LATER_HOVER@": "#E8EDF5",
        "@UPDATE_TOAST_LATER_TEXT@": "#334155",
        "@UPDATE_TOAST_LATER_BORDER@": "#E2E8F0",
        "@OVERLAY_SCRIM@": "rgba(15, 23, 42, 0.42)",
        "@OVERLAY_ABORT_COLOR@": "#EF4444",
        "@OVERLAY_ABORT_BORDER@": "#FECACA",
        "@OVERLAY_ABORT_HOVER_BG@": "#FEF2F2",
        "@OVERLAY_ABORT_PRESSED@": "#FEE2E2",
        "@OVERLAY_HINT@": "#64748B",
        "@CTA_BG@": "#6366F1",
        "@CTA_HOVER@": "#4F46E5",
        "@CTA_TEXT@": "#ffffff",
        "@ACCENT_GRAD_END@": "#7c3aed",
        **_CLASSIC_SHAPE,
    },
    THEME_DARK: {
        "@BG_WINDOW@": "#0E1116",
        "@BG_PANEL@": "#181C23",
        "@BG_PANEL_ALT@": "#212630",
        "@BG_INPUT@": "#212630",
        "@BG_BUTTON@": "#212630",
        "@BG_HOVER@": "#2A303B",
        "@FG_TITLE@": "#F1F5F9",
        "@FG_TEXT@": "#E2E8F0",
        "@FG_MUTED@": "#94A3B8",
        "@FG_ACCENT@": "#818CF8",
        "@ACCENT@": "#818CF8",
        "@ACCENT_HOVER@": "#A5B4FC",
        "@BORDER@": "#2A303B",
        "@BORDER_FOCUS@": "#818CF8",
        "@COMBO_BORDER@": "#2A303B",
        "@SEP@": "#242933",
        "@FOOTER_CLOSE_BG@": "transparent",
        "@FOOTER_CLOSE_HOVER@": "#2A303B",
        "@FOOTER_CLOSE_BORDER@": "transparent",
        "@UPDATE_TOAST_BG@": "#181C23",
        "@UPDATE_TOAST_BORDER@": "#818CF8",
        "@UPDATE_TOAST_TITLE@": "#F1F5F9",
        "@UPDATE_TOAST_TEXT@": "#CBD5E1",
        "@UPDATE_TOAST_PROGRESS@": "#94A3B8",
        "@UPDATE_TOAST_INSTALL_BG@": "#6366F1",
        "@UPDATE_TOAST_INSTALL_HOVER@": "#818CF8",
        "@UPDATE_TOAST_INSTALL_TEXT@": "#FFFFFF",
        "@UPDATE_TOAST_LATER_BG@": "#212630",
        "@UPDATE_TOAST_LATER_HOVER@": "#2A303B",
        "@UPDATE_TOAST_LATER_TEXT@": "#E2E8F0",
        "@UPDATE_TOAST_LATER_BORDER@": "#2A303B",
        "@OVERLAY_SCRIM@": "rgba(0, 0, 0, 0.58)",
        "@OVERLAY_ABORT_COLOR@": "#F87171",
        "@OVERLAY_ABORT_BORDER@": "#7F1D1D",
        "@OVERLAY_ABORT_HOVER_BG@": "#3F1515",
        "@OVERLAY_ABORT_PRESSED@": "#551818",
        "@OVERLAY_HINT@": "#94A3B8",
        "@CTA_BG@": "#818CF8",
        "@CTA_HOVER@": "#A5B4FC",
        "@CTA_TEXT@": "#ffffff",
        "@ACCENT_GRAD_END@": "#7c3aed",
        **_CLASSIC_SHAPE,
    },
    # Design system Dobra Kaloria 1.0.0 (skill ds-dobra-kaloria, themes/photo-resizer), tryb zwarty.
    # Względem szkicu: pola i przyciski na cream-100 (cream-50 na białym kafelku był niewidoczny),
    # żółty przycisk głównej akcji, Lato, promienie 4/8/12, cienka piaskowa ramka kart.
    THEME_DK: {
        "@BG_WINDOW@": "#FBF3E0",  # cream-100
        "@BG_PANEL@": "#FFFFFF",  # white
        "@BG_PANEL_ALT@": "#FDF8EC",  # cream-50
        "@BG_INPUT@": "#FBF3E0",  # cream-100
        "@BG_BUTTON@": "#FBF3E0",  # cream-100
        "@BG_HOVER@": "#F0EBDD",  # sand-150
        "@FG_TITLE@": "#3B2A20",  # brown-900
        "@FG_TEXT@": "#3B2A20",  # brown-900
        "@FG_MUTED@": "#7D5E44",  # brown-600
        "@FG_ACCENT@": "#0F763E",  # green-700
        "@ACCENT@": "#0F763E",  # green-700
        "@ACCENT_HOVER@": "#0B5F31",  # green-800
        "@BORDER@": "#D9CFBB",  # sand-300
        "@BORDER_FOCUS@": "#0F763E",  # green-700 (fokus = zieleń)
        "@COMBO_BORDER@": "#D9CFBB",  # sand-300
        "@SEP@": "#EDE7DA",  # sand-200
        "@FOOTER_CLOSE_BG@": "transparent",
        "@FOOTER_CLOSE_HOVER@": "#F0EBDD",  # sand-150
        "@FOOTER_CLOSE_BORDER@": "transparent",
        "@UPDATE_TOAST_BG@": "#FFFFFF",  # white
        "@UPDATE_TOAST_BORDER@": "#0F763E",  # green-700
        "@UPDATE_TOAST_TITLE@": "#3B2A20",  # brown-900
        "@UPDATE_TOAST_TEXT@": "#7D5E44",  # brown-600
        "@UPDATE_TOAST_PROGRESS@": "#7D5E44",  # brown-600
        "@UPDATE_TOAST_INSTALL_BG@": "#FFD42A",  # yellow-400
        "@UPDATE_TOAST_INSTALL_HOVER@": "#F6C700",  # yellow-500
        "@UPDATE_TOAST_INSTALL_TEXT@": "#3B2A20",  # brown-900
        "@UPDATE_TOAST_LATER_BG@": "#FDF8EC",  # cream-50
        "@UPDATE_TOAST_LATER_HOVER@": "#F0EBDD",  # sand-150
        "@UPDATE_TOAST_LATER_TEXT@": "#3B2A20",  # brown-900
        "@UPDATE_TOAST_LATER_BORDER@": "#D9CFBB",  # sand-300
        "@OVERLAY_SCRIM@": "rgba(59, 42, 32, 0.42)",
        "@OVERLAY_ABORT_COLOR@": "#DA272D",  # red-600
        "@OVERLAY_ABORT_BORDER@": "#F3B9BB",  # red-200
        "@OVERLAY_ABORT_HOVER_BG@": "#FCE8E9",  # red-50
        "@OVERLAY_ABORT_PRESSED@": "#F8D4D5",  # red-100
        "@OVERLAY_HINT@": "#7D5E44",  # brown-600
        "@CTA_BG@": "#FFD42A",  # yellow-400 — jedna główna akcja na ekran
        "@CTA_HOVER@": "#F6C700",  # yellow-500
        "@CTA_TEXT@": "#3B2A20",  # brown-900
        "@ACCENT_GRAD_END@": "#0B5F31",  # green-800
        "@FONT_FAMILY@": '"Lato", "Segoe UI", sans-serif',
        "@RADIUS_BTN@": "4px",
        "@RADIUS_FIELD@": "8px",
        "@RADIUS_CARD@": "12px",
        "@CARD_BORDER@": "1px solid #EDE7DA",  # sand-200
        "@MENU_STRIP_BG@": "#FFFFFF",  # biały pasek nagłówka nad kremowym obszarem pracy
        "@MENU_STRIP_BORDER@": "1px solid #EDE7DA",  # sand-200
        "@DROP_BORDER@": "2px dashed #AD8767",  # tan-400, strefa upuszczania
        "@RADIUS_DROP@": "16px",
    },
}


_CURRENT_THEME = DEFAULT_THEME

# Ikony z pliku: własne warianty motywu; jasny motyw bez własnych ikon bierze "light".
_ICON_VARIANT = {THEME_LIGHT: "light", THEME_DARK: "dark", THEME_DK: "dk"}

# Krój interfejsu (QApplication.setFont). Lato leży w paczce: themes/fonts/ (licencja OFL 1.1).
_THEME_FONT_FAMILY = {THEME_DK: "Lato"}
_CLASSIC_FONT_FAMILY = "Segoe UI"
_FONT_POINT_SIZE = 9
_FONT_FILES = ("Lato-Regular.ttf", "Lato-Bold.ttf")
_LOADED_FAMILIES: set[str] | None = None


def normalize_theme(theme: str | None) -> str:
    return theme if theme in _THEME_TOKENS else DEFAULT_THEME


def current_theme() -> str:
    """Ostatnio zastosowany motyw ('dobra-kaloria' / 'light' / 'dark')."""
    return _CURRENT_THEME


def is_dark_theme(theme: str | None = None) -> bool:
    return (theme if theme is not None else _CURRENT_THEME) == THEME_DARK


def theme_token(name: str, theme: str | None = None) -> str:
    """Wartość znacznika (np. "@ACCENT@") — dla kodu, który rysuje sam (QPainter)."""
    return _THEME_TOKENS[normalize_theme(theme if theme is not None else _CURRENT_THEME)][name]


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


def theme_font_family(theme: str) -> str:
    """Krój, którego motyw faktycznie użyje (Segoe UI, gdy plików Lato zabrakło)."""
    wanted = _THEME_FONT_FAMILY.get(normalize_theme(theme), _CLASSIC_FONT_FAMILY)
    if wanted == _CLASSIC_FONT_FAMILY:
        return wanted
    return wanted if wanted in register_fonts() else _CLASSIC_FONT_FAMILY


def _icon_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "icons" / name


def _themed_icon(prefix: str, theme: str) -> Path:
    fallback = "dark" if theme == THEME_DARK else "light"
    path = _icon_path(f"{prefix}-{_ICON_VARIANT.get(theme, fallback)}.png")
    return path if path.is_file() else _icon_path(f"{prefix}-{fallback}.png")


def render_qss(theme: str) -> str:
    """Arkusz z podstawionymi znacznikami (bez nakładania na aplikację)."""
    theme = normalize_theme(theme)
    qss = (Path(__file__).resolve().parent / "app.qss").read_text(encoding="utf-8")
    tokens = dict(_THEME_TOKENS[theme])
    if theme_font_family(theme) == _CLASSIC_FONT_FAMILY:
        tokens["@FONT_FAMILY@"] = _CLASSIC_SHAPE["@FONT_FAMILY@"]
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
    _CURRENT_THEME = normalize_theme(theme)
    font = QFont(app.font())
    font.setFamily(theme_font_family(_CURRENT_THEME))
    font.setPointSize(_FONT_POINT_SIZE)
    app.setFont(font)
    app.setStyleSheet(render_qss(_CURRENT_THEME))
