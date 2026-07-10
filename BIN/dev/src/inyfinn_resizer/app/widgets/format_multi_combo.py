"""Multi-select format combo — Explorer-style selection in dropdown."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QModelIndex, QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QListView,
    QStyle,
    QStyleOptionComboBox,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QWidget,
)

from inyfinn_resizer.app.i18n_pl import FORMAT_LABEL_PL
from inyfinn_resizer.app.i18n_tooltips import (
    ALPHA_OUTPUT_FORMATS,
    FORMAT_ALPHA_TIPS,
    FORMAT_EXTENSION_TIPS,
)
from inyfinn_resizer.core.formats.registry import OUTPUT_FORMATS

PRIMARY_FORMATS = ("webp", "jpeg", "png", "avif", "gif", "tiff", "heic", "bmp", "jp2", "pdf")

_MULTI_SELECT_TOOLTIP = (
    "Kliknij nazwę formatu, aby wybrać tylko ten format.\n"
    "Możesz zaznaczyć więcej, jeśli chcesz — użyj Ctrl, Shift lub kliknij checkbox."
)

_ALPHA_NO_TRANSPARENCY_TIP = "To rozszerzenie nie obsługuje przezroczystości."


class _FormatListView(QListView):
    """List view that blocks Qt's default checkbox toggle on row click."""

    def __init__(self, combo: "FormatMultiCombo", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._combo = combo
        self._handled_press = False
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._handled_press = False
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.indexAt(event.pos())
            if idx.isValid():
                self._combo._keep_popup_open = True
                self._combo._handle_row_click(idx, event.pos(), event.modifiers())
                self._handled_press = True
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._handled_press:
            self._handled_press = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class _FormatItemDelegate(QStyledItemDelegate):
    """Delegate that paints checkboxes without letting Qt auto-toggle on row click."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        opt = QStyleOptionViewItem(option)
        model = index.model()
        if isinstance(model, QStandardItemModel):
            item = model.itemFromIndex(index)
            if item is not None:
                if not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                    opt.palette.setColor(opt.palette.ColorRole.Text, opt.palette.color(opt.palette.ColorRole.Mid))
                elif item.checkState() == Qt.CheckState.Checked:
                    opt.state &= ~QStyle.StateFlag.State_MouseOver
        super().paint(painter, opt, index)

    def editorEvent(
        self,
        event: QEvent,
        model,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        if event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
        ):
            return False
        return super().editorEvent(event, model, option, index)


class FormatMultiCombo(QComboBox):
    """Combo with multi-select popup (Ctrl/Shift/checkbox) and single-select on label click."""

    selectionChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("formatMultiCombo")
        self.setToolTip(_MULTI_SELECT_TOOLTIP)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._keep_popup_open = False
        line = self.lineEdit()
        if line is not None:
            line.setReadOnly(True)
            line.setToolTip(_MULTI_SELECT_TOOLTIP)
            line.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            line.installEventFilter(self)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(18)

        self._list_model = QStandardItemModel(self)
        self._block_item_changed = False
        self._anchor_row = 0
        self._alpha_only_mode = False
        self._formats_before_alpha: list[str] = []

        for key in PRIMARY_FORMATS:
            if key not in OUTPUT_FORMATS:
                continue
            label = FORMAT_LABEL_PL.get(key, OUTPUT_FORMATS[key]["label"])
            item = QStandardItem(label)
            item.setData(key, Qt.ItemDataRole.UserRole)
            item.setToolTip(FORMAT_EXTENSION_TIPS.get(key, label))
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list_model.appendRow(item)

        list_view = _FormatListView(self)
        list_view.setObjectName("formatMultiList")
        list_view.setModel(self._list_model)
        list_view.setItemDelegate(_FormatItemDelegate(list_view))
        list_view.setUniformItemSizes(True)
        list_view.setSpacing(0)
        self.setView(list_view)

        self._list_model.itemChanged.connect(self._on_item_changed)
        self.setModel(self._list_model)
        self.set_selected(["webp"])

    def set_alpha_only_mode(self, enabled: bool) -> None:
        """Ogranicza wybór do formatów z kanałem alpha (PNG/WebP/AVIF)."""
        if enabled == self._alpha_only_mode:
            return
        self._alpha_only_mode = enabled
        if enabled:
            self._formats_before_alpha = self.selected_formats()
            allowed = [f for f in self._formats_before_alpha if f in ALPHA_OUTPUT_FORMATS]
            if not allowed:
                allowed = ["png"]
            self.set_selected(allowed)
        else:
            restore = self._formats_before_alpha or ["webp"]
            self.set_selected(restore)
            self._formats_before_alpha = []
        self._apply_alpha_row_states()
        self._update_alpha_combo_style()

    def _update_alpha_combo_style(self) -> None:
        if self._alpha_only_mode:
            self.setToolTip(
                "Usuwanie tła wymaga formatu z przezroczystością (PNG, WebP, AVIF).\n"
                + _ALPHA_NO_TRANSPARENCY_TIP
            )
        else:
            self.setToolTip(_MULTI_SELECT_TOOLTIP)
        line = self.lineEdit()
        if line is not None:
            line.setToolTip(self.toolTip())

    def _apply_alpha_row_states(self) -> None:
        self._block_item_changed = True
        try:
            for row in range(self._list_model.rowCount()):
                item = self._list_model.item(row)
                key = self._item_key(item)
                if self._alpha_only_mode and key not in ALPHA_OUTPUT_FORMATS:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    item.setToolTip(_ALPHA_NO_TRANSPARENCY_TIP)
                else:
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    if self._alpha_only_mode and key in FORMAT_ALPHA_TIPS:
                        item.setToolTip(FORMAT_ALPHA_TIPS[key])
                    else:
                        item.setToolTip(FORMAT_EXTENSION_TIPS.get(key, item.text()))
        finally:
            self._block_item_changed = False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        line = self.lineEdit()
        if watched is line and event.type() == QEvent.Type.MouseButtonPress:
            mouse = event
            if isinstance(mouse, QMouseEvent) and mouse.button() == Qt.MouseButton.LeftButton:
                self.showPopup()
                return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def hidePopup(self) -> None:
        if self._keep_popup_open:
            return
        super().hidePopup()
        QTimer.singleShot(0, self._update_summary)

    def _release_keep_popup(self) -> None:
        self._keep_popup_open = False

    def _item_key(self, item: QStandardItem) -> str:
        return str(item.data(Qt.ItemDataRole.UserRole))

    def _row_for_key(self, key: str) -> int:
        for row in range(self._list_model.rowCount()):
            if self._item_key(self._list_model.item(row)) == key:
                return row
        return 0

    def _apply_check_states(self, keys: list[str]) -> None:
        wanted = set(keys)
        self._block_item_changed = True
        try:
            for row in range(self._list_model.rowCount()):
                item = self._list_model.item(row)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if self._item_key(item) in wanted
                    else Qt.CheckState.Unchecked
                )
        finally:
            self._block_item_changed = False

    def selected_formats(self) -> list[str]:
        out: list[str] = []
        for row in range(self._list_model.rowCount()):
            item = self._list_model.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                out.append(self._item_key(item))
        return out

    def set_selected(self, keys: list[str]) -> None:
        if not keys:
            keys = ["webp"]
        if self._alpha_only_mode:
            keys = [k for k in keys if k in ALPHA_OUTPUT_FORMATS] or ["png"]
        self._apply_check_states(keys)
        self._update_summary()
        self.selectionChanged.emit()

    def _update_summary(self) -> None:
        selected = self.selected_formats()
        if not selected:
            self.setCurrentText("Wybierz format")
            return
        if len(selected) == 1:
            key = selected[0]
            self.setCurrentText(FORMAT_LABEL_PL.get(key, key.upper()))
            return
        self.setCurrentText(f"{len(selected)} formatów")

    def _click_on_checkbox(self, view: QListView, pos: QPoint) -> bool:
        opt = QStyleOptionViewItem()
        idx = view.indexAt(pos)
        if not idx.isValid():
            return False
        opt.rect = view.visualRect(idx)
        indicator = view.style().subElementRect(
            QStyle.SubElement.SE_ItemViewItemCheckIndicator,
            opt,
            view,
        )
        if indicator.isValid():
            return indicator.adjusted(-4, -4, 4, 4).contains(pos)
        return pos.x() - opt.rect.x() <= 24

    def _handle_row_click(self, index: QModelIndex, pos: QPoint, modifiers: Qt.KeyboardModifier) -> None:
        row = index.row()
        item = self._list_model.item(row)
        if item is None:
            self._keep_popup_open = False
            return
        key = self._item_key(item)
        if self._alpha_only_mode and key not in ALPHA_OUTPUT_FORMATS:
            self._keep_popup_open = False
            return
        view = self.view()
        on_checkbox = isinstance(view, QListView) and self._click_on_checkbox(view, pos)

        self.blockSignals(True)
        try:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                start = min(self._anchor_row, row)
                end = max(self._anchor_row, row)
                keys = [
                    self._item_key(self._list_model.item(r))
                    for r in range(start, end + 1)
                ]
                self.set_selected(keys)
            elif modifiers & Qt.KeyboardModifier.ControlModifier or on_checkbox:
                self._toggle_row(row)
                self._anchor_row = row
                self._update_summary()
                self.selectionChanged.emit()
            else:
                self.set_selected([key])
                self._anchor_row = row
        finally:
            self.blockSignals(False)
            QTimer.singleShot(0, self._release_keep_popup)

    def _toggle_row(self, row: int) -> None:
        item = self._list_model.item(row)
        if item is None:
            return
        new_state = (
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        self._block_item_changed = True
        try:
            item.setCheckState(new_state)
            if new_state == Qt.CheckState.Unchecked and not self.selected_formats():
                item.setCheckState(Qt.CheckState.Checked)
        finally:
            self._block_item_changed = False

    def _on_item_changed(self, item: QStandardItem) -> None:
        if self._block_item_changed or item is None:
            return
        key = self._item_key(item)
        if item.checkState() == Qt.CheckState.Checked:
            self._block_item_changed = True
            try:
                self.set_selected([key])
                self._anchor_row = self._row_for_key(key)
            finally:
                self._block_item_changed = False
        elif not self.selected_formats():
            self._block_item_changed = True
            try:
                item.setCheckState(Qt.CheckState.Checked)
            finally:
                self._block_item_changed = False
        else:
            self._update_summary()
            self.selectionChanged.emit()

    def first_selected(self) -> str:
        sel = self.selected_formats()
        return sel[0] if sel else "jpeg"

    def showPopup(self) -> None:
        super().showPopup()
        view = self.view()
        if isinstance(view, QListView):
            view.setMinimumWidth(max(self.width(), 220))
