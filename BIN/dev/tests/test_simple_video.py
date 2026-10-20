"""Tryb prosty: film na liście odsłania ustawienia GIF-a i przekazuje je do konwersji."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp):
    win = MainWindow()
    win.resize(1000, 800)
    win._set_ui_mode("simple", mark_dirty=False)
    win.show()
    qapp.processEvents()
    yield win
    win.hide()
    win.deleteLater()
    qapp.processEvents()


def test_video_tile_shows_only_for_video(window, qapp, tmp_path: Path) -> None:
    zdjecie = tmp_path / "kot.png"
    Image.new("RGB", (8, 8), (10, 120, 60)).save(zdjecie)
    window._add_path_to_queue(zdjecie)
    window._update_queue_label()
    qapp.processEvents()
    assert not window.simple_video_tile.isVisible(), "same zdjęcia — kafelek filmu ma być schowany"

    film = tmp_path / "klip.mov"
    film.write_bytes(b"")
    window._add_path_to_queue(film)
    window._update_queue_label()
    qapp.processEvents()
    assert window.simple_video_tile.isVisible(), "film na liście — kafelek filmu ma być widoczny"


def test_simple_opts_carry_video_settings(window) -> None:
    window.simple_video_mode.set_value("ultra")  # ULTRA
    window.simple_video_frames.setValue(6)
    opts = window._simple_format_opts()
    assert opts.video_mode == "ultra"
    assert opts.video_ultra_frames == 6


def test_simple_number_field_follows_mode(window, qapp) -> None:
    """Plynnie pyta o klatki na sekunde, ULTRA o liczbe zatrzyman — jedno pole naraz."""
    window.simple_video_tile.setVisible(True)
    qapp.processEvents()
    window.simple_video_mode.set_value("smooth", emit=True)  # plynnie
    qapp.processEvents()
    assert window.simple_video_fps.isVisible() and not window.simple_video_frames.isVisible()
    assert window.simple_video_num_label.text() == "Klatki na sekundę"
    assert window.simple_video_fps.suffix() == " kl/s"

    window.simple_video_mode.set_value("ultra", emit=True)  # ULTRA
    qapp.processEvents()
    assert window.simple_video_frames.isVisible() and not window.simple_video_fps.isVisible()
    assert window.simple_video_num_label.text() == "Liczba zatrzymań"


def test_simple_video_row_is_two_pills_and_nothing_is_disabled(window, qapp) -> None:
    """S81: dwie drogi pigułkami (Płynnie / ULTRA), jedno pole liczbowe naraz, żadne pole nie jest wyszarzone."""
    window.simple_video_tile.setVisible(True)
    qapp.processEvents()
    pills = window.simple_video_mode
    assert [pills.button(k).text() for k in pills.keys()] == ["Płynnie", "ULTRA"]
    assert pills.keys() == ["smooth", "ultra"]
    for mode in ("smooth", "ultra"):
        pills.set_value(mode, emit=True)
        qapp.processEvents()
        visible = [w for w in (window.simple_video_fps, window.simple_video_frames) if w.isVisible()]
        assert len(visible) == 1 and visible[0].isEnabled()
        assert all(pills.button(k).isEnabled() for k in pills.keys())


def test_simple_fps_reaches_opts(window) -> None:
    window.simple_video_mode.set_value("smooth")
    window.simple_video_fps.setValue(20)
    opts = window._simple_format_opts()
    assert opts.video_mode == "smooth"
    assert opts.video_fps == 20
