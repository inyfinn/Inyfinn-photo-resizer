"""Application entry point."""

from __future__ import annotations

import sys

from pathlib import Path

from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import QApplication
from inyfinn_resizer.app.dialogs.message_boxes import show_warning

from inyfinn_resizer import __version__
from inyfinn_resizer.app.main_window import MainWindow
from inyfinn_resizer.app.themes import apply_theme
from inyfinn_resizer.utils.app_mutex import (
    acquire_app_mutex,
    activate_existing_instance,
    release_app_mutex,
)
from inyfinn_resizer.utils.paths import bundle_dir, project_root


def _app_icon() -> QIcon | None:
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


def main() -> int:
    if not acquire_app_mutex():
        if activate_existing_instance():
            return 0
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

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(release_app_mutex)
    app.setFont(QFont("Segoe UI", 9))
    app.setApplicationName("Inyfinn Photo Resizer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Inyfinn")
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    apply_theme(app, "light")

    window = MainWindow()
    if icon is not None:
        window.setWindowIcon(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    sys.exit(main())
