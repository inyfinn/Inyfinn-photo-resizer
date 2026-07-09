"""Dialog zmiany nazw plików."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.widgets.layout_helpers import ROW_GAP, add_form_row
from inyfinn_resizer.core.job import RenameRule
from inyfinn_resizer.core.rename.templates import preview_rename


class RenameDialog(AppDialog):
    def __init__(self, rule: RenameRule, queue: list[Path], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zmiana nazw")
        self.setMinimumSize(480, 360)
        self._rule = rule
        self._queue = queue

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(ROW_GAP)

        layout.addWidget(QLabel("Szablon nazwy (np. {name}_{counter:04d}):"))
        self.rename_template = QLineEdit(rule.template or "{name}_{counter:04d}")
        self.rename_template.setMinimumHeight(28)
        layout.addWidget(self.rename_template)

        sr = QGridLayout()
        sr.setHorizontalSpacing(10)
        sr.setVerticalSpacing(ROW_GAP)
        self.rename_search = QLineEdit(rule.search)
        self.rename_replace = QLineEdit(rule.replace)
        add_form_row(sr, 0, "Szukaj:", self.rename_search)
        add_form_row(sr, 1, "Zamień na:", self.rename_replace)
        layout.addLayout(sr)

        self.rename_preview = QListWidget()
        layout.addWidget(self.rename_preview, stretch=1)

        preview_btn = QPushButton("Podgląd nazw")
        preview_btn.setObjectName("btnSecondary")
        preview_btn.setMinimumHeight(28)
        preview_btn.clicked.connect(self._preview_rename)
        layout.addWidget(preview_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_rule(self) -> RenameRule:
        return RenameRule(
            enabled=True,
            template=self.rename_template.text().strip() or "{name}_{counter:04d}",
            search=self.rename_search.text(),
            replace=self.rename_replace.text(),
        )

    def _preview_rename(self) -> None:
        self.rename_preview.clear()
        if not self._queue:
            self.rename_preview.addItem("Dodaj pliki do listy, aby zobaczyć podgląd.")
            return
        fmt = "jpeg"
        parent = self.parent()
        if parent is not None and hasattr(parent, "format_combo"):
            fmt = parent.format_combo.first_selected()
        rule = self.get_rule()
        rows = preview_rename(self._queue, rule, fmt)
        if not rows:
            self.rename_preview.addItem("Brak wyników — sprawdź szablon nazwy.")
            return
        for old, new in rows:
            self.rename_preview.addItem(f"{old}  →  {new}")
