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
    window.simple_video_mode.setCurrentIndex(1)  # ULTRA
    window.simple_video_frames.setValue(6)
    opts = window._simple_format_opts()
    assert opts.video_mode == "ultra"
    assert opts.video_ultra_frames == 6


def test_simple_number_field_follows_mode(window, qapp) -> None:
    """Plynnie pyta o klatki na sekunde, ULTRA o liczbe zatrzyman — jedno pole naraz."""
    window.simple_video_tile.setVisible(True)
    qapp.processEvents()
    window.simple_video_mode.setCurrentIndex(0)  # plynnie
    qapp.processEvents()
    assert window.simple_video_fps.isVisible() and not window.simple_video_frames.isVisible()
    assert "Klatki/s" in window.simple_video_num_label.text()

    window.simple_video_mode.setCurrentIndex(1)  # ULTRA
    qapp.processEvents()
    assert window.simple_video_frames.isVisible() and not window.simple_video_fps.isVisible()
    assert "Zatrzymań" in window.simple_video_num_label.text()


def test_simple_fps_reaches_opts(window) -> None:
    window.simple_video_mode.setCurrentIndex(0)
    window.simple_video_fps.setValue(20)
    opts = window._simple_format_opts()
    assert opts.video_mode == "smooth"
    assert opts.video_fps == 20
