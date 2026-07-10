"""Ikony przycisków narzędziowych — plus zielony, minus czerwony."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


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
    return _glyph_icon(plus=True, color=QColor("#16a34a"))


def icon_minus_red() -> QIcon:
    return _glyph_icon(plus=False, color=QColor("#dc2626"))


def icon_folder_green() -> QIcon:
    """Zielona ikona folderu."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    fill = QColor("#16a34a")
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(fill)
    painter.drawRoundedRect(2, 5, 12, 9, 1, 1)
    painter.setBrush(QColor("#22c55e"))
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


def icon_clear_gray() -> QIcon:
    """Wyczyść — szary krzyżyk."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#64748b"), 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    margin = 4
    painter.drawLine(margin, margin, size - margin, size - margin)
    painter.drawLine(size - margin, margin, margin, size - margin)
    painter.end()
    return QIcon(px)
