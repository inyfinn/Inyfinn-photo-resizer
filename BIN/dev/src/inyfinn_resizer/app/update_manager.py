"""Orkiestracja auto-update: check, download, toast, dialog, instalacja."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.message_boxes import show_info
from inyfinn_resizer.app.dialogs.update_dialog import UpdateDialog
from inyfinn_resizer.app.user_settings import (
    load_update_auto_check,
    save_last_update_check,
    should_check_for_updates,
)
from inyfinn_resizer.app.widgets.update_toast import UpdateToast
from inyfinn_resizer.utils.app_log import log_event
from inyfinn_resizer.utils.install_layout import install_root, launcher_executable
from inyfinn_resizer.utils.update_apply import write_apply_script
from inyfinn_resizer.utils.update_cache import (
    cleanup_orphans,
    find_cached,
    package_dir,
)
from inyfinn_resizer.utils.update_release import ReleaseInfo
from inyfinn_resizer.utils.update_success import consume_pending_success, mark_pending_success
from inyfinn_resizer.utils.version_compare import is_newer
from inyfinn_resizer.workers.update_worker import UpdateThread, UpdateWorker


class UpdateManager(QObject):
    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self._host = window.centralWidget() or window
        self._toast = UpdateToast(self._host)
        self._toast.install_requested.connect(self._on_install)
        self._toast.dismiss_requested.connect(self._toast.hide_toast)

        self._dialog: UpdateDialog | None = None
        self._manual_flow = False
        self._install_after_download = False

        self._pending_release: ReleaseInfo | None = None
        self._ready_zip: Path | None = None
        self._ready_version: str | None = None

        self._check_thread: UpdateThread | None = None
        self._check_worker: UpdateWorker | None = None
        self._download_thread: QThread | None = None
        self._download_worker: UpdateWorker | None = None

        self._check_scheduled = False
        cleanup_orphans()

    @staticmethod
    def is_supported() -> bool:
        return getattr(sys, "frozen", False) and install_root() is not None

    def attach(self) -> None:
        if not self.is_supported():
            return
        QTimer.singleShot(800, self._show_post_update_notice)
        if not load_update_auto_check():
            return
        if self._check_scheduled:
            return
        self._check_scheduled = True
        QTimer.singleShot(2500, lambda: self.check_now(force=False))

    def _show_post_update_notice(self) -> None:
        version = consume_pending_success(__version__)
        if not version:
            return
        show_info(
            self._window,
            "Aktualizacja",
            f"Udało się zaktualizować do wersji {version}.",
        )
        log_event("Aktualizacja", f"potwierdzono v{version} po restarcie")

    def open_manual_dialog(self) -> None:
        if not self.is_supported():
            show_info(
                self._window,
                "Aktualizacje",
                "Automatyczne aktualizacje działają w wersji EXE (portable).\n"
                "Uruchom zbudowaną aplikację InyfinnPhotoResizer.exe.",
            )
            return

        self._manual_flow = True
        if self._dialog is None:
            self._dialog = UpdateDialog(self._window)
            self._dialog.install_requested.connect(self._on_manual_install_clicked)
            self._dialog.destroyed.connect(self._on_dialog_closed)
        self._dialog.set_checking()
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()

        cached = self._find_any_ready_newer()
        if cached:
            self._ready_version, zip_str = cached
            self._ready_zip = Path(zip_str)
            self._dialog.set_update_available(self._ready_version, cached=True)
            return

        save_last_update_check(time.time())
        self._start_check_thread()

    def _on_dialog_closed(self) -> None:
        self._dialog = None
        self._manual_flow = False
        self._install_after_download = False

    def check_now(self, *, force: bool = False) -> None:
        if not self.is_supported():
            return
        if not force and not should_check_for_updates():
            cached = self._find_any_ready_newer()
            if cached:
                self._show_ready(cached[0], Path(cached[1]))
            return
        if self._check_thread and self._check_thread.isRunning():
            return
        save_last_update_check(time.time())
        self._start_check_thread()

    def _find_any_ready_newer(self) -> tuple[str, str] | None:
        from inyfinn_resizer.utils.update_cache import list_packages

        for pkg in sorted(list_packages(), key=lambda p: p.downloaded_at, reverse=True):
            if not is_newer(pkg.version, __version__):
                continue
            return pkg.version, str(pkg.path)
        return None

    def _start_check_thread(self) -> None:
        self._check_worker = UpdateWorker()
        self._check_thread = UpdateThread(self._check_worker)
        self._check_worker.checked.connect(self._on_release_checked)
        self._check_worker.failed.connect(self._on_check_failed)
        self._check_thread.finished.connect(self._cleanup_check_thread)
        self._check_worker.moveToThread(self._check_thread)
        self._check_thread.started.connect(self._check_worker.check_release)
        self._check_thread.start()

    def _cleanup_check_thread(self) -> None:
        if self._check_thread:
            self._check_thread.deleteLater()
            self._check_thread = None
        if self._check_worker:
            self._check_worker.deleteLater()
            self._check_worker = None

    def _on_check_failed(self, message: str) -> None:
        log_event("Aktualizacja", f"sprawdzenie nieudane: {message}")
        if self._dialog and self._manual_flow:
            self._dialog.set_check_failed(message)

    def _on_release_checked(self, release: ReleaseInfo) -> None:
        if not isinstance(release, ReleaseInfo):
            return

        if not is_newer(release.version, __version__):
            if self._dialog and self._manual_flow:
                self._dialog.set_up_to_date()
            return

        self._pending_release = release
        cached = find_cached(release.version, release.size or None)
        if cached is not None:
            self._ready_version = release.version
            self._ready_zip = cached.path
            if self._dialog and self._manual_flow:
                self._dialog.set_update_available(release.version, cached=True)
            else:
                self._show_ready(release.version, cached.path)
            if self._install_after_download:
                self._install_after_download = False
                self._on_install()
            return

        if self._dialog and self._manual_flow:
            self._dialog.set_update_available(release.version, cached=False)
            if self._install_after_download:
                self._start_download(release)
            return

        self._toast.set_downloading(0, release.size or 0)
        self._toast.show()
        self._toast.reposition(self._host)
        self._start_download(release)

    def _on_manual_install_clicked(self) -> None:
        if self._ready_zip and self._ready_version:
            self._on_install()
            return
        if self._pending_release:
            self._install_after_download = True
            self._start_download(self._pending_release)
            return
        if self._check_thread and self._check_thread.isRunning():
            self._install_after_download = True
            return
        save_last_update_check(time.time())
        self._install_after_download = True
        self._start_check_thread()

    def _start_download(self, release: ReleaseInfo) -> None:
        if self._download_thread and self._download_thread.isRunning():
            return
        self._download_worker = UpdateWorker()
        self._download_thread = QThread()
        self._download_worker.moveToThread(self._download_thread)
        self._download_worker.download_progress.connect(self._on_download_progress)
        self._download_worker.download_ready.connect(self._on_download_ready)
        self._download_worker.failed.connect(self._on_download_failed)
        self._download_thread.started.connect(
            lambda: self._download_worker.download_release(release)
        )
        self._download_thread.finished.connect(self._cleanup_download_thread)
        self._download_thread.start()

    def _on_download_progress(self, received: int, total: int) -> None:
        self._toast.set_downloading(received, total)
        if self._dialog and self._manual_flow:
            self._dialog.set_downloading(received, total)

    def _cleanup_download_thread(self) -> None:
        if self._download_thread:
            self._download_thread.deleteLater()
            self._download_thread = None
        if self._download_worker:
            self._download_worker.deleteLater()
            self._download_worker = None

    def _on_download_ready(self, version: str, zip_path: str) -> None:
        self._ready_version = version
        self._ready_zip = Path(zip_path)
        log_event("Aktualizacja", f"pobrano v{version}")

        if self._dialog and self._manual_flow:
            self._dialog.set_ready_to_install(version)

        if self._install_after_download:
            self._install_after_download = False
            self._on_install()
            return

        if not (self._dialog and self._manual_flow):
            self._toast.set_ready(version)
            self._toast.show()
            self._toast.reposition(self._host)

    def _on_download_failed(self, message: str) -> None:
        log_event("Aktualizacja", f"pobieranie nieudane: {message}")
        self._install_after_download = False
        self._toast.hide()
        if self._dialog and self._manual_flow:
            self._dialog.set_download_failed(message)

    def _show_ready(self, version: str, zip_path: Path) -> None:
        self._ready_version = version
        self._ready_zip = zip_path
        self._toast.set_ready(version)
        self._toast.show()
        self._toast.reposition(self._host)

    def _on_install(self) -> None:
        if not self._ready_zip or not self._ready_version:
            return
        root = install_root()
        launcher = launcher_executable()
        if root is None or launcher is None or not self._ready_zip.is_file():
            return

        pkg_dir = package_dir(self._ready_version)
        script = write_apply_script(
            zip_path=self._ready_zip,
            install_root=root,
            version=self._ready_version,
            launcher=launcher,
            package_dir=pkg_dir,
        )
        mark_pending_success(self._ready_version)
        log_event("Aktualizacja", f"instalacja v{self._ready_version}")

        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            creationflags=flags,
            close_fds=True,
        )
        QApplication.instance().quit()

    def reposition_toast(self) -> None:
        self._toast.reposition(self._host)
