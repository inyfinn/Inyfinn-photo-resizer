"""Lista plików: zaznaczanie Ctrl/Shift, Delete i ✕ w trybie prostym i zaawansowanym."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.main_window import MainWindow
from inyfinn_resizer.app.widgets.removable_items import remove_zone


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, tmp_path: Path):
    win = MainWindow()
    win.resize(1200, 850)
    files = []
    for i in range(5):
        p = tmp_path / f"zdjecie_{i}.png"
        Image.new("RGB", (8, 8), (200, 20, 30)).save(p)
        files.append(p)
        win._add_path_to_queue(p)
    win._update_queue_label()
    win.show()
    qapp.processEvents()
    yield win, [p.resolve() for p in files]
    win.hide()
    win.deleteLater()
    qapp.processEvents()


def _click_row(view, row: int, modifier=Qt.KeyboardModifier.NoModifier) -> None:
    rect = view.visualRect(view.model().index(row, 0))
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, modifier, rect.center() - QPoint(40, 0))


def test_simple_ctrl_shift_select_and_delete_key(window, qapp) -> None:
    win, files = window
    win._set_ui_mode("simple", mark_dirty=False)
    view = win.simple_file_list
    assert view.count() == 5
    _click_row(view, 0)
    _click_row(view, 2, Qt.KeyboardModifier.ShiftModifier)
    assert len(view.selectedItems()) == 3, "Shift+klik zaznacza zakres 0..2"
    _click_row(view, 4, Qt.KeyboardModifier.ControlModifier)
    assert len(view.selectedItems()) == 4, "Ctrl+klik dokłada pojedynczy plik"
    view.setFocus()
    QTest.keyClick(view, Qt.Key.Key_Delete)
    qapp.processEvents()
    assert win._queue == [files[3]]
    assert view.count() == 1
    assert "1 plik" in win.simple_queue_label.text()


def test_simple_x_button_removes_single_file(window, qapp) -> None:
    win, files = window
    win._set_ui_mode("simple", mark_dirty=False)
    view = win.simple_file_list
    rect = view.visualRect(view.model().index(3, 0))
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, remove_zone(rect).center())
    qapp.processEvents()
    assert files[3] not in win._queue
    assert len(win._queue) == 4


def test_advanced_delete_key_and_x(window, qapp) -> None:
    win, files = window
    win._set_ui_mode("advanced", mark_dirty=False)
    qapp.processEvents()
    tree = win.input_tree
    _click_row(tree, 0)
    _click_row(tree, 1, Qt.KeyboardModifier.ControlModifier)
    tree.setFocus()
    QTest.keyClick(tree, Qt.Key.Key_Delete)
    qapp.processEvents()
    assert files[0] not in win._queue and files[1] not in win._queue
    assert len(win._queue) == 3
    # ✕ w kolumnie „Rozmiar”
    rect = tree.visualRect(tree.model().index(0, 1))
    first = Path(tree.topLevelItem(0).data(0, Qt.UserRole))
    QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, remove_zone(rect).center())
    qapp.processEvents()
    assert first not in win._queue
    assert len(win._queue) == 2
    # tryb prosty widzi ten sam stan
    assert win.simple_file_list.count() == 2


def test_simple_output_folder_starts_empty(window) -> None:
    win, _files = window
    win.output_dir_edit.setText(r"D:\stary\folder\z\poprzedniej\sesji")
    win._set_ui_mode("simple", mark_dirty=False)
    assert win._simple_output_dir is None
    assert win.simple_output_edit.text() == ""
