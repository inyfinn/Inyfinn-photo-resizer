"""Rozwijana lista wielokrotnego wyboru formatów (jak FastStone)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QListView

from inyfinn_resizer.app.i18n_pl import FORMAT_LABEL_PL
from inyfinn_resizer.core.formats.registry import OUTPUT_FORMATS

PRIMARY_FORMATS = ("webp", "jpeg", "png", "avif", "gif", "tiff", "heic", "bmp", "jxl", "jp2", "pdf")


class FormatMultiCombo(QComboBox):
    selectionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("formatMultiCombo")
        self._keys: list[str] = []

        model = QStandardItemModel(self)
        self.setModel(model)

        view = QListView(self)
        view.setObjectName("formatMultiList")
        view.setMinimumWidth(280)
        view.setMinimumHeight(180)
        self.setView(view)

        self.setEditable(True)
        le = self.lineEdit()
        if le:
            le.setReadOnly(True)
            le.setPlaceholderText("Wybierz formaty…")
            le.setCursor(Qt.PointingHandCursor)

        view.pressed.connect(self._on_item_pressed)

        for key in PRIMARY_FORMATS:
            if key not in OUTPUT_FORMATS:
                continue
            label = FORMAT_LABEL_PL.get(key, key.upper())
            item = QStandardItem(label)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(key, Qt.UserRole)
            item.setCheckState(Qt.Unchecked)
            model.appendRow(item)
            self._keys.append(key)

        self.set_selected(["webp"])

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.setFocus()
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def _on_item_pressed(self, index) -> None:
        item = self.model().itemFromIndex(index)
        if not item:
            return
        state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(state)
        self._update_summary()
        self.selectionChanged.emit()

    def _update_summary(self) -> None:
        sel = self.selected_formats()
        if not sel:
            text = "Wybierz formaty…"
        elif len(sel) == 1:
            text = FORMAT_LABEL_PL.get(sel[0], sel[0])
        else:
            short = ", ".join(FORMAT_LABEL_PL.get(k, k).split()[0] for k in sel[:4])
            if len(sel) > 4:
                short += f" +{len(sel) - 4}"
            text = short
        if self.lineEdit():
            self.lineEdit().setText(text)

    def selected_formats(self) -> list[str]:
        out: list[str] = []
        model = self.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item and item.checkState() == Qt.Checked:
                key = item.data(Qt.UserRole)
                if key:
                    out.append(str(key))
        return out

    def set_selected(self, formats: list[str]) -> None:
        model = self.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item:
                key = str(item.data(Qt.UserRole))
                item.setCheckState(Qt.Checked if key in formats else Qt.Unchecked)
        self._update_summary()

    def first_selected(self) -> str:
        sel = self.selected_formats()
        return sel[0] if sel else "webp"
