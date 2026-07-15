"""Ikony kroków workflow — badge w stylu mobilnego konwertera (2x, biały glyph)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

STEP_ACCENTS = {
    "format": ("#6366f1", "#eef2ff"),
    "dimensions": ("#0d9488", "#ecfdf5"),
    "save": ("#ea580c", "#fff7ed"),
}

# Tryb ciemny: przyciemnione, mniej nasycone warianty — nie rażą na ciemnym tle.
STEP_ACCENTS_DARK = {
    "format": "#3b3f7a",
    "dimensions": "#0f5a54",
    "save": "#8a4416",
}

HELP_ACCENTS = {
    "start": ("#2563eb", "#eff6ff"),
    "list": ("#7c3aed", "#f5f3ff"),
    "compression": ("#0891b2", "#ecfeff"),
    "advanced": ("#ca8a04", "#fefce8"),
    "menu": ("#64748b", "#f8fafc"),
    "update": ("#4f46e5", "#eef2ff"),
}

HELP_ACCENTS_DARK = {
    "start": "#2c4a86",
    "list": "#4a3a7a",
    "compression": "#155e73",
    "advanced": "#7a5410",
    "menu": "#3f4a5c",
    "update": "#3b3f7a",
    "format": "#3b3f7a",
    "dimensions": "#0f5a54",
    "save": "#8a4416",
}


def _is_dark() -> bool:
    try:
        from inyfinn_resizer.app.themes import current_theme

        return current_theme() == "dark"
    except Exception:
        return False

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
    if _is_dark():
        accent = STEP_ACCENTS_DARK.get(step_key, accent)
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


def _draw_start_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    c = size / 2
    painter.drawPolygon(
        [
            QPointF(c - 4, c - 7),
            QPointF(c + 8, c),
            QPointF(c - 4, c + 7),
        ]
    )


def _draw_list_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    for y in (13.0, 20.0, 27.0):
        painter.drawLine(11, int(y), 29, int(y))
    painter.drawLine(11, 13, 11, 27)


def _draw_compression_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(12, 26, 20, 18)
    painter.drawLine(20, 18, 28, 22)
    painter.drawLine(28, 22, 28, 12)


def _draw_advanced_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(14, 14, 12, 12)
    painter.drawLine(23, 23, 28, 28)


def _draw_menu_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    for y in (12.0, 20.0, 28.0):
        painter.drawLine(10, int(y), 30, int(y))


def _draw_update_white(painter: QPainter, size: float) -> None:
    white = QColor("#ffffff")
    pen = QPen(white, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(10, 10, 20, 20, 40 * 16, 280 * 16)
    painter.drawLine(24, 10, 24, 15)
    painter.drawLine(24, 10, 19, 10)


_HELP_DRAWERS = {
    "start": _draw_start_white,
    "list": _draw_list_white,
    "format": _draw_format_white,
    "compression": _draw_compression_white,
    "dimensions": _draw_dimensions_white,
    "save": _draw_save_white,
    "advanced": _draw_advanced_white,
    "menu": _draw_menu_white,
    "update": _draw_update_white,
}


def help_section_pixmap(section_key: str, *, size: int | None = None) -> QPixmap:
    accent, _bg = HELP_ACCENTS.get(section_key, STEP_ACCENTS.get(section_key, STEP_ACCENTS["format"]))
    if _is_dark():
        accent = HELP_ACCENTS_DARK.get(section_key, accent)
    logical = size or 32
    px, painter, side = _badge_canvas(logical)
    radius = 8.0
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(0.5, 0.5, side - 1, side - 1, radius, radius)
    drawer = _HELP_DRAWERS.get(section_key, _draw_start_white)
    drawer(painter, side)
    return _finish_icon(px, painter, logical)


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
