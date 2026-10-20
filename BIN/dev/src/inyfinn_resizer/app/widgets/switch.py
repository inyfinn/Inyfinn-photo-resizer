"""Przełącznik DS (rozdz. 25.8 / 26.4): tor 48×28, gałka biała, napis „Włączone / Wyłączone” po lewej.

To zwykły ``QCheckBox`` (``isChecked``, ``setChecked``, ``toggled``) z własnym rysowaniem, więc kod, który dotąd czytał
pole wyboru „Włącz…”, dostaje ten sam stan. Kolory z roli motywu (``theme_token``), bez stałych w tym pliku.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QSizePolicy, QWidget

TRACK_W = 48
TRACK_H = 28
KNOB_D = 20
LABEL_GAP = 10


def _token(name: str) -> QColor:
    from inyfinn_resizer.app.themes import theme_token

    return QColor(theme_token(name))


class SwitchBox(QCheckBox):
    """Przełącznik z napisem; ``labels`` = (gdy wyłączony, gdy włączony)."""

    def __init__(self, labels: tuple[str, str] = ("Wyłączone", "Włączone"), parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionSwitch")
        self._labels = labels
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.toggled.connect(lambda _c: self.updateGeometry())

    def label_text(self) -> str:
        return self._labels[1 if self.isChecked() else 0]

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        widest = max(QFontMetrics(self.font()).horizontalAdvance(t) for t in self._labels)
        return QSize(widest + LABEL_GAP + TRACK_W, TRACK_H + 4)

    def minimumSizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return self.sizeHint()

    def hitButton(self, pos) -> bool:  # noqa: N802 (Qt API)
        return self.rect().contains(pos)

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        enabled = self.isEnabled()
        on = self.isChecked()
        track = QRectF(self.width() - TRACK_W, (self.height() - TRACK_H) / 2, TRACK_W, TRACK_H)
        if on:
            fill, edge = _token("@SWITCH_ON@"), _token("@SWITCH_ON@")
        else:
            fill, edge = _token("@SWITCH_OFF@"), _token("@SWITCH_OFF_BORDER@")
        if not enabled:
            fill.setAlphaF(0.5)
            edge.setAlphaF(0.5)
        p.setPen(QPen(edge, 1))
        p.setBrush(fill)
        p.drawRoundedRect(track.adjusted(0.5, 0.5, -0.5, -0.5), TRACK_H / 2, TRACK_H / 2)
        pad = (TRACK_H - KNOB_D) / 2
        knob_x = track.right() - pad - KNOB_D if on else track.left() + pad
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_token("@SWITCH_KNOB@"))
        p.drawEllipse(QRectF(knob_x, track.top() + pad, KNOB_D, KNOB_D))
        if self.hasFocus():
            focus = QPen(_token("@BORDER_FOCUS@"), 2)
            p.setPen(focus)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(track.adjusted(-1, -1, 1, 1), TRACK_H / 2 + 1, TRACK_H / 2 + 1)
        text_color = _token("@FG_TEXT@" if enabled else "@FG_MUTED@")
        p.setPen(text_color)
        p.setFont(self.font())
        p.drawText(
            QRectF(0, 0, self.width() - TRACK_W - LABEL_GAP, self.height()),
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            self.label_text(),
        )
        p.end()
