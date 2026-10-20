"""Lista rozszerzeń nie zwija się od razu (zgłoszenie usera 20.10.2026: „wybieranie rozszerzeń z listy rozwijanej
jest trudne, bo zwija się od razu”).

Wcześniej zwykły klik w format wybierał TYLKO ten format i zamykał listę; kilka formatów dało się wybrać tylko z Ctrl.
Teraz każdy klik przełącza format, lista zostaje otwarta, zamyka ją klik obok albo Esc.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.widgets.format_multi_combo import FormatMultiCombo


def _otworz():
    app = QApplication.instance() or QApplication(sys.argv)
    combo = FormatMultiCombo()
    combo.resize(300, 40)
    combo.show()
    combo.activateWindow()
    QTest.qWaitForWindowExposed(combo)
    combo.showPopup()
    QTest.qWait(150)
    view = combo.view()
    assert view.isVisible(), "lista musi się otworzyć"
    return app, combo, view


def _klik(combo, view, row: int, mods=Qt.KeyboardModifier.NoModifier) -> None:
    pos = view.visualRect(combo._list_model.index(row, 0)).center()
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, mods, pos)
    QTest.qWait(120)


def test_klik_przelacza_format_i_lista_zostaje() -> None:
    app, combo, view = _otworz()
    start = combo.selected_formats()
    _klik(combo, view, 2)
    third = combo._item_key(combo._list_model.item(2))
    assert view.isVisible(), "po kliknięciu formatu lista ma zostać otwarta"
    assert combo.selected_formats() == start + [third] or set(combo.selected_formats()) == set(start + [third])
    _klik(combo, view, 3)
    assert view.isVisible() and len(combo.selected_formats()) == 3, "drugi klik dokłada kolejny format"
    _klik(combo, view, 2)
    assert third not in combo.selected_formats(), "ponowny klik odznacza"
    combo.hidePopup()
    combo.close()


def test_ostatniego_formatu_nie_da_sie_odznaczyc() -> None:
    app, combo, view = _otworz()
    only = combo.selected_formats()
    row = combo._row_for_key(only[0])
    _klik(combo, view, row)
    assert combo.selected_formats() == only, "zawsze zostaje co najmniej jeden format"
    combo.hidePopup()
    combo.close()


def test_puszczenie_po_otwarciu_nie_zmienia_formatu() -> None:
    app, combo, view = _otworz()
    pos = view.visualRect(combo._list_model.index(2, 0)).center()
    QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    QTest.qWait(120)
    assert view.isVisible() and combo.selected_formats() == ["webp"]
    combo.hidePopup()
    combo.close()


if __name__ == "__main__":
    test_klik_przelacza_format_i_lista_zostaje()
    test_ostatniego_formatu_nie_da_sie_odznaczyc()
    test_puszczenie_po_otwarciu_nie_zmienia_formatu()
    print("OK: test_format_combo_popup")
