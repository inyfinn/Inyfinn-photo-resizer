"""Pytanie o zajęte nazwy (2.6.8, S82): nadpisać czy zapisać obok z dopiskiem. Wspólne dla trybu prostego i zaawansowanego."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from inyfinn_resizer.app.dialogs.base_dialog import DIALOG_STACK_GAP, AppDialog, apply_dialog_layout
from inyfinn_resizer.app.save_conflicts import OVERWRITE, SUFFIX, nbsp

TITLE = "Te nazwy są już zajęte"
SHOWN_NAMES = 3


def _body_text(conflicts: list[Path], total: int, same_as_source: bool) -> str:
    n = len(conflicts)
    if total <= 1:
        head = "Plik o tej samej nazwie już istnieje w miejscu zapisu:"
    else:
        head = f"{n} z {total} plików ma już plik o tej samej nazwie w miejscu zapisu:"
    names = [f"• {p.name}" for p in conflicts[:SHOWN_NAMES]]
    extra = n - SHOWN_NAMES
    if extra > 0:
        names.append("i 1 inny" if extra == 1 else f"i {extra} innych")
    lines = [nbsp(head), *names]
    if same_as_source:
        lines += ["", f"Nadpisanie zastąpi {'oryginał' if n == 1 else 'oryginały'}."]
    return "\n".join(lines)


class SaveConflictDialog(AppDialog):
    def __init__(self, parent=None, *, conflicts: list[Path], total: int, same_as_source: bool) -> None:
        super().__init__(parent)
        self.setWindowTitle(TITLE)
        self.setMinimumWidth(460)
        self._choice: str | None = None

        root = QVBoxLayout(self)
        apply_dialog_layout(root, spacing=DIALOG_STACK_GAP)

        title = QLabel(TITLE)
        title.setObjectName("saveChoiceTitle")
        title.setWordWrap(True)
        root.addWidget(title)

        body = QLabel(_body_text(conflicts, total, same_as_source))
        body.setObjectName("saveChoiceBody")
        body.setWordWrap(True)
        root.addWidget(body)

        # Bezpieczna droga = główna (żółta, Enter). Nadpisanie jest nieodwracalne, więc to przycisk z obrysem.
        suffix_btn = QPushButton("Zapisz obok z dopiskiem")
        suffix_btn.setObjectName("saveChoicePrimary")
        suffix_btn.setMinimumHeight(40)
        suffix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        suffix_btn.setToolTip("Oryginał zostaje bez zmian. Nowy plik dostaje dopisek w nazwie.")
        suffix_btn.setAutoDefault(True)
        suffix_btn.setDefault(True)
        suffix_btn.clicked.connect(lambda: self._pick(SUFFIX))
        root.addWidget(suffix_btn)

        overwrite_btn = QPushButton("Nadpisz")
        overwrite_btn.setObjectName("saveChoiceOutline")
        overwrite_btn.setMinimumHeight(40)
        overwrite_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        overwrite_btn.setToolTip("Zastąpi istniejące pliki. Tego nie da się cofnąć.")
        overwrite_btn.setAutoDefault(False)
        overwrite_btn.setDefault(False)
        overwrite_btn.clicked.connect(lambda: self._pick(OVERWRITE))
        root.addWidget(overwrite_btn)
        self.suffix_button = suffix_btn
        self.overwrite_button = overwrite_btn

        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        cancel = QPushButton("Anuluj")
        cancel.setObjectName("btnLink")
        cancel.setMinimumHeight(36)
        cancel.setMinimumWidth(88)
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        cancel_row.addWidget(cancel)
        root.addLayout(cancel_row)
        suffix_btn.setFocus(Qt.FocusReason.OtherFocusReason)

    def _pick(self, choice: str) -> None:
        self._choice = choice
        self.accept()

    def choice(self) -> str | None:
        return self._choice


def ask_save_conflict(parent, *, conflicts: list[Path], total: int, same_as_source: bool) -> str | None:
    """``"suffix"`` | ``"overwrite"`` | ``None`` (anulowano)."""
    dlg = SaveConflictDialog(parent, conflicts=conflicts, total=total, same_as_source=same_as_source)
    if dlg.exec() != SaveConflictDialog.Accepted:
        return None
    return dlg.choice()
