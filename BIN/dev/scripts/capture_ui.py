"""Zrzuty ekranu UI do weryfikacji (tylko własne okna programu: ``widget.grab()``, nigdy cały ekran).

    capture_ui.py [iteracja] [folder_wyjściowy] [motyw,motyw,...] [zestaw]

Zestawy (4. argument):
- ``stare`` (domyślny): główne okno, tryb prosty, Ustawienia, Opcje zaawansowane, okno konwersji;
- ``v267``: wygląd 2.6.7 — tryb prosty (pusty, z 3 plikami, wąski 960 px), tryb zaawansowany (rozwinięty, dwie karty
  zwinięte, wąski 960 px), Ustawienia (góra i przewinięte), Opcje zaawansowane;
- ``v268``: wygląd 2.6.8 — białe pole na pliki, zdanie o zapisie, ustawienia GIF, pytanie o zajęte nazwy.

Motyw: pełne id (``dobra-kaloria-zielen-ciemny``) albo skrót (``zielen-ciemny``, ``krem-jasny``, ``zielen-jasny``, ``krem-ciemny``).
Nieznana nazwa kończy program błędem (wcześniej cicho dawała jasny domyślny, więc „ciemne” zrzuty wychodziły jasne).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget

from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.main_window import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MainWindow,
)
from inyfinn_resizer.app.themes import THEMES, apply_theme, is_dark_theme
from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions


def _theme_id(name: str) -> str:
    """Skrót ``zielen-ciemny`` → pełne id motywu. Nieznana nazwa NIE jest cicho zamieniana na jasny domyślny
    (przez to zrzuty „ciemne” wychodziły jasne): kończy program błędem."""
    full = name if name in THEMES else f"dobra-kaloria-{name}"
    if full not in THEMES:
        raise SystemExit(f"Nieznany motyw {name!r}; dostępne: {', '.join(THEMES)}")
    return full


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
        toggle.set_dark(is_dark_theme(theme))
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


def _isolate_settings() -> None:
    """Kopia ustawień użytkownika w pliku tymczasowym — zrzuty nie zmieniają rejestru
    (np. migracji motywu z 2.6.0 ani sesji)."""
    from PySide6.QtCore import QSettings

    from inyfinn_resizer.app import user_settings

    path = Path(tempfile.gettempdir()) / "inyfinn-capture-settings.ini"
    src = QSettings("Inyfinn", "PhotoResizer")
    dst = QSettings(str(path), QSettings.Format.IniFormat)
    dst.clear()
    for key in src.allKeys():
        # sesja i rozmiary okna użytkownika nie wpływają na zrzuty (dopasowanie okna liczy się od zera)
        if key == "session" or key.startswith("ui/window_size") or key in ("ui/splitter", "ui/collapsed_sections"):
            continue
        dst.setValue(key, src.value(key))
    dst.sync()
    user_settings._settings = lambda: QSettings(str(path), QSettings.Format.IniFormat)


def _discard_widget(widget: QWidget) -> None:
    """hide + deleteLater — closeEvent woła persist_all i zapisałby sesję/motyw."""
    widget.hide()
    widget.deleteLater()


def _sample_files() -> list[Path]:
    """Trzy pliki do listy (jak w makietach: arbuz.png, banan.jpg, cytryna.mov) w katalogu tymczasowym."""
    from PIL import Image

    folder = Path(tempfile.gettempdir()) / "inyfinn-capture-files"
    folder.mkdir(exist_ok=True)
    out: list[Path] = []
    for name, color in (("arbuz.png", (60, 160, 90)), ("banan.jpg", (240, 210, 70))):
        path = folder / name
        if not path.exists():
            Image.new("RGB", (640, 480), color).save(path)
        out.append(path)
    film = folder / "cytryna.mov"
    if not film.exists():
        film.write_bytes(b"")
    out.append(film)
    return out


def _fill_files(widget: MainWindow) -> None:
    for path in _sample_files():
        widget._add_path_to_queue(path)
    widget._update_queue_label()
    widget._refresh_simple_file_list()


def _save_choice_dialog() -> QWidget:
    """Pytanie o zapis, gdy nazwy są zajęte (3 pliki z listy próbnej, wszystkie w jednym folderze)."""
    from inyfinn_resizer.app.dialogs import simple_save_dialog as ssd

    files = _sample_files()
    if hasattr(ssd, "SaveConflictDialog"):
        return ssd.SaveConflictDialog(None, conflicts=files[:2], total=len(files), same_as_source=True)
    return ssd.SimpleSaveChoiceDialog(None, file_count=len(files), folders=[p.parent for p in files])


def _scroll_of(dialog: QWidget) -> QScrollArea | None:
    return dialog.findChild(QScrollArea, "settingsScroll")


# (rodzaj, nazwa w pliku, opcje)
STATES_OLD: list[tuple[str, str, dict]] = [
    ("main", "main", {"format": "avif"}),
    ("main", "main-png", {"format": "png"}),
    ("simple", "simple", {}),
    ("format", "format", {}),
    ("advanced", "advanced", {}),
    ("overlay", "overlay", {"format": "png"}),
]
STATES_V267: list[tuple[str, str, dict]] = [
    ("simple", "tryb-prosty-pusty", {}),
    ("simple", "tryb-prosty-3-pliki", {"files": True}),
    ("simple", "tryb-prosty-waski-960", {"files": True, "width": 960}),
    ("main", "tryb-zaawansowany-rozwiniety", {"format": "avif", "files": True}),
    ("main", "tryb-zaawansowany-zwiniete", {"format": "avif", "files": True, "collapse": ["background", "save"]}),
    ("main", "tryb-zaawansowany-waski-960", {"format": "png", "files": True, "width": 960}),
    ("format", "ustawienia-gora", {"fmt": "jpeg"}),
    ("format", "ustawienia-przewiniete", {"fmt": "jpeg", "scroll": "end"}),
    ("advanced", "opcje-zaawansowane", {}),
]
# 2.6.8: strefa plików, informacja o zapisie, ustawienia GIF, pytanie „Nadpisz / Zapisz obok z dopiskiem”
STATES_V268: list[tuple[str, str, dict]] = [
    ("simple", "prosty-pusty", {}),
    ("simple", "prosty-3-pliki", {"files": True}),
    ("simple", "prosty-folder-zdjec", {"files": True, "simple_out": "source"}),
    ("simple", "prosty-waski-960", {"files": True, "width": 960}),
    ("main", "zaawansowany-gif", {"format": "gif", "files": True}),
    ("format", "ustawienia-gif", {"fmt": "gif"}),
    ("format", "ustawienia-gif-film", {"fmt": "gif", "scroll_extra": 460}),
    ("savechoice", "pytanie-zapis", {}),
]


def main() -> int:
    # capture_ui.py [iteracja] [folder_wyjściowy] [motyw,motyw,...] [zestaw: stare|v267]
    root = Path(__file__).resolve().parents[2]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "ui-complete" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    iteration = sys.argv[1] if len(sys.argv) > 1 else "final"
    themes = sys.argv[3].split(",") if len(sys.argv) > 3 else list(THEMES)
    sets = {"v267": STATES_V267, "v268": STATES_V268}
    states = sets.get(sys.argv[4], STATES_OLD) if len(sys.argv) > 4 else STATES_OLD

    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 9))
    _isolate_settings()

    queue = [(kind, theme, file_kind, opts) for theme in themes for kind, file_kind, opts in states]

    def run_step(idx: int = 0) -> None:
        if idx >= len(queue):
            app.quit()
            return

        kind, theme, file_kind, opts = queue[idx]
        fmt = opts.get("format", "")
        # stan zwinięcia kart jest zapamiętywany w ustawieniach — każdy zrzut zaczyna od rozwiniętych kart
        from inyfinn_resizer.app import user_settings

        user_settings.save_collapsed_sections([])

        if kind == "main":
            widget = MainWindow()
            widget.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
            widget._set_ui_mode("advanced", mark_dirty=False)
        elif kind in ("simple", "overlay"):
            widget = MainWindow()
            widget.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
            widget._set_ui_mode("simple", mark_dirty=False)
        elif kind == "format":
            widget = FormatSettingsDialog(opts.get("fmt", "webp"), FormatOptions())
        elif kind == "savechoice":
            widget = _save_choice_dialog()
        else:
            widget = AdvancedOptionsDialog(ResizeOptions(), TransformOptions())

        # Motyw PO konstrukcji: MainWindow.__init__ woła _apply_saved_theme()
        # i nadpisuje apply_theme ustawione wcześniej.
        apply_theme(app, _theme_id(theme))
        _sync_window_theme(widget, _theme_id(theme))
        if fmt:
            try:
                _set_output_format(widget, fmt)
            except Exception as exc:
                print(f"WARN format {fmt}: {type(exc).__name__}: {exc}", file=sys.stderr)
        if opts.get("files") and isinstance(widget, MainWindow):
            _fill_files(widget)
        if opts.get("simple_out") == "source" and isinstance(widget, MainWindow):
            widget._simple_output_dir = _sample_files()[0].parent
            widget._refresh_simple_output()
        for key in opts.get("collapse", []):
            widget._cards[key].set_collapsed(True)

        _repolish(widget)
        widget.show()
        app.processEvents()
        width = opts.get("width")
        if width and isinstance(widget, MainWindow):
            widget.resize(width, widget.height())
            app.processEvents()
            widget._fit_window(initial=False)
            app.processEvents()
        if kind == "overlay":
            overlay = widget._conversion_overlay
            overlay.start_batch(
                [
                    ("CIASTO-SLIWKOW.png", "png"),
                    ("KWIAT sliwki-1.png", "png"),
                    ("KWIAT sliwki-2.png", "png"),
                ]
            )
            overlay.set_file_state(
                0,
                state="Usuwanie tła…",
                percent=5,
                detail="Usuwanie tła · najlepsza jakość",
                force=True,
            )
            overlay.set_file_state(
                1,
                state="Usuwanie tła…",
                percent=5,
                detail="Usuwanie tła · najlepsza jakość",
                force=True,
            )
            overlay.set_file_state(2, state="Oczekiwanie", percent=0, detail="Oczekiwanie", force=True)
            overlay.set_overall(0, 3)
            overlay.set_eta_seconds(148)
            app.processEvents()
        if opts.get("scroll_extra"):
            scroll = _scroll_of(widget)
            section = getattr(widget, "_sections", {}).get(opts.get("fmt", ""))
            if scroll is not None and section is not None:
                app.processEvents()
                scroll.verticalScrollBar().setValue(section.y() + int(opts["scroll_extra"]))
                widget._initial_scrolled = True  # showEvent nie przewinie z powrotem do początku sekcji
                app.processEvents()
        if opts.get("scroll") == "end":
            scroll = _scroll_of(widget)
            if scroll is not None:
                bar = scroll.verticalScrollBar()
                bar.setValue(bar.maximum() // 2)
                app.processEvents()

        def grab_and_continue() -> None:
            app.processEvents()
            path = out / f"{iteration}-{file_kind}-{theme}.png"
            widget.grab().save(str(path))
            size = f"{widget.width()}x{widget.height()}"
            print("saved", path, size)
            _discard_widget(widget)
            QTimer.singleShot(80, lambda: run_step(idx + 1))

        QTimer.singleShot(160, grab_and_continue)

    QTimer.singleShot(300, lambda: run_step(0))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
