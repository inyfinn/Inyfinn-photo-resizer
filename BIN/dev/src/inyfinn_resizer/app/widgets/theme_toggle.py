"""Przełącznik jasny / ciemny motyw (suwak słońce–księżyc).

Dwa stany: słońce = tryb jasny, księżyc = tryb ciemny. Styl kolorów (zieleń / krem) wybiera
menu Narzędzia → Styl kolorów; suwak go nie zmienia. Kolory suwaka z bieżącego motywu.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def _token(name: str) -> str:
    """Kolor z roli motywu (themes.theme_token) — w tym pliku nie ma stałych kolorów."""
    from inyfinn_resizer.app.themes import theme_token

    return theme_token(name)


TOGGLE_TOOLTIP = "Tryb jasny lub ciemny (styl kolorów: Narzędzia → Styl kolorów)"


class ThemeToggle(QWidget):
    """Suwak inspirowany Uiverse — klik przełącza motyw."""

    toggled = Signal(bool)

    def __init__(self, *, dark: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dark = dark
        self.setFixedSize(64, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(TOGGLE_TOOLTIP)
        self.setObjectName("themeToggleWidget")

    def is_dark(self) -> bool:
        return self._dark

    def set_dark(self, dark: bool) -> None:
        if self._dark != dark:
            self._dark = dark
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dark = not self._dark
            self.toggled.emit(self._dark)
            self.update()
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # DS 1.6.0 (G5): wyłączony = tor switch-off + obrys 1 px switch-off-border, włączony (ciemny motyw) = tor
        # switch-on; gałka switch-knob. Słońce w kolorze switch-on, księżyc czytelny na gałce.
        w, h = self.width(), self.height()
        slot_h = h - 4
        slot = QRectF(2, 2, w - 4, slot_h)
        if self._dark:
            track = QColor(_token("@SWITCH_ON@"))
            p.setPen(QPen(track, 1))
        else:
            track = QColor(_token("@SWITCH_OFF@"))
            p.setPen(QPen(QColor(_token("@SWITCH_OFF_BORDER@")), 1))
        p.setBrush(track)
        p.drawRoundedRect(slot, slot_h / 2, slot_h / 2)

        knob_d = slot_h - 6
        knob_x = slot.right() - knob_d - 3 if self._dark else slot.left() + 3
        knob = QRectF(knob_x, slot.top() + 3, knob_d, knob_d)
        knob_fill = QColor(_token("@SWITCH_KNOB@"))
        p.setPen(Qt.NoPen)
        p.setBrush(knob_fill)
        p.drawEllipse(knob)

        c = knob.center()
        if not self._dark:
            sun = QColor(_token("@SWITCH_SUN@"))
            inner = knob_d * 0.42
            p.setBrush(sun)
            p.drawEllipse(QRectF(c.x() - inner / 2, c.y() - inner / 2, inner, inner))
            p.setPen(QPen(sun, 1.5))
            for i in range(8):
                rad = math.radians(i * 45)
                r0 = knob_d / 2 + 2
                r1 = r0 + 4
                p.drawLine(
                    QPointF(c.x() + r0 * math.cos(rad), c.y() + r0 * math.sin(rad)),
                    QPointF(c.x() + r1 * math.cos(rad), c.y() + r1 * math.sin(rad)),
                )
        else:
            # księżyc = tarcza w kolorze switch-moon z wycięciem w kolorze gałki (półksiężyc)
            moon_d = knob_d * 0.62
            p.setBrush(QColor(_token("@SWITCH_MOON@")))
            p.drawEllipse(QRectF(c.x() - moon_d / 2, c.y() - moon_d / 2, moon_d, moon_d))
            cut_d = moon_d * 0.8
            p.setBrush(knob_fill)
            p.drawEllipse(QRectF(c.x() - cut_d / 2 + moon_d * 0.28, c.y() - cut_d / 2 - moon_d * 0.18, cut_d, cut_d))

        p.end()
