"""Weryfikacja: checkbox segregacji jest zawsze klikalny (poza trybem wizek)."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.main_window import MainWindow


def test_segregate_enabled_with_one_format() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    assert win.segregate_cb.isEnabled(), "Segreguj musi być włączony przy starcie"
    assert not win.segregate_cb.isChecked(), "Domyślnie odznaczony"

    win.segregate_cb.click()
    assert win.segregate_cb.isChecked(), "Klik musi zaznaczyć checkbox"

    win.segregate_cb.click()
    assert not win.segregate_cb.isChecked(), "Drugi klik musi odznaczyć"

    win.wiz_sequence_cb.setChecked(True)
    assert not win.segregate_cb.isEnabled(), "W trybie wizek segregacja wyłączona"

    win.wiz_sequence_cb.setChecked(False)
    assert win.segregate_cb.isEnabled(), "Po wyjściu z wizek segregacja znów aktywna"

    win.close()
    app.processEvents()


if __name__ == "__main__":
    test_segregate_enabled_with_one_format()
    print("OK: test_segregate_checkbox")
