"""Ekran startowy Dobra Kaloria (2.6.2): pasek, szacowany czas, zapis czasu startu, zamknięcie."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QWidget

from inyfinn_resizer.app.widgets import startup_splash as ss


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def ini(tmp_path, monkeypatch):
    path = tmp_path / "splash.ini"
    monkeypatch.setattr(ss, "_settings", lambda: QSettings(str(path), QSettings.Format.IniFormat))
    return path


def _splash(app, *, elapsed: float, expected: float) -> ss.StartupSplash:
    return ss.StartupSplash(t0=time.perf_counter() - elapsed, expected_seconds=expected)


def test_size_and_assets(app):
    s = _splash(app, elapsed=0, expected=6)
    assert (s.width(), s.height()) == (560, 330)
    assert (ss._assets_dir() / "logo_white_box.png").is_file()
    assert s._logo is not None and s._logo.width() == 190
    assert s._font_title.family() == "Mindset"


@pytest.mark.parametrize(
    "elapsed, expected, low, high",
    [(0.0, 6, 0.0, 0.01), (3.0, 6, 0.65, 0.72), (6.0, 6, 0.919, 0.921), (30.0, 6, 0.95, 0.99)],
)
def test_progress_curve(app, elapsed, expected, low, high):
    p = _splash(app, elapsed=elapsed, expected=expected).progress()
    assert low <= p <= high


def test_right_text(app):
    assert _splash(app, elapsed=1.2, expected=6).right_text() == "zostało ok. 5 s"
    assert _splash(app, elapsed=7.0, expected=6).right_text() == "jeszcze chwilkę…"


def test_expected_seconds_default_and_saved(ini):
    assert ss.load_startup_seconds() in (ss.DEFAULT_LOCAL_S, ss.DEFAULT_NETWORK_S)
    ss.save_startup_seconds(4.37)
    assert ss.load_startup_seconds() == pytest.approx(4.37)
    ss.save_startup_seconds(10_000)  # nierealne — nie zapisuje
    assert ss.load_startup_seconds() == pytest.approx(4.37)


def test_network_drive_detection():
    assert ss._on_network_drive(r"\\serwer\udzial\app.exe") is True


def test_expected_is_clamped(app):
    assert _splash(app, elapsed=0, expected=0.1)._expected == 2.0
    assert _splash(app, elapsed=0, expected=999)._expected == 120.0


def test_finish_closes_splash_then_shows_window(app):
    s = _splash(app, elapsed=1, expected=6)
    s.show()
    win = QWidget()
    shown = []
    s.finish(win, lambda: shown.append(True), hold_ms=0)
    assert s.progress() == 1.0 and s.right_text() == ""
    deadline = time.perf_counter() + 2
    while not shown and time.perf_counter() < deadline:
        app.processEvents()
    assert shown and win.isVisible() and not s.isVisible()
    assert ss._ACTIVE is None
    win.close()


def test_pulse_without_splash_is_noop():
    ss._ACTIVE = None
    ss.pulse()
