"""Panel „EAN i nazwy plików” dla presetów sieci z nazwami EAN_rola (Rossmann).

Jeden egzemplarz w oknie: MainWindow przenosi go między trybem prostym a zaawansowanym.
Wygląd z QSS (DS Dobra Kaloria): ``QLabel#retailVerdict[state="ok|bad|warn"]``, ``QLabel#retailFileName``.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRegularExpression, Qt, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.widgets.layout_helpers import BTN_H, mark_quiet, set_themed_icon, style_dropdown
from inyfinn_resizer.app.widgets.tool_icons import icon_clear_gray
from inyfinn_resizer.core.ean import ROLE_LABELS, SKIP_ROLE


def _set_state(label: QLabel, state: str) -> None:
    label.setProperty("state", state)
    label.style().unpolish(label)
    label.style().polish(label)


class _ElideLabel(QLabel):
    """Nazwa pliku skracana wielokropkiem w środku (pełna w podpowiedzi)."""

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self._full = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setToolTip(text)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        self.setText(self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideMiddle, self.width()))


class RetailNamesPanel(QWidget):
    ean_edited = Signal(str)
    role_changed = Signal(object, str)  # Path, rola ("" = nie wybrano)
    ean_chosen = Signal(str)  # klik w jedną z propozycji przy niezgodnych źródłach

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("retailNamesPanel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)
        title = QLabel("EAN produktu")
        title.setObjectName("formLabelInline")
        self.ean_edit = QLineEdit()
        self.ean_edit.setObjectName("eanEdit")
        self.ean_edit.setPlaceholderText("13 cyfr")
        self.ean_edit.setMaxLength(13)
        self.ean_edit.setFixedHeight(BTN_H)
        self.ean_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,13}"), self.ean_edit))
        self.ean_edit.setToolTip("Kod EAN produktu do nazw plików. Program wpisuje go sam, możesz go poprawić.")
        self.ean_edit.textEdited.connect(self.ean_edited.emit)
        row.addWidget(title)
        row.addWidget(self.ean_edit, 1)
        lay.addLayout(row)

        self.verdict = QLabel()
        self.verdict.setObjectName("retailVerdict")
        self.verdict.setWordWrap(True)
        lay.addWidget(self.verdict)

        self._choices = QWidget()
        ch_lay = QHBoxLayout(self._choices)
        ch_lay.setContentsMargins(0, 0, 0, 0)
        ch_lay.setSpacing(8)
        self._choice_btns: list[QPushButton] = []
        for _ in range(2):
            btn = mark_quiet(QPushButton())
            btn.setFixedHeight(BTN_H)
            btn.clicked.connect(lambda _=False, b=btn: self.ean_chosen.emit(b.property("ean")))
            ch_lay.addWidget(btn)
            self._choice_btns.append(btn)
        ch_lay.addStretch(1)
        self._choices.setVisible(False)
        lay.addWidget(self._choices)

        self._files_title = QLabel("Nazwy plików")
        self._files_title.setObjectName("formLabelInline")
        lay.addSpacing(6)
        lay.addWidget(self._files_title)
        self._rows_box = QWidget()
        self._rows = QVBoxLayout(self._rows_box)
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(16)  # wyraźny odstęp między plikami, ciaśniej wewnątrz wiersza
        lay.addWidget(self._rows_box)
        self.summary = QLabel()
        self.summary.setObjectName("hintLabel")
        self.summary.setWordWrap(True)
        lay.addWidget(self.summary)
        self._show_rows = True

    def set_ean(self, ean: str, verdict: str, state: str, choices: list[tuple[str, str]] = ()) -> None:
        """``choices`` = [(ean, napis przycisku)] przy niezgodnych źródłach, inaczej puste."""
        if self.ean_edit.text() != ean:
            self.ean_edit.setText(ean)
        self.verdict.setText(verdict)
        _set_state(self.verdict, state)
        for btn, choice in zip(self._choice_btns, list(choices) + [None, None]):
            btn.setVisible(choice is not None)
            if choice is not None:
                btn.setProperty("ean", choice[0])
                btn.setText(choice[1])
        self._choices.setVisible(bool(choices))

    def set_rows_visible(self, visible: bool) -> None:
        """Tryb prosty: role są w wierszach listy plików u góry, panel pokazuje tylko EAN i podsumowanie."""
        self._show_rows = visible
        self._rows_box.setVisible(visible)
        self._files_title.setVisible(visible and self._rows.count() > 0)

    def set_files(self, rows: list[tuple[Path, str, str, str, str]], summary: str = "") -> None:
        """Wiersz = (plik, rola, nazwa wynikowa, problem, notka). Problem pusty = dobrze."""
        while self._rows.count():
            item = self._rows.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for row in rows:
            self._rows.addWidget(file_row(*row, on_role=self.role_changed.emit))
        self._files_title.setVisible(self._show_rows and bool(rows))
        self.summary.setText(summary)
        self.summary.setVisible(bool(summary))


def role_combo(role: str) -> QComboBox:
    combo = style_dropdown(QComboBox())
    combo.setObjectName("retailRoleCombo")
    combo.addItem("Wybierz rolę", "")
    for key, label in ROLE_LABELS.items():
        combo.addItem(label[:1].upper() + label[1:], key)
    combo.addItem("Pomiń", SKIP_ROLE)  # notka pod wierszem mówi, dlaczego (duplikat)
    combo.setCurrentIndex(max(0, combo.findData(role)))
    combo.setToolTip("Co pokazuje to zdjęcie. Od tego zależy końcówka nazwy pliku (_g, _t ...).\n"
                     "„Pomiń” = tego pliku nie zapiszę (np. mniejsza kopia tej samej strony).")
    return combo


def file_row(path: Path, role: str, target: str, problem: str, note: str, *, on_role,
             on_remove=None, compact: bool = False) -> QWidget:
    """Wiersz pliku: nazwa, lista ról, nazwa wynikowa, pod spodem problem (czerwony) albo notka (szara).
    ``compact`` = jedna linia (wiersz listy plików trybu prostego, z własnym ✕)."""
    box = QWidget()
    box.setObjectName("retailFileRow")
    v = QVBoxLayout(box)
    v.setContentsMargins(*((8, 7, 4, 7) if compact else (0, 0, 0, 0)))
    v.setSpacing(4)
    name = _ElideLabel(path.name)
    name.setObjectName("retailFileName")
    h = QHBoxLayout()
    h.setSpacing(10)
    if compact:
        h.addWidget(name, 1)
    else:
        v.addWidget(name)
    combo = role_combo(role)
    combo.setFixedWidth(combo.fontMetrics().horizontalAdvance("Rich content 4") + 56)
    combo.setFixedHeight(BTN_H)
    combo.currentIndexChanged.connect(lambda _i, c=combo: on_role(path, c.currentData()))
    h.addWidget(combo)
    out = QLabel(target)
    out.setObjectName("retailTarget")
    out.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if compact:
        out.setMinimumWidth(out.fontMetrics().horizontalAdvance("5903548004897_rc4.png") + 8)
    h.addWidget(out, 0 if compact else 1)
    if on_remove is not None:
        btn = QPushButton()
        btn.setObjectName("iconBtn")
        set_themed_icon(btn, icon_clear_gray)  # krzyżyk rysowany (glifu ✕ nie ma we wszystkich czcionkach)
        btn.setFixedSize(BTN_H, BTN_H)
        btn.setToolTip("Usuń z listy (pliku na dysku nie rusza)")
        btn.clicked.connect(lambda _=False: on_remove(path))
        mark_quiet(btn)
        h.addWidget(btn)
    v.addLayout(h)
    if problem or note:
        msg = QLabel(problem or note)
        msg.setObjectName("retailVerdict" if problem else "retailNote")
        msg.setWordWrap(True)
        if problem:
            _set_state(msg, "bad")
        v.addWidget(msg)
    return box
