"""Theme loader — wspólna struktura + zamiana kolorów."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

_THEME_TOKENS: dict[str, dict[str, str]] = {
    "light": {
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
    },
    "dark": {
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
    },
}


_CURRENT_THEME = "light"


def current_theme() -> str:
    """Ostatnio zastosowany motyw ('light' / 'dark')."""
    return _CURRENT_THEME


def _icon_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "icons" / name


def apply_theme(app: QApplication, theme: str = "light") -> None:
    global _CURRENT_THEME
    _CURRENT_THEME = theme if theme in _THEME_TOKENS else "light"
    base_path = Path(__file__).resolve().parent / "app.qss"
    qss = base_path.read_text(encoding="utf-8")
    tokens = _THEME_TOKENS.get(theme, _THEME_TOKENS["light"])
    for token, value in tokens.items():
        qss = qss.replace(token, value)

    check = _icon_path("check-light.png" if theme == "light" else "check-dark.png")
    if check.is_file():
        qss = qss.replace("@CHECK_ICON@", check.as_posix())

    combo_arrow = _icon_path("combo-down-light.png" if theme == "light" else "combo-down-dark.png")
    if combo_arrow.is_file():
        qss = qss.replace("@COMBO_ARROW@", combo_arrow.as_posix())

    app.setStyleSheet(qss)
