"""Kafelek „Kolory” (2.6.3): treść tuż pod nagłówkiem, bez pustej płyty nad suwakiem; kolumny równe."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app import user_settings


@pytest.fixture()
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / "settings.ini"
    monkeypatch.setattr(user_settings, "_settings", lambda: QSettings(str(path), QSettings.Format.IniFormat))
    from inyfinn_resizer.app.main_window import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH, MainWindow

    w = MainWindow()
    w.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    w._set_ui_mode("advanced", mark_dirty=False)
    yield w, app
    w.hide()
    w.deleteLater()


def _layout_of(window, tile):
    for lay in (window._bento_left_lay, window._bento_right_lay):
        if lay.indexOf(tile) >= 0:
            return lay
    return None


def test_colors_only_sits_under_background_tile(window):
    w, app = window
    w.format_combo.set_selected(["png"])
    app.processEvents()
    if not w._show_colors_tile or w._show_crop_tile:
        pytest.skip("PNG bez kafelka Kolory albo z Kadrem w tej konfiguracji")
    assert _layout_of(w, w._bento_tile_colors) is w._bento_left_lay
    assert _layout_of(w, w._bento_tile_dims) is w._bento_right_lay
    left = w._bento_left_lay
    assert left.indexOf(w._bento_tile_bg) < left.indexOf(w._bento_tile_colors)


def test_colors_content_right_under_heading(window):
    w, app = window
    w.format_combo.set_selected(["png"])
    w.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)  # układ bez okna na ekranie
    w.show()
    app.processEvents()
    tile = w._bento_tile_colors
    header = tile.findChild(type(tile.layout().itemAt(0).widget()), "sectionStepHeader")
    row_top = w._colors_row.mapTo(tile, w._colors_row.rect().topLeft()).y()
    header_bottom = header.geometry().bottom()
    assert row_top - header_bottom <= 16, (row_top, header_bottom)


def test_formats_without_palette_keep_262_layout(window):
    w, app = window
    w.format_combo.set_selected(["avif"])
    app.processEvents()
    assert not w._bento_tile_colors.isVisibleTo(w)
    assert _layout_of(w, w._bento_tile_dims) is w._bento_left_lay
