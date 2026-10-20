"""Pytanie o zajęte nazwy (2.6.8, S82/S83): bezpieczne „Zapisz obok z dopiskiem” jest głównym przyciskiem i domyślnym
(Enter), nieodwracalne „Nadpisz” to przycisk z obrysem; w tekstach nie ma wewnętrznego dopisku `_conv`."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from inyfinn_resizer.app.dialogs import simple_save_dialog as ssd


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def _dialog(n=2, total=3, same=True):
    names = [Path(f"C:/zdjecia/foto{i}.png") for i in range(n)]
    return ssd.SaveConflictDialog(None, conflicts=names, total=total, same_as_source=same)


def _text(dlg) -> str:
    return " ".join(lbl.text() for lbl in dlg.findChildren(QLabel)).replace("\u00a0", " ")


def test_texts_buttons_and_tooltips(app):
    dlg = _dialog()
    assert dlg.windowTitle() == "Te nazwy są już zajęte"
    assert dlg.findChild(QLabel, "saveChoiceTitle").text() == "Te nazwy są już zajęte"
    assert dlg.suffix_button.text() == "Zapisz obok z dopiskiem"
    assert dlg.suffix_button.toolTip() == "Oryginał zostaje bez zmian. Nowy plik dostaje dopisek w nazwie."
    assert dlg.overwrite_button.text() == "Nadpisz"
    assert dlg.overwrite_button.toolTip() == "Zastąpi istniejące pliki. Tego nie da się cofnąć."
    cancel = [b for b in dlg.findChildren(QPushButton) if b.text() == "Anuluj"]
    assert len(cancel) == 1 and cancel[0].objectName() == "btnLink"


def test_safe_action_is_primary_and_default(app):
    dlg = _dialog()
    assert dlg.suffix_button.objectName() == "saveChoicePrimary"
    assert dlg.suffix_button.isDefault()
    assert dlg.overwrite_button.objectName() == "saveChoiceOutline"
    assert not dlg.overwrite_button.isDefault()
    assert not dlg.overwrite_button.autoDefault()


def test_only_one_yellow_button_and_safe_one_comes_first(app):
    dlg = _dialog()
    primaries = [b for b in dlg.findChildren(QPushButton) if b.objectName() == "saveChoicePrimary"]
    assert primaries == [dlg.suffix_button]
    lay = dlg.layout()
    order = [lay.itemAt(i).widget() for i in range(lay.count()) if lay.itemAt(i).widget() is not None]
    assert order.index(dlg.suffix_button) < order.index(dlg.overwrite_button)


def test_body_counts_names_and_original_warning(app):
    text = _text(_dialog(n=2, total=3, same=True))
    assert "2 z 3 plików ma już plik o tej samej nazwie w miejscu zapisu:" in text
    assert "foto0.png" in text and "foto1.png" in text
    assert "Nadpisanie zastąpi oryginały." in text
    # inny folder niż źródło: bez ostrzeżenia o oryginałach
    assert "oryginał" not in _text(_dialog(n=2, total=3, same=False))


def test_body_shows_at_most_three_names_and_the_rest_as_count(app):
    text = _text(_dialog(n=6, total=8))
    assert "foto0.png" in text and "foto2.png" in text and "foto3.png" not in text
    assert "i 3 innych" in text
    one_more = _text(_dialog(n=4, total=8))
    assert "i 1 inny" in one_more and "foto3.png" not in one_more


def test_single_file_wording_and_singular_original(app):
    text = _text(_dialog(n=1, total=1, same=True))
    assert "Plik o tej samej nazwie już istnieje w miejscu zapisu:" in text
    assert "Nadpisanie zastąpi oryginał." in text


def test_no_internal_suffix_in_visible_texts(app):
    dlg = _dialog()
    everything = _text(dlg) + " ".join(b.text() + b.toolTip() for b in dlg.findChildren(QPushButton))
    assert "_conv" not in everything and "conv" not in everything.lower()


def test_no_unbreakable_one_letter_words_at_line_end(app):
    """S72: po jednoliterowych wyrazach twarda spacja (w zdaniu „n z total plików…”)."""
    dlg = _dialog()
    raw = " ".join(lbl.text() for lbl in dlg.findChildren(QLabel))
    assert " w miejscu" not in raw and " o tej" not in raw and "\u00a0" in raw


def test_enter_picks_suffix(app):
    dlg = _dialog()
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)  # bez okna na ekranie usera
    dlg.show()
    app.processEvents()
    QTest.keyClick(dlg, Qt.Key.Key_Return)
    app.processEvents()
    assert dlg.result() == ssd.SaveConflictDialog.Accepted
    assert dlg.choice() == ssd.SUFFIX == "suffix"


@pytest.mark.parametrize("button, expected", (("suffix_button", "suffix"), ("overwrite_button", "overwrite")))
def test_clicks_return_choice(app, button, expected):
    dlg = _dialog()
    getattr(dlg, button).click()
    assert dlg.choice() == expected
    assert dlg.result() == ssd.SaveConflictDialog.Accepted


def test_cancel_returns_none(app, monkeypatch):
    monkeypatch.setattr(ssd.SaveConflictDialog, "exec", lambda self: ssd.SaveConflictDialog.Rejected)
    assert ssd.ask_save_conflict(None, conflicts=[Path("a.png")], total=1, same_as_source=False) is None


def test_ask_returns_the_clicked_choice(app, monkeypatch):
    def fake_exec(self):
        self.overwrite_button.click()
        return ssd.SaveConflictDialog.Accepted

    monkeypatch.setattr(ssd.SaveConflictDialog, "exec", fake_exec)
    assert ssd.ask_save_conflict(None, conflicts=[Path("a.png")], total=2, same_as_source=True) == "overwrite"
