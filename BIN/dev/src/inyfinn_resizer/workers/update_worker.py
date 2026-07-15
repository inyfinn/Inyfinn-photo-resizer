"""Worker sprawdzania i pobierania aktualizacji (QThread)."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from inyfinn_resizer.utils.update_cache import (
    find_cached,
    part_path_for,
    register_download,
    zip_path_for,
)
from inyfinn_resizer.utils.update_config import DOWNLOAD_CHUNK_BYTES, USER_AGENT
from inyfinn_resizer.utils.update_release import ReleaseInfo, fetch_latest_release


class UpdateWorker(QObject):
    checked = Signal(object)  # ReleaseInfo | None
    download_progress = Signal(int, int)  # received, total
    download_ready = Signal(str, str)  # version, zip_path
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = False

    def request_cancel(self) -> None:
        self._cancelled = True

    def check_release(self) -> None:
        try:
            release = fetch_latest_release()
            self.checked.emit(release)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 — worker boundary
            self.failed.emit(str(exc))

    def download_release(self, release: ReleaseInfo) -> None:
        try:
            cached = find_cached(release.version, release.size or None)
            if cached is not None:
                self.download_ready.emit(release.version, str(cached.path))
                return

            folder = zip_path_for(release.version).parent
            folder.mkdir(parents=True, exist_ok=True)
            final_path = zip_path_for(release.version)
            part_path = part_path_for(release.version)

            existing = part_path.stat().st_size if part_path.is_file() else 0
            headers = {"User-Agent": USER_AGENT}
            if existing > 0:
                headers["Range"] = f"bytes={existing}-"

            req = urllib.request.Request(release.download_url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                code = getattr(resp, "status", 200) or 200
                total_header = resp.headers.get("Content-Length")
                total = int(total_header) if total_header else release.size
                if code == 206:
                    content_range = resp.headers.get("Content-Range", "")
                    if "/" in content_range:
                        total = int(content_range.rsplit("/", 1)[-1])
                elif existing > 0 and code == 200:
                    existing = 0
                    part_path.unlink(missing_ok=True)

                mode = "ab" if existing > 0 else "wb"
                received = existing
                with part_path.open(mode) as handle:
                    while not self._cancelled:
                        chunk = resp.read(DOWNLOAD_CHUNK_BYTES)
                        if not chunk:
                            break
                        handle.write(chunk)
                        received += len(chunk)
                        self.download_progress.emit(received, total or received)

            if self._cancelled:
                return

            if not part_path.is_file():
                raise ValueError("Pobieranie przerwane — brak pliku")

            actual_size = part_path.stat().st_size
            if release.size and actual_size != release.size:
                part_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Niepełny pakiet ({actual_size} B, oczekiwano {release.size} B)"
                )

            part_path.replace(final_path)
            register_download(release.version, final_path, actual_size)
            self.download_ready.emit(release.version, str(final_path))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class UpdateThread(QThread):
    def __init__(self, worker: UpdateWorker) -> None:
        super().__init__()
        self.worker = worker

    def run(self) -> None:
        self.worker.check_release()
