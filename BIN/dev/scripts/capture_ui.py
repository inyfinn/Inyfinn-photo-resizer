"""Zrzuty ekranu UI do weryfikacji."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QWidget

from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.main_window import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MainWindow,
)
from inyfinn_resizer.app.themes import apply_theme
from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.ensurePolished()
    widget.update()
    for child in widget.findChildren(QWidget):
        style.unpolish(child)
        style.polish(child)
        child.ensurePolished()
        child.update()


def _sync_window_theme(widget: QWidget, theme: str) -> None:
    """MainWindow po konstrukcji przywraca motyw z sesji — ustawiamy bez zapisu."""
    if not isinstance(widget, MainWindow):
        return
    widget._theme = theme
    toggle = getattr(widget, "_theme_toggle", None)
    if toggle is not None:
        toggle.blockSignals(True)
        toggle.set_dark(theme == "dark")
        toggle.blockSignals(False)
    refresh = getattr(widget, "_refresh_step_icons", None)
    if callable(refresh):
        refresh()


def _set_output_format(widget: QWidget, fmt: str) -> None:
    combo = getattr(widget, "format_combo", None)
    setter = getattr(combo, "set_selected", None) if combo is not None else None
    if not callable(setter):
        raise RuntimeError(
            "Brak publicznego format_combo.set_selected — nie ustawiono "
            f"formatu {fmt!r} bez znajomości wnętrza panelu ustawień."
        )
    setter([fmt])


def _discard_widget(widget: QWidget) -> None:
    """hide + deleteLater — closeEvent woła persist_all i zapisałby sesję/motyw."""
    widget.hide()
    widget.deleteLater()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out = root / "ui-complete" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    iteration = sys.argv[1] if len(sys.argv) > 1 else "final"

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 9))

    # kind, theme, filename_kind, format_key (pusty = bez zmiany)
    queue: list[tuple[str, str, str, str]] = [
        ("main", "light", "main", "avif"),
        ("main", "light", "main-png", "png"),
        ("format", "light", "format", ""),
        ("advanced", "light", "advanced", ""),
        ("main", "dark", "main", "avif"),
        ("main", "dark", "main-png", "png"),
        ("format", "dark", "format", ""),
        ("advanced", "dark", "advanced", ""),
    ]

    def run_step(idx: int = 0) -> None:
        if idx >= len(queue):
            app.quit()
            return

        kind, theme, file_kind, fmt = queue[idx]

        if kind == "main":
            widget = MainWindow()
            widget.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        elif kind == "format":
            widget = FormatSettingsDialog("webp", FormatOptions())
        else:
            widget = AdvancedOptionsDialog(ResizeOptions(), TransformOptions())

        # Motyw PO konstrukcji: MainWindow.__init__ woła _apply_saved_theme()
        # i nadpisuje apply_theme ustawione wcześniej.
        apply_theme(app, theme)
        _sync_window_theme(widget, theme)
        if fmt:
            try:
                _set_output_format(widget, fmt)
            except Exception as exc:
                print(f"WARN format {fmt}: {type(exc).__name__}: {exc}", file=sys.stderr)

        _repolish(widget)
        widget.show()
        app.processEvents()

        def grab_and_continue() -> None:
            app.processEvents()
            path = out / f"{iteration}-{file_kind}-{theme}.png"
            widget.grab().save(str(path))
            print("saved", path)
            _discard_widget(widget)
            QTimer.singleShot(80, lambda: run_step(idx + 1))

        QTimer.singleShot(120, grab_and_continue)

    QTimer.singleShot(300, lambda: run_step(0))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
