"""Testy kroków scroll w polach numerycznych."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app.widgets.wheel_controls import wheel_step_for_event


def _wheel_event(*, ctrl: bool = False, shift: bool = False, up: bool = True) -> QWheelEvent:
    app = QApplication.instance() or QApplication([])
    mods = Qt.KeyboardModifier.NoModifier
    if ctrl:
        mods |= Qt.KeyboardModifier.ControlModifier
    if shift:
        mods |= Qt.KeyboardModifier.ShiftModifier
    delta = 120 if up else -120
    return QWheelEvent(
        app.primaryScreen().availableGeometry().center(),
        app.primaryScreen().availableGeometry().center(),
        (0, delta),
        (0, delta),
        Qt.MouseButton.NoButton,
        mods,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )


def test_wheel_step_default_is_ten() -> None:
    assert wheel_step_for_event(_wheel_event()) == 10


def test_wheel_step_shift_is_hundred() -> None:
    assert wheel_step_for_event(_wheel_event(shift=True)) == 100


def test_wheel_step_ctrl_is_one() -> None:
    assert wheel_step_for_event(_wheel_event(ctrl=True)) == 1
