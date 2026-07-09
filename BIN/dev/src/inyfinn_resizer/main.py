"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication


def _app_icon() -> QIcon | None:
    from pathlib import Path

    from inyfinn_resizer.utils.paths import bootstrap_runtime_paths, bundle_dir, project_root

    bootstrap_runtime_paths()
    for base in (project_root(), bundle_dir()):
        if base is None:
            continue
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
    from inyfinn_resizer import __version__
    from inyfinn_resizer.app.main_window import MainWindow
    from inyfinn_resizer.app.themes import apply_theme
    from inyfinn_resizer.app.user_settings import load_theme
    from inyfinn_resizer.utils.app_log import log_event
    from inyfinn_resizer.utils.paths import bootstrap_runtime_paths

    bootstrap_runtime_paths()
    log_event("Uruchomienie aplikacji", f"v{__version__}")
    splash.set_status("Ładowanie motywu…")
    app.processEvents()
    apply_theme(app, load_theme())

    splash.set_status("Ładowanie okna…")
    app.processEvents()
    _configure_pillow()

    window = MainWindow()
    if icon is not None:
        window.setWindowIcon(icon)
    window.show()
    splash.finish(window)


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

    splash = StartupSplash()
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
