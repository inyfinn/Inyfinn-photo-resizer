"""Ikony przycisków narzędziowych i plików — w kolorze ikony motywu (@ICON@, DS 1.6.0 rola icon).

Ikony nie mają własnych kolorów (zielony plus, czerwony minus, pomarańczowy folder, niebieskie słońce):
przyciski Dobrej Kalorii mają jeden akcent, ikona to brąz (beżowe zestawy) albo limonka (zieleń ciemny).
Po zmianie motywu ``layout_helpers.refresh_themed_icons`` rysuje je od nowa.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _token(name: str) -> QColor:
    from inyfinn_resizer.app.themes import theme_token

    return QColor(theme_token(name))


def _fg() -> QColor:
    """Kolor ikony w bieżącym motywie (rola icon)."""
    return _token("@ICON@")


def _glyph_icon(*, plus: bool, color: QColor, size: int = 16) -> QIcon:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, 2.0)  # S7: kreska ikon ≈ 2
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
    """Plus w kolorze ikony (nazwa historyczna)."""
    return _glyph_icon(plus=True, color=_fg())


def icon_minus_red() -> QIcon:
    """Minus w kolorze ikony (nazwa historyczna)."""
    return _glyph_icon(plus=False, color=_fg())


def icon_folder_green() -> QIcon:
    """Ikona folderu w kolorze ikony (nazwa historyczna)."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # S7: ikona liniowa (kontur, kreska ≈ 2), nie wypełniony kształt
    pen = QPen(_fg(), 1.6)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(2, 4.5)
    path.lineTo(6.2, 4.5)
    path.lineTo(7.6, 6)
    path.lineTo(14, 6)
    path.lineTo(14, 13)
    path.lineTo(2, 13)
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return QIcon(px)


def _file_frame(painter: QPainter) -> None:
    """Ramka pliku: kontur (ikona liniowa), bez wypełnienia."""
    painter.setPen(QPen(_fg(), 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(2, 3, 12, 10, 2, 2)


_ICON_GRID = 16  # ikony plików rysujemy na siatce 16×16 i skalujemy do żądanego rozmiaru
_ICON_DPR = 2  # bufor 2× — ostre linie na ekranie HiDPI i przy skali 125 %


def _grid_canvas(size: int) -> tuple[QPixmap, QPainter]:
    """Płótno size×size (px logiczne) w buforze 2×, współrzędne painter na siatce 16×16."""
    px = QPixmap(size * _ICON_DPR, size * _ICON_DPR)
    px.setDevicePixelRatio(_ICON_DPR)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / _ICON_GRID, size / _ICON_GRID)
    return px, painter


def icon_image_file(size: int = 16) -> QIcon:
    """Ikona pliku graficznego: kontur, słońce i wzgórze w kolorze ikony; ``size`` w px logicznych (np. 20)."""
    px, painter = _grid_canvas(size)
    _file_frame(painter)
    pen = QPen(_fg(), 1.4)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(4, 5, 3, 3)
    painter.drawPolyline([QPoint(3, 13), QPoint(8, 8), QPoint(13, 13)])
    painter.end()
    return QIcon(px)


def icon_video_file(size: int = 16) -> QIcon:
    """Ikona filmu — ta sama rodzina co ikona zdjęcia, ale klatka filmowa z play; ``size`` w px logicznych."""
    px, painter = _grid_canvas(size)
    _file_frame(painter)
    pen = QPen(_fg(), 1.4)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPolygon([QPoint(7, 6), QPoint(7, 11), QPoint(11, 8)])
    painter.end()
    return QIcon(px)


def icon_clear_gray() -> QIcon:
    """Wyczyść — krzyżyk w kolorze ikony (nazwa historyczna)."""
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(_fg(), 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    margin = 4
    painter.drawLine(margin, margin, size - margin, size - margin)
    painter.drawLine(size - margin, margin, margin, size - margin)
    painter.end()
    return QIcon(px)
