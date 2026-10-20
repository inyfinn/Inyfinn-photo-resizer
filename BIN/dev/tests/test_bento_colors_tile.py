"""Wiersze warunkowe kart trybu zaawansowanego (2.6.7): „Liczba kolorów” (PNG / GIF) i „Kadr” (przycięcie).

Do 2.6.6 były to kafelki Bento przestawiane między dwiema kolumnami (test pilnował ich kolejności). Od 2.6.7 karty stoją
w jednej kolumnie, a te dwie rzeczy to wiersze siatki kart Format i jakość / Wymiary — widoczne tylko wtedy, gdy mają sens.
"""

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
    w.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)  # układ bez okna na ekranie
    w.show()
    app.processEvents()
    yield w, app
    w.hide()
    w.deleteLater()


def _label_of(grid, field):
    return next(lbl for lbl, f in grid._rows if f is field)


@pytest.mark.parametrize("fmt,visible", [("png", True), ("gif", True), ("avif", False), ("jpeg", False), ("webp", False)])
def test_colors_row_only_for_png_and_gif(window, fmt, visible):
    w, app = window
    w.format_combo.set_selected([fmt])
    app.processEvents()
    assert w._show_colors_tile is visible
    assert w._colors_row.isVisibleTo(w) is visible
    assert _label_of(w._format_grid, w._colors_row).isVisibleTo(w) is visible  # etykieta znika razem z polem


def test_colors_row_sits_in_the_format_card_under_quality(window):
    w, app = window
    w.format_combo.set_selected(["png"])
    app.processEvents()
    card = w._cards["format"]
    assert card.isAncestorOf(w._colors_row)
    assert w._colors_row.mapTo(w, w._colors_row.rect().topLeft()).y() > w.quality_slider.mapTo(w, w.quality_slider.rect().topLeft()).y()


def test_crop_row_follows_resize_mode(window):
    w, app = window
    # preset z przycinaniem do ramki pokazuje „Kadr”, zwykła skala go chowa
    w.custom_format_cb.setChecked(True)
    app.processEvents()
    assert w._show_crop_tile and w.crop_anchor_picker.isVisibleTo(w)
    assert _label_of(w._dims_grid, w.crop_anchor_picker).isVisibleTo(w)
    assert w._cards["dimensions"].isAncestorOf(w.crop_anchor_picker)
    w.custom_format_cb.setChecked(False)
    app.processEvents()
    if not w._show_crop_tile:
        assert not w.crop_anchor_picker.isVisibleTo(w)
        assert not _label_of(w._dims_grid, w.crop_anchor_picker).isVisibleTo(w)
