"""Theme loader — wspólna struktura + zamiana kolorów."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

_THEME_TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "@BG_WINDOW@": "#dde4ec",
        "@BG_PANEL@": "#ffffff",
        "@BG_PANEL_ALT@": "#f1f5f9",
        "@BG_INPUT@": "#ffffff",
        "@BG_BUTTON@": "#ffffff",
        "@BG_HOVER@": "#e0f2fe",
        "@FG_TEXT@": "#0f172a",
        "@FG_TITLE@": "#0f172a",
        "@FG_MUTED@": "#64748b",
        "@FG_ACCENT@": "#0369a1",
        "@BORDER@": "#94a3b8",
        "@BORDER_FOCUS@": "#0284c7",
        "@COMBO_BORDER@": "#7dd3fc",
        "@ACCENT@": "#0284c7",
        "@ACCENT_HOVER@": "#0369a1",
        "@SEP@": "rgba(0, 0, 0, 0.05)",
    },
    "dark": {
        "@BG_WINDOW@": "#0c1220",
        "@BG_PANEL@": "#141e34",
        "@BG_PANEL_ALT@": "#0f1729",
        "@BG_INPUT@": "#0f1729",
        "@BG_BUTTON@": "#1e2d4a",
        "@BG_HOVER@": "#1e3a5f",
        "@FG_TEXT@": "#f1f5f9",
        "@FG_TITLE@": "#f8fafc",
        "@FG_MUTED@": "#94a3b8",
        "@FG_ACCENT@": "#7dd3fc",
        "@BORDER@": "#4a5f8c",
        "@BORDER_FOCUS@": "#38bdf8",
        "@COMBO_BORDER@": "#38bdf8",
        "@ACCENT@": "#0284c7",
        "@ACCENT_HOVER@": "#0369a1",
        "@SEP@": "rgba(255, 255, 255, 0.08)",
    },
}


def _icon_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "icons" / name


def apply_theme(app: QApplication, theme: str = "light") -> None:
    base_path = Path(__file__).resolve().parent / "app.qss"
    if not base_path.is_file():
        legacy = Path(__file__).resolve().parent / f"{theme}.qss"
        if legacy.is_file():
            app.setStyleSheet(legacy.read_text(encoding="utf-8"))
        return

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
