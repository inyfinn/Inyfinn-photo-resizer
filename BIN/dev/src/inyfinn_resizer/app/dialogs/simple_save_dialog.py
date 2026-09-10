"""Tryb prosty: brak folderu → nadpisz oryginały albo zapisz jako *_conv."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog

OVERWRITE = "overwrite"
CONV = "conv"


class SimpleSaveChoiceDialog(AppDialog):
    def __init__(
        self,
        parent=None,
        *,
        file_count: int,
        folders: list[Path],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gdzie zapisać?")
        self.setMinimumWidth(440)
        self._choice: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel("Nie wybrano folderu zapisu")
        title.setObjectName("saveChoiceTitle")
        title.setWordWrap(True)
        root.addWidget(title)

        n = max(1, file_count)
        plikow = "plik" if n == 1 else "pliki" if n < 5 else "plików"
        folder_txt = _folder_summary(folders)
        body = QLabel(
            f"Masz {n} {plikow} w {folder_txt}.\n"
            "Nadpisać oryginały, czy zapisać obok jako nowe pliki z dopiskiem _conv?"
        )
        body.setObjectName("saveChoiceBody")
        body.setWordWrap(True)
        root.addWidget(body)

        overwrite_btn = QPushButton("Nadpisz oryginały")
        overwrite_btn.setObjectName("saveChoicePrimary")
        overwrite_btn.setMinimumHeight(40)
        overwrite_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        overwrite_btn.setToolTip("Zastąpi pliki w tym samym folderze, w tym samym formacie.")
        overwrite_btn.clicked.connect(lambda: self._pick(OVERWRITE))
        root.addWidget(overwrite_btn)

        conv_btn = QPushButton("Zapisz jako nowe (_conv)")
        conv_btn.setObjectName("saveChoiceOutline")
        conv_btn.setMinimumHeight(40)
        conv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        conv_btn.setToolTip("np. KULKI-KREATYNA1_conv.png — oryginał zostaje nietknięty.")
        conv_btn.clicked.connect(lambda: self._pick(CONV))
        root.addWidget(conv_btn)

        hint = QLabel("Jeśli nazwa z _conv jest zajęta, program doda kolejny numer: _conv2, _conv3…")
        hint.setObjectName("saveChoiceHint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        cancel = QPushButton("Anuluj")
        cancel.setObjectName("btnSecondary")
        cancel.setMinimumHeight(36)
        cancel.setMinimumWidth(88)
        cancel.clicked.connect(self.reject)
        cancel_row.addWidget(cancel)
        root.addLayout(cancel_row)

    def _pick(self, choice: str) -> None:
        self._choice = choice
        self.accept()

    def choice(self) -> str | None:
        return self._choice


def _folder_summary(folders: list[Path]) -> str:
    names = []
    seen: set[str] = set()
    for folder in folders:
        key = str(folder)
        if key in seen:
            continue
        seen.add(key)
        names.append(folder.name or key)
        if len(names) == 2:
            break
    if not names:
        return "folderze źródłowym"
    if len(seen) == 1:
        return f"folderze „{names[0]}”"
    extra = len(seen) - len(names)
    if extra > 0:
        return f"folderach „{names[0]}”, „{names[1]}” i {extra} kolejnych"
    return f"folderach „{names[0]}” i „{names[1]}”"


def ask_simple_save_choice(parent, *, file_count: int, folders: list[Path]) -> str | None:
    dlg = SimpleSaveChoiceDialog(parent, file_count=file_count, folders=folders)
    if dlg.exec() != SimpleSaveChoiceDialog.Accepted:
        return None
    return dlg.choice()
