"""Ikony kroków workflow — badge w stylu mobilnego konwertera (2x, biały glyph)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

STEP_ACCENTS = {
    "format": ("#6366f1", "#eef2ff"),
    "dimensions": ("#0d9488", "#ecfdf5"),
    "save": ("#ea580c", "#fff7ed"),
}

BADGE_SIZE = 40
RENDER_SCALE = 2


def _badge_canvas(logical_size: int) -> tuple[QPixmap, QPainter, float]:
    px = QPixmap(logical_size * RENDER_SCALE, logical_size * RENDER_SCALE)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.scale(RENDER_SCALE, RENDER_SCALE)
    return px, painter, float(logical_size)


def _finish_icon(px: QPixmap, painter: QPainter, logical_size: int) -> QPixmap:
    painter.end()
    return px.scaled(
        logical_size,
        logical_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _draw_format_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    c = size / 2
    r = 8.5
    painter.drawArc(int(c - r), int(c - r), int(r * 2), int(r * 2), 35 * 16, 290 * 16)
    painter.drawLine(int(c + 5), int(c - 3), int(c + 9), int(c - 7))
    painter.drawLine(int(c + 5), int(c - 3), int(c + 9), int(c + 1))


def _draw_dimensions_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    m = 10.0
    s = size - m
    painter.drawLine(int(m), int(s), int(s), int(m))
    arm = 4.5
    painter.drawLine(int(s - arm), int(m), int(s), int(m))
    painter.drawLine(int(s), int(m), int(s), int(m + arm))
    painter.drawLine(int(m), int(s), int(m + arm), int(s))
    painter.drawLine(int(m), int(s), int(m), int(s - arm))


def _draw_save_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    folder = QPainterPath()
    folder.moveTo(11, 14)
    folder.lineTo(11, 10)
    folder.lineTo(15, 10)
    folder.lineTo(17, 12)
    folder.lineTo(29, 12)
    folder.lineTo(29, 30)
    folder.lineTo(11, 30)
    folder.closeSubpath()
    painter.drawPath(folder)
    painter.drawLine(16, 18, 24, 18)
    painter.drawLine(16, 22, 22, 22)
    painter.drawLine(16, 26, 20, 26)


def step_pixmap(step_key: str, *, size: int | None = None) -> QPixmap:
    accent, _bg = STEP_ACCENTS.get(step_key, STEP_ACCENTS["format"])
    logical = size or BADGE_SIZE
    px, painter, side = _badge_canvas(logical)
    radius = 10.0
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(0.5, 0.5, side - 1, side - 1, radius, radius)
    painter.setPen(QPen(QColor(255, 255, 255, 55), 1.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(1.5, 1.5, side - 3, side - 3, radius - 1, radius - 1)
    if step_key == "format":
        _draw_format_white(painter, side)
    elif step_key == "dimensions":
        _draw_dimensions_white(painter, side)
    else:
        _draw_save_white(painter, side)
    return _finish_icon(px, painter, logical)


def step_icon(step_key: str) -> QIcon:
    return QIcon(step_pixmap(step_key))


def action_icon_refresh_path() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#ffffff"), 2.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(6, 6, 20, 20, 50 * 16, 280 * 16)
    painter.drawLine(22, 6, 22, 11)
    painter.drawLine(22, 6, 18, 6)
    painter.end()
    return QIcon(px.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


def action_icon_restore() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#6366f1"), 2.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(8, 16)
    path.lineTo(12, 12)
    path.lineTo(12, 14)
    path.lineTo(22, 14)
    path.lineTo(22, 22)
    path.lineTo(8, 22)
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return QIcon(px.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


def action_icon_folder_orange() -> QIcon:
    px, painter, side = _badge_canvas(16)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#ea580c"))
    painter.drawRoundedRect(0, 0, side, side, 4, 4)
    pen = QPen(QColor("#ffffff"), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(3, 5, 10, 8, 1, 1)
    painter.drawRoundedRect(3, 3, 5, 3, 1, 1)
    return QIcon(_finish_icon(px, painter, 16))
