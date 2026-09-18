"""Regresja: obiekt QThread nie może zniknąć, zanim wątek naprawdę się zakończy.

Qt woła wtedy qFatal i EXE ginie bez komunikatu (fast-fail 7 — awarie auto-update 2026-09-18).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.update_manager import UpdateManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class _SlowThread(QThread):
    """Emituje finished() i pracuje jeszcze chwilę — jak QThread tuż przed końcem."""

    def __init__(self) -> None:
        super().__init__()
        self.stop_at = 0.0

    def run(self) -> None:
        time.sleep(0.2)


def test_retire_thread_waits_before_delete(qapp) -> None:
    manager = UpdateManager.__new__(UpdateManager)
    manager._retired_threads = []

    thread = _SlowThread()
    thread.start()
    assert thread.isRunning()

    UpdateManager._retire_thread(manager, thread, None)

    assert not thread.isRunning(), "wątek musi być zakończony, zanim zwolnimy obiekt"
    assert manager._retired_threads == [], "zakończony wątek nie zostaje na liście"


def test_retire_thread_keeps_reference_when_wait_times_out(qapp, monkeypatch) -> None:
    manager = UpdateManager.__new__(UpdateManager)
    manager._retired_threads = []

    thread = _SlowThread()
    thread.start()
    monkeypatch.setattr(thread, "wait", lambda _ms=0: False)

    UpdateManager._retire_thread(manager, thread, None)

    assert manager._retired_threads == [thread], "wątek bez potwierdzenia końca zostaje w referencjach"
    thread.wait(5000)


def test_retire_thread_accepts_none(qapp) -> None:
    manager = UpdateManager.__new__(UpdateManager)
    manager._retired_threads = []
    UpdateManager._retire_thread(manager, None, None)
    assert manager._retired_threads == []
