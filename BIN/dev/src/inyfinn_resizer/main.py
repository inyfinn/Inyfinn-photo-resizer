"""Application entry point."""

from __future__ import annotations

import sys
import time

# Początek startu — od tej chwili liczy się czas pokazywany na ekranie startowym.
_T0 = time.perf_counter()

from inyfinn_resizer.utils.frozen_stdio import ensure_stdio  # noqa: E402

ensure_stdio()

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QFont, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

_IMPORT_POLL_MS = 30


def _app_icon() -> QIcon | None:
    from pathlib import Path

    from inyfinn_resizer.utils.paths import bootstrap_runtime_paths, bundle_dir, project_root

    bootstrap_runtime_paths()
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
    for base in (project_root(), bundle_dir()):
        if base is not None:
            candidates.append(base)
    seen: set[Path] = set()
    for base in candidates:
        if base in seen:
            continue
        seen.add(base)
        for name in ("InyfinnPhotoResizer.ico", "icon.ico"):
            path = base / name
            if path.is_file():
                return QIcon(str(path))
    assets = Path(__file__).resolve().parents[2].parent / "assets" / "icon.ico"
    if assets.is_file():
        return QIcon(str(assets))
    return None


def _configure_pillow() -> None:
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = 300_000_000


def _boot_application(app: QApplication, splash, icon: QIcon | None) -> None:
    """Ciężkie importy (okno główne, biblioteki obrazów) w wątku w tle, żeby ekran startowy żył.

    Na poziomie modułów nie powstają obiekty Qt, więc import poza wątkiem GUI jest bezpieczny;
    samo okno tworzy już wątek główny (``_boot_application_impl``).
    """
    import threading

    from inyfinn_resizer.utils.paths import bootstrap_runtime_paths

    state: dict[str, BaseException] = {}

    def _import_heavy() -> None:
        try:
            import inyfinn_resizer.app.main_window  # noqa: F401
        except BaseException as exc:  # przekazane do wątku głównego
            state["error"] = exc
            return
        try:
            # Lista czcionek systemu (na stacjach graficznych tysiące rodzin) — wczytana tu, a nie
            # w trakcie budowy okna w wątku GUI. QFontDatabase w Qt 6 jest bezpieczny wątkowo.
            from PySide6.QtGui import QFontDatabase

            QFontDatabase.families()
        except Exception:
            pass

    try:
        bootstrap_runtime_paths()
    except Exception as exc:
        _boot_failed(app, splash, exc)
        return
    worker = threading.Thread(target=_import_heavy, name="inyfinn-import", daemon=True)
    worker.start()
    poll = QTimer(app)
    poll.setInterval(_IMPORT_POLL_MS)

    def _check() -> None:
        if worker.is_alive():
            return
        poll.stop()
        try:
            if "error" in state:
                raise state["error"]
            _boot_application_impl(app, splash, icon)
        except Exception as exc:
            _boot_failed(app, splash, exc)

    poll.timeout.connect(_check)
    poll.start()


def _boot_failed(app: QApplication, splash, exc: BaseException) -> None:
    import traceback

    from inyfinn_resizer.app.dialogs.message_boxes import show_critical
    from inyfinn_resizer.utils.app_log import log_event

    try:
        splash.close()
    except Exception:
        pass
    log_event("Błąd uruchomienia", str(exc), status="ERR")
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    show_critical(
        None,
        "Inyfinn Photo Resizer",
        f"Nie udało się uruchomić aplikacji.\n\n{exc}\n\n{details}",
    )
    app.quit()


def _boot_application_impl(app: QApplication, splash, icon: QIcon | None) -> None:
    from inyfinn_resizer import __version__
    from inyfinn_resizer.app.themes import apply_theme
    from inyfinn_resizer.app.user_settings import load_theme
    from inyfinn_resizer.utils.app_log import log_event
    from inyfinn_resizer.utils.paths import bootstrap_runtime_paths

    bootstrap_runtime_paths()
    splash.set_status("Ładowanie modułów…")
    app.processEvents()

    from inyfinn_resizer.app.main_window import MainWindow

    log_event("Uruchomienie aplikacji", f"v{__version__}")
    splash.set_status("Ładowanie motywu…")
    app.processEvents()
    theme = load_theme()
    apply_theme(app, theme)
    # Design Dobra Kaloria (jak program „Stwórz prezentację”): styl kolorów × tryb, Lato + Mindset.
    from inyfinn_resizer.app.themes import display_font_family

    log_event("Motyw", f"{theme} · czcionka {app.font().family()} · nagłówki {display_font_family()}")

    splash.set_status("Ładowanie okna…")
    app.processEvents()
    _configure_pillow()

    window = MainWindow()
    if icon is not None:
        window.setWindowIcon(icon)

    def _on_shown() -> None:
        from inyfinn_resizer.app.widgets.startup_splash import save_startup_seconds

        seconds = time.perf_counter() - _T0
        save_startup_seconds(seconds)
        log_event("Start programu", f"{seconds:.1f} s")

    # Plansza: 100% przez chwilę, potem znika i pojawia się okno (plansza nigdy nie zostaje nad oknem).
    splash.finish(window, _on_shown)


def main() -> int:
    from inyfinn_resizer.utils.app_mutex import (
        acquire_app_mutex,
        activate_existing_instance,
        release_app_mutex,
    )

    if not acquire_app_mutex():
        if activate_existing_instance():
            return 0
        from inyfinn_resizer.app.dialogs.message_boxes import show_warning

        warn_app = QApplication(sys.argv)
        show_warning(
            None,
            "Inyfinn Photo Resizer",
            "Główna aplikacja jest już uruchomiona.\n\n"
            "To nie jest pngquant — narzędzia kompresji działają w tle jako osobne procesy "
            "tylko podczas konwersji.\n\n"
            "Zamknij poprzednie okno Inyfinn Photo Resizer lub sprawdź pasek zadań.",
        )
        del warn_app
        return 1

    from inyfinn_resizer import __version__
    from inyfinn_resizer.app.widgets.startup_splash import StartupSplash

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(release_app_mutex)
    app.setFont(QFont("Segoe UI", 9))
    app.setApplicationName("Inyfinn Photo Resizer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Inyfinn")

    splash = StartupSplash(t0=_T0)
    splash.center_on_screen()
    splash.show()
    app.processEvents()

    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
        splash.setWindowIcon(icon)

    QTimer.singleShot(0, lambda: _boot_application(app, splash, icon))
    return app.exec()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    sys.exit(main())
