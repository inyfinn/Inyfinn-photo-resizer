"""Usuwanie pozycji z listy plików: ✕ przy wierszu, klawisz Delete, zaznaczanie jak w Eksploratorze."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEvent, QModelIndex, QRect, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPen, QShortcut
from PySide6.QtWidgets import QAbstractItemView, QStyle, QStyledItemDelegate, QStyleOptionViewItem

_ZONE_W = 26  # szerokość strefy ✕ po prawej stronie komórki


def remove_zone(cell: QRect) -> QRect:
    return QRect(cell.right() - _ZONE_W + 1, cell.top(), _ZONE_W, cell.height())


class RemoveButtonDelegate(QStyledItemDelegate):
    """Rysuje ✕ po prawej stronie komórki; klik w ✕ = remove_clicked(index)."""

    remove_clicked = Signal(QModelIndex)

    def paint(self, painter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)
        zone = remove_zone(option.rect)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if not (hovered or selected):
            color = QColor(option.palette.text().color())
            color.setAlphaF(0.35)
        elif selected and not hovered:
            color = QColor("#ffffff")
        else:
            color = QColor("#e5484d")  # czerwień „usuń” — jak ikona minus przy przycisku Usuń
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        pen = QPen(color)
        pen.setWidthF(1.8)
        painter.setPen(pen)
        c = zone.center()
        r = 4
        painter.drawLine(c.x() - r, c.y() - r, c.x() + r, c.y() + r)
        painter.drawLine(c.x() - r, c.y() + r, c.x() + r, c.y() - r)
        painter.restore()

    def editorEvent(self, event, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:  # noqa: N802
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
            and remove_zone(option.rect).contains(event.position().toPoint())
        ):
            self.remove_clicked.emit(index)
            return True
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick) and remove_zone(
            option.rect
        ).contains(event.position().toPoint()):
            return True  # klik w ✕ nie zmienia zaznaczenia
        return super().editorEvent(event, model, option, index)


def install_remove_support(
    view: QAbstractItemView,
    *,
    on_remove_index: Callable[[QModelIndex], None],
    on_remove_selected: Callable[[], None],
    column: int | None = None,
) -> RemoveButtonDelegate:
    """✕ w wierszu + Delete/Backspace + wielokrotne zaznaczanie (Ctrl/Shift)."""
    view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    view.setMouseTracking(True)
    delegate = RemoveButtonDelegate(view)
    delegate.remove_clicked.connect(on_remove_index)
    if column is None:
        view.setItemDelegate(delegate)
    else:
        view.setItemDelegateForColumn(column, delegate)
    for key in (QKeySequence.StandardKey.Delete, QKeySequence(Qt.Key.Key_Backspace)):
        shortcut = QShortcut(QKeySequence(key), view)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(on_remove_selected)
    return delegate
