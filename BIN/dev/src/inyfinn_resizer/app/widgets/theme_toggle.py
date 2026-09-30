"""Przełącznik jasny / ciemny motyw (suwak słońce–księżyc).

Dwa stany: słońce = tryb jasny, księżyc = tryb ciemny. Styl kolorów (zieleń / krem) wybiera
menu Narzędzia → Styl kolorów; suwak go nie zmienia. Kolory suwaka z bieżącego motywu.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def _token(name: str, fallback: str) -> str:
    try:
        from inyfinn_resizer.app.themes import theme_token

        return theme_token(name)
    except Exception:
        return fallback


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

        w, h = self.width(), self.height()
        slot_h = h - 4
        slot = QRectF(2, 2, w - 4, slot_h)
        slot_bg = QColor(_token("@BG_INPUT@", "#ffffff"))
        p.setPen(QPen(QColor(_token("@FIELD_BORDER@", "#9C8B72")), 1))
        p.setBrush(slot_bg)
        p.drawRoundedRect(slot, slot_h / 2, slot_h / 2)

        knob_d = slot_h - 6
        knob_x = slot.right() - knob_d - 3 if self._dark else slot.left() + 3
        knob = QRectF(knob_x, slot.top() + 3, knob_d, knob_d)
        knob_fill = QColor(_token("@BG_HOVER@", "#2F4D39")) if self._dark else QColor("#ffeccf")
        p.setPen(Qt.NoPen)
        p.setBrush(knob_fill)
        p.drawEllipse(knob)

        inner = knob_d * 0.42
        inner_rect = QRectF(
            knob.center().x() - inner / 2,
            knob.center().y() - inner / 2,
            inner,
            inner,
        )
        p.setBrush(QColor(_token("@FG_TEXT@", "#F5F1E8")) if self._dark else QColor("#ffbb52"))
        p.drawEllipse(inner_rect)

        if not self._dark:
            p.setPen(QPen(QColor("#ffbb52"), 1.5))
            for i in range(8):
                angle = i * 45
                import math

                rad = math.radians(angle)
                cx, cy = knob.center().x(), knob.center().y()
                r0 = knob_d / 2 + 2
                r1 = r0 + 4
                p.drawLine(
                    QPointF(cx + r0 * math.cos(rad), cy + r0 * math.sin(rad)),
                    QPointF(cx + r1 * math.cos(rad), cy + r1 * math.sin(rad)),
                )
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(_token("@FG_MUTED@", "#C9BEA6")))
            c = knob.center()
            p.drawEllipse(QRectF(c.x() - knob_d * 0.22, c.y() - knob_d * 0.28, knob_d * 0.35, knob_d * 0.35))

        p.end()
