"""Zrzuty ekranu UI do weryfikacji."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.main_window import MainWindow
from inyfinn_resizer.app.themes import apply_theme
from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out = root / "ui-complete" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    iteration = sys.argv[1] if len(sys.argv) > 1 else "final"

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 9))

    queue: list[tuple[str, str, str]] = [
        ("main", "light", ""),
        ("format", "light", "webp"),
        ("advanced", "light", ""),
        ("main", "dark", ""),
        ("format", "dark", "webp"),
        ("advanced", "dark", ""),
    ]

    def run_step(idx: int = 0) -> None:
        if idx >= len(queue):
            app.quit()
            return

        kind, theme, _ = queue[idx]
        apply_theme(app, theme)

        if kind == "main":
            widget = MainWindow()
        elif kind == "format":
            widget = FormatSettingsDialog("webp", FormatOptions())
        else:
            widget = AdvancedOptionsDialog(ResizeOptions(), TransformOptions())

        widget.show()
        app.processEvents()

        path = out / f"{iteration}-{kind}-{theme}.png"
        widget.grab().save(str(path))
        print("saved", path)
        widget.close()
        QTimer.singleShot(80, lambda: run_step(idx + 1))

    QTimer.singleShot(300, lambda: run_step(0))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
