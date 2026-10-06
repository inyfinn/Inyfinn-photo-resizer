"""Przyciski w stylu Dobra Kaloria (2.6.2): trzy rodziny (główny żółty, drugorzędny z ramką, link),
ikony w kolorze tekstu przycisku, brak napisów wersalikami poza nagłówkami Mindset."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox, QPushButton

from inyfinn_resizer.app import themes
from inyfinn_resizer.app.dialogs.base_dialog import polish_dialog_buttons
from inyfinn_resizer.app.dialogs.message_boxes import _make_box
from inyfinn_resizer.app.widgets import layout_helpers, section_icons, tool_icons

ZJ = "dobra-kaloria-zielen-jasny"
KC = "dobra-kaloria-krem-ciemny"


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def _ink(icon) -> QColor:
    """Kolor najbardziej kryjącego piksela ikony."""
    img = icon.pixmap(16, 16).toImage()
    best, best_a = QColor(), -1
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() > best_a:
                best, best_a = c, c.alpha()
    return QColor(best.red(), best.green(), best.blue())


def test_browse_button_is_not_uppercase(app):
    btn = layout_helpers.browse_button()
    assert btn.text() == "Przeglądaj"
    assert btn.objectName() == "btnBrowse"


@pytest.mark.parametrize("theme", (ZJ, KC))
def test_button_icons_follow_icon_color(app, theme):
    """Runda 3: ikony przy przyciskach mają kolor roli icon (brąz #85654A / #CBBFA8), nie zieleń."""
    themes.apply_theme(app, theme)
    want = QColor(themes.theme_token("@ICON@"))
    for factory in (
        tool_icons.icon_plus_green,
        tool_icons.icon_minus_red,
        tool_icons.icon_folder_green,
        tool_icons.icon_clear_gray,
        section_icons.action_icon_folder_orange,
        section_icons.action_icon_refresh_path,
    ):
        got = _ink(factory())
        assert abs(got.red() - want.red()) < 12 and abs(got.green() - want.green()) < 12 and abs(got.blue() - want.blue()) < 12, (
            factory.__name__, got.name(), want.name())


def test_themed_icons_are_redrawn_after_theme_change(app):
    from PySide6.QtWidgets import QWidget

    host = QWidget()
    btn = QPushButton("x", host)
    themes.apply_theme(app, ZJ)
    layout_helpers.set_themed_icon(btn, tool_icons.icon_plus_green)
    before = _ink(btn.icon()).name()
    themes.apply_theme(app, KC)
    layout_helpers.refresh_themed_icons(host)
    assert _ink(btn.icon()).name() != before


def test_dialog_buttons_use_three_families(app):
    box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Close | QDialogButtonBox.Reset)
    polish_dialog_buttons(box)
    assert box.button(QDialogButtonBox.Ok).objectName() == "primaryBtn"
    assert box.button(QDialogButtonBox.Cancel).objectName() == "btnLink"
    assert box.button(QDialogButtonBox.Close).objectName() == "btnLink"
    assert box.button(QDialogButtonBox.Reset).objectName() == "btnSecondary"


def test_message_box_buttons(app):
    box = _make_box(None, QMessageBox.Question, "t", "x", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
    assert box.button(QMessageBox.Yes).objectName() == "primaryBtn"
    assert box.button(QMessageBox.No).objectName() == "btnSecondary"
    assert box.button(QMessageBox.Cancel).objectName() == "btnLink"


@pytest.mark.parametrize("theme", (ZJ, KC))
def test_qss_styles_every_button_family(theme):
    qss = themes.render_qss(theme)
    for name in ("btnLink", "primaryBtn", "btnSecondary", "updateDialogAction", "updateToastLater", "btnBrowse"):
        assert f"QPushButton#{name}" in qss, name
