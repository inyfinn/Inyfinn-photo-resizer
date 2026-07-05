"""Theme loader — design tokens + ikony checkbox."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication


def theme_path(name: str) -> Path:
    return Path(__file__).resolve().parent / f"{name}.qss"


def _icon_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "icons" / name


def apply_theme(app: QApplication, theme: str = "light") -> None:
    path = theme_path(theme)
    if not path.is_file():
        return
    qss = path.read_text(encoding="utf-8")
    check = _icon_path("check-light.png" if theme == "light" else "check-dark.png")
    if not check.is_file():
        try:
            from inyfinn_resizer.app.themes.icons.generate_check_icons import main as gen

            gen()
        except Exception:
            pass
    if check.is_file():
        qss = qss.replace("@CHECK_ICON@", check.as_posix())
    app.setStyleSheet(qss)
