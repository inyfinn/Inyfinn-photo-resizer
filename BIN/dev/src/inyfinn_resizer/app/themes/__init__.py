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
        "@SECTION1_BG@": "#f5f3ff",
        "@SECTION2_BG@": "#ecfdf5",
        "@SECTION3_BG@": "#fff7ed",
        "@S1_LABEL@": "#4338ca",
        "@S2_LABEL@": "#0f766e",
        "@S3_LABEL@": "#c2410c",
        "@S1_BORDER@": "#6366f1",
        "@S2_BORDER@": "#0d9488",
        "@S3_BORDER@": "#ea580c",
        "@FOOTER_CLOSE_BG@": "#dc2626",
        "@FOOTER_CLOSE_HOVER@": "#b91c1c",
        "@FOOTER_CLOSE_BORDER@": "#b91c1c",
    },
    "dark": {
        "@BG_WINDOW@": "#0c1220",
        "@BG_PANEL@": "#141e34",
        "@BG_PANEL_ALT@": "#0f1729",
        "@BG_INPUT@": "#0f1729",
        "@BG_BUTTON@": "#1e2d4a",
        "@BG_HOVER@": "#1e3a5f",
        "@FG_TEXT@": "#e2e8f0",
        "@FG_TITLE@": "#f8fafc",
        "@FG_MUTED@": "#94a3b8",
        "@FG_ACCENT@": "#93c5fd",
        "@BORDER@": "#4a5f8c",
        "@BORDER_FOCUS@": "#60a5fa",
        "@COMBO_BORDER@": "#3b82f6",
        "@ACCENT@": "#2563eb",
        "@ACCENT_HOVER@": "#1d4ed8",
        "@SEP@": "rgba(255, 255, 255, 0.08)",
        "@SECTION1_BG@": "#1a1d32",
        "@SECTION2_BG@": "#172224",
        "@SECTION3_BG@": "#241c16",
        "@S1_LABEL@": "#c7d2fe",
        "@S2_LABEL@": "#99f6e4",
        "@S3_LABEL@": "#fdba74",
        "@S1_BORDER@": "#818cf8",
        "@S2_BORDER@": "#2dd4bf",
        "@S3_BORDER@": "#fb923c",
        "@FOOTER_CLOSE_BG@": "#dc2626",
        "@FOOTER_CLOSE_HOVER@": "#b91c1c",
        "@FOOTER_CLOSE_BORDER@": "#991b1b",
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

    for section_key, filename in (
        ("@CHECK_S1@", "check-section1.png"),
        ("@CHECK_S2@", "check-section2.png"),
        ("@CHECK_S3@", "check-section3.png"),
    ):
        icon = _icon_path(filename)
        if icon.is_file():
            qss = qss.replace(section_key, icon.as_posix())

    combo_arrow = _icon_path("combo-down-light.png" if theme == "light" else "combo-down-dark.png")
    if combo_arrow.is_file():
        qss = qss.replace("@COMBO_ARROW@", combo_arrow.as_posix())

    app.setStyleSheet(qss)
