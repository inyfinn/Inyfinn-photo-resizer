"""Okno „Nie wybrano folderu zapisu” (2.6.3): bezpieczne „Zapisz jako nowe (_conv)” jest głównym
żółtym przyciskiem i domyślnym (Enter), nieodwracalne „Nadpisz oryginały” to przycisk drugorzędny."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from inyfinn_resizer.app.dialogs import simple_save_dialog as ssd


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def _dialog():
    return ssd.SimpleSaveChoiceDialog(None, file_count=3, folders=[Path("C:/zdjecia")])


def test_safe_action_is_primary_and_default(app):
    dlg = _dialog()
    assert dlg.conv_button.text() == "Zapisz jako nowe (_conv)"
    assert dlg.conv_button.objectName() == "saveChoicePrimary"
    assert dlg.conv_button.isDefault()
    assert dlg.overwrite_button.text() == "Nadpisz oryginały"
    assert dlg.overwrite_button.objectName() == "saveChoiceOutline"
    assert not dlg.overwrite_button.isDefault()
    assert not dlg.overwrite_button.autoDefault()


def test_only_one_yellow_button(app):
    dlg = _dialog()
    primaries = [b for b in dlg.findChildren(QPushButton) if b.objectName() == "saveChoicePrimary"]
    assert primaries == [dlg.conv_button]


def test_safe_action_comes_first(app):
    dlg = _dialog()
    lay = dlg.layout()
    order = [lay.itemAt(i).widget() for i in range(lay.count()) if lay.itemAt(i).widget() is not None]
    assert order.index(dlg.conv_button) < order.index(dlg.overwrite_button)


def test_enter_picks_conv(app):
    dlg = _dialog()
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)  # bez okna na ekranie usera
    dlg.show()
    app.processEvents()
    QTest.keyClick(dlg, Qt.Key.Key_Return)
    app.processEvents()
    assert dlg.result() == ssd.SimpleSaveChoiceDialog.Accepted
    assert dlg.choice() == ssd.CONV


@pytest.mark.parametrize("button, expected", (("conv_button", ssd.CONV), ("overwrite_button", ssd.OVERWRITE)))
def test_clicks_return_choice(app, button, expected):
    dlg = _dialog()
    getattr(dlg, button).click()
    assert dlg.choice() == expected
    assert dlg.result() == ssd.SimpleSaveChoiceDialog.Accepted


def test_cancel_returns_none(app, monkeypatch):
    monkeypatch.setattr(ssd.SimpleSaveChoiceDialog, "exec", lambda self: ssd.SimpleSaveChoiceDialog.Rejected)
    assert ssd.ask_simple_save_choice(None, file_count=1, folders=[]) is None
