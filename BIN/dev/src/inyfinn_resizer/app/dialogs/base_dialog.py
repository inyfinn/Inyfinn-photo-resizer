"""Bazowy dialog — polskie przyciski, spójny motyw."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton


def polish_dialog_buttons(box: QDialogButtonBox) -> None:
    mapping = {
        QDialogButtonBox.Ok: "OK",
        QDialogButtonBox.Cancel: "Anuluj",
        QDialogButtonBox.Close: "Zamknij",
        QDialogButtonBox.Reset: "Resetuj",
        QDialogButtonBox.Apply: "Zastosuj",
        QDialogButtonBox.Save: "Zapisz",
        QDialogButtonBox.Open: "Otwórz",
    }
    for role, text in mapping.items():
        btn = box.button(role)
        if btn:
            btn.setText(text)
            if role == QDialogButtonBox.Ok:
                btn.setObjectName("primaryBtn")
            elif role in (QDialogButtonBox.Cancel, QDialogButtonBox.Close):
                btn.setObjectName("btnLink")  # anulowanie i powrót = link (design system)
            else:
                btn.setObjectName("btnSecondary")


class AppDialog(QDialog):
    """Dialog dziedziczący stylesheet aplikacji."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appDialog")

    def polish_button(self, btn: QPushButton, *, primary: bool = False, link: bool = False) -> None:
        btn.setObjectName("primaryBtn" if primary else "btnLink" if link else "btnSecondary")
        btn.setMinimumHeight(36)
