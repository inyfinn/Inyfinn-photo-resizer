"""Ikony przycisków narzędziowych — w kolorze tekstu przycisku (@FG_ACCENT@ bieżącego motywu).

Od 2.6.2 ikony nie mają własnych kolorów (zielony plus, czerwony minus, pomarańczowy folder):
przyciski Dobrej Kalorii mają jeden akcent, ikona idzie za tekstem. Po zmianie motywu
``layout_helpers.refresh_themed_icons`` rysuje je od nowa.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _fg() -> QColor:
    """Kolor tekstu przycisku drugorzędnego w bieżącym motywie."""
    try:
        from inyfinn_resizer.app.themes import theme_token

        return QColor(theme_token("@FG_ACCENT@"))
    except Exception:
        return QColor("#0F763E")


def _glyph_icon(*, plus: bool, color: QColor, size: int = 16) -> QIcon:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, 2.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    center = size // 2
    margin = 3
    if plus:
        painter.drawLine(center, margin, center, size - margin)
        painter.drawLine(margin, center, size - margin, center)
    else:
        painter.drawLine(margin, center, size - margin, center)
    painter.end()
    return QIcon(px)


def icon_plus_green() -> QIcon:
    """Plus w kolorze akcentu (nazwa historyczna)."""
    return _glyph_icon(plus=True, color=_fg())


def icon_minus_red() -> QIcon:
    """Minus w kolorze akcentu (nazwa historyczna)."""
    return _glyph_icon(plus=False, color=_fg())


def icon_folder_green() -> QIcon:
    """Ikona folderu w kolorze akcentu (nazwa historyczna)."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_fg())
    painter.drawRoundedRect(2, 5, 12, 9, 1, 1)
    painter.drawRoundedRect(2, 3, 7, 4, 1, 1)
    painter.end()
    return QIcon(px)


def icon_image_file() -> QIcon:
    """Ikona pliku graficznego."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    frame = QColor("#94a3b8")
    fill = QColor("#e2e8f0")
    painter.setPen(QPen(frame, 1.2))
    painter.setBrush(fill)
    painter.drawRoundedRect(2, 3, 12, 10, 1, 1)
    sun = QColor("#38bdf8")
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(sun)
    painter.drawEllipse(4, 5, 3, 3)
    hill = QColor("#22c55e")
    painter.setBrush(hill)
    from PySide6.QtCore import QPoint
    painter.drawPolygon([QPoint(4, 12), QPoint(8, 8), QPoint(12, 12)])
    painter.end()
    return QIcon(px)


def icon_video_file() -> QIcon:
    """Ikona filmu — ta sama rodzina co ikona zdjęcia, ale klatka filmowa z play."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#94a3b8"), 1.2))
    painter.setBrush(QColor("#e2e8f0"))
    painter.drawRoundedRect(2, 3, 12, 10, 1, 1)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#f59e0b"))
    from PySide6.QtCore import QPoint

    painter.drawPolygon([QPoint(7, 6), QPoint(7, 11), QPoint(11, 8)])
    painter.end()
    return QIcon(px)


def icon_clear_gray() -> QIcon:
    """Wyczyść — krzyżyk w kolorze akcentu (nazwa historyczna)."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(_fg(), 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    margin = 4
    painter.drawLine(margin, margin, size - margin, size - margin)
    painter.drawLine(size - margin, margin, margin, size - margin)
    painter.end()
    return QIcon(px)
