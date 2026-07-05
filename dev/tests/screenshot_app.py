"""Capture Qt window screenshots for Ralph visual loop."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.main_window import MainWindow
from inyfinn_resizer.app.themes import apply_theme


def main() -> int:
    widths = [375, 768, 1024]
    theme = sys.argv[1] if len(sys.argv) > 1 else "light"
    loop = sys.argv[2] if len(sys.argv) > 2 else "1"

    out_dir = Path(__file__).resolve().parents[1] / "ui-complete" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    apply_theme(app, theme)
    win = MainWindow()
    win.show()

    def shot(idx: int = 0) -> None:
        if idx >= len(widths):
            QTimer.singleShot(100, app.quit)
            return
        w = widths[idx]
        win.resize(w, 700)
        QTimer.singleShot(300, lambda: _grab(win, out_dir, loop, w, theme, idx))

    def _grab(window, directory, loop_id, width, th, index):
        screen = app.primaryScreen()
        pix = screen.grabWindow(window.winId())
        path = directory / f"loop-{loop_id}-{width}-{th}.png"
        pix.save(str(path))
        print(f"Saved {path}")
        shot(index + 1)

    QTimer.singleShot(500, lambda: shot(0))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
