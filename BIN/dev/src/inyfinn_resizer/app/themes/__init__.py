"""Theme loader — wspólna struktura + zamiana kolorów."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

_SECTION_TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "@S1_GROUP_BG@": "rgba(99, 102, 241, 0.07)",
        "@S1_GROUP_BORDER@": "#c7d2fe",
        "@S1_CTRL_BORDER@": "#a5b4fc",
        "@S1_DROPDOWN_BG@": "#eef2ff",
        "@S1_HOVER_BG@": "#eef2ff",
        "@S1_HOVER_BORDER@": "#6366f1",
        "@S1_FOCUS_BORDER@": "#4f46e5",
        "@S1_SLIDER_GROOVE@": "#c7d2fe",
        "@S1_SLIDER_HANDLE@": "#6366f1",
        "@S1_SLIDER_FILL@": "#818cf8",
        "@S1_CHECK_BORDER@": "#818cf8",
        "@S1_CHECK_BG@": "#6366f1",
        "@S1_CHECK_BORDER_ON@": "#4f46e5",
        "@S1_VALUE@": "#4f46e5",
        "@S1_BTN_TEXT@": "#4338ca",
        "@S1_SELECT_BG@": "#6366f1",
        "@S2_DROPDOWN_BG@": "#ecfdf5",
        "@S2_HOVER_BG@": "#ecfdf5",
        "@S2_HOVER_BORDER@": "#0d9488",
        "@S2_FOCUS_BORDER@": "#0f766e",
        "@S2_CTRL_BORDER@": "#5eead4",
        "@S2_SLIDER_GROOVE@": "#99f6e4",
        "@S2_SLIDER_HANDLE@": "#0d9488",
        "@S2_SLIDER_FILL@": "#2dd4bf",
        "@S2_CHECK_BORDER@": "#2dd4bf",
        "@S2_CHECK_BG@": "#0d9488",
        "@S2_CHECK_BORDER_ON@": "#0f766e",
        "@S2_VALUE@": "#0f766e",
        "@S2_SELECT_BG@": "#0d9488",
        "@S2_TOOL_HOVER@": "#0d9488",
        "@S3_INPUT_BORDER@": "#fdba74",
        "@S3_INPUT_HOVER_BG@": "#ffedd5",
        "@S3_INPUT_HOVER_BORDER@": "#ea580c",
        "@S3_CHECK_BORDER@": "#fb923c",
        "@S3_CHECK_BG@": "#ea580c",
        "@S3_CHECK_BORDER_ON@": "#c2410c",
        "@S3_BTN_PRIMARY@": "#ea580c",
        "@S3_BTN_PRIMARY_HOVER@": "#c2410c",
        "@S3_BTN_PRIMARY_BORDER@": "#c2410c",
        "@S3_BTN_BROWSE_BORDER@": "#ea580c",
        "@S3_BTN_BROWSE_TEXT@": "#c2410c",
        "@S3_BTN_BROWSE_HOVER_BG@": "#ffedd5",
        "@S3_BTN_BROWSE_HOVER_BORDER@": "#c2410c",
        "@S3_BTN_BROWSE_HOVER_TEXT@": "#9a3412",
        "@OVERLAY_SCRIM@": "rgba(15, 23, 42, 0.42)",
        "@OVERLAY_ABORT_COLOR@": "#ef4444",
        "@OVERLAY_ABORT_BORDER@": "#fecaca",
        "@OVERLAY_ABORT_HOVER_BG@": "#fef2f2",
        "@OVERLAY_ABORT_PRESSED@": "#fee2e2",
        "@OVERLAY_HINT@": "#64748b",
    },
    "dark": {
        "@S1_GROUP_BG@": "rgba(129, 140, 248, 0.14)",
        "@S1_GROUP_BORDER@": "#4a5080",
        "@S1_CTRL_BORDER@": "#5c6194",
        "@S1_DROPDOWN_BG@": "#1c2038",
        "@S1_HOVER_BG@": "#252945",
        "@S1_HOVER_BORDER@": "#818cf8",
        "@S1_FOCUS_BORDER@": "#a5b4fc",
        "@S1_SLIDER_GROOVE@": "#3d4268",
        "@S1_SLIDER_HANDLE@": "#818cf8",
        "@S1_SLIDER_FILL@": "#6366f1",
        "@S1_CHECK_BORDER@": "#6366f1",
        "@S1_CHECK_BG@": "#6366f1",
        "@S1_CHECK_BORDER_ON@": "#818cf8",
        "@S1_VALUE@": "#c7d2fe",
        "@S1_BTN_TEXT@": "#c7d2fe",
        "@S1_SELECT_BG@": "#6366f1",
        "@S2_DROPDOWN_BG@": "#1a2830",
        "@S2_HOVER_BG@": "#1e3338",
        "@S2_HOVER_BORDER@": "#2dd4bf",
        "@S2_FOCUS_BORDER@": "#5eead4",
        "@S2_CTRL_BORDER@": "#3d6b66",
        "@S2_SLIDER_GROOVE@": "#2a4548",
        "@S2_SLIDER_HANDLE@": "#2dd4bf",
        "@S2_SLIDER_FILL@": "#14b8a6",
        "@S2_CHECK_BORDER@": "#2dd4bf",
        "@S2_CHECK_BG@": "#0d9488",
        "@S2_CHECK_BORDER_ON@": "#14b8a6",
        "@S2_VALUE@": "#99f6e4",
        "@S2_SELECT_BG@": "#0d9488",
        "@S2_TOOL_HOVER@": "#0d9488",
        "@S3_INPUT_BORDER@": "#4a5568",
        "@S3_INPUT_HOVER_BG@": "#1a2030",
        "@S3_INPUT_HOVER_BORDER@": "#64748b",
        "@S3_CHECK_BORDER@": "#64748b",
        "@S3_CHECK_BG@": "#64748b",
        "@S3_CHECK_BORDER_ON@": "#94a3b8",
        "@S3_BTN_PRIMARY@": "#475569",
        "@S3_BTN_PRIMARY_HOVER@": "#64748b",
        "@S3_BTN_PRIMARY_BORDER@": "#334155",
        "@S3_BTN_BROWSE_BORDER@": "#64748b",
        "@S3_BTN_BROWSE_TEXT@": "#cbd5e1",
        "@S3_BTN_BROWSE_HOVER_BG@": "#1a2030",
        "@S3_BTN_BROWSE_HOVER_BORDER@": "#94a3b8",
        "@S3_BTN_BROWSE_HOVER_TEXT@": "#e2e8f0",
        "@OVERLAY_SCRIM@": "rgba(0, 0, 0, 0.58)",
        "@OVERLAY_ABORT_COLOR@": "#f87171",
        "@OVERLAY_ABORT_BORDER@": "#7f1d1d",
        "@OVERLAY_ABORT_HOVER_BG@": "#3f1515",
        "@OVERLAY_ABORT_PRESSED@": "#551818",
        "@OVERLAY_HINT@": "#94a3b8",
    },
}

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
        "@UPDATE_TOAST_BG@": "#ffffff",
        "@UPDATE_TOAST_BORDER@": "#6366f1",
        "@UPDATE_TOAST_TITLE@": "#0f172a",
        "@UPDATE_TOAST_TEXT@": "#475569",
        "@UPDATE_TOAST_PROGRESS@": "#64748b",
        "@UPDATE_TOAST_INSTALL_BG@": "#6366f1",
        "@UPDATE_TOAST_INSTALL_HOVER@": "#4f46e5",
        "@UPDATE_TOAST_INSTALL_TEXT@": "#ffffff",
        "@UPDATE_TOAST_LATER_BG@": "#f1f5f9",
        "@UPDATE_TOAST_LATER_HOVER@": "#e2e8f0",
        "@UPDATE_TOAST_LATER_TEXT@": "#334155",
        "@UPDATE_TOAST_LATER_BORDER@": "#cbd5e1",
        **_SECTION_TOKENS["light"],
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
        "@SECTION3_BG@": "#181b24",
        "@S1_LABEL@": "#c7d2fe",
        "@S2_LABEL@": "#99f6e4",
        "@S3_LABEL@": "#b8c2d4",
        "@S1_BORDER@": "#818cf8",
        "@S2_BORDER@": "#2dd4bf",
        "@S3_BORDER@": "#64748b",
        "@FOOTER_CLOSE_BG@": "#dc2626",
        "@FOOTER_CLOSE_HOVER@": "#b91c1c",
        "@FOOTER_CLOSE_BORDER@": "#991b1b",
        "@UPDATE_TOAST_BG@": "#1a2238",
        "@UPDATE_TOAST_BORDER@": "#818cf8",
        "@UPDATE_TOAST_TITLE@": "#f8fafc",
        "@UPDATE_TOAST_TEXT@": "#cbd5e1",
        "@UPDATE_TOAST_PROGRESS@": "#94a3b8",
        "@UPDATE_TOAST_INSTALL_BG@": "#6366f1",
        "@UPDATE_TOAST_INSTALL_HOVER@": "#818cf8",
        "@UPDATE_TOAST_INSTALL_TEXT@": "#ffffff",
        "@UPDATE_TOAST_LATER_BG@": "#1e2d4a",
        "@UPDATE_TOAST_LATER_HOVER@": "#253656",
        "@UPDATE_TOAST_LATER_TEXT@": "#e2e8f0",
        "@UPDATE_TOAST_LATER_BORDER@": "#4a5f8c",
        **_SECTION_TOKENS["dark"],
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
