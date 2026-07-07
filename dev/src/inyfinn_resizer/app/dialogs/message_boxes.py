"""Polskie QMessageBox — czytelne, spójne z motywem aplikacji."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def _polish_buttons(box: QMessageBox) -> None:
    mapping = {
        QMessageBox.Yes: ("Tak", "primaryBtn"),
        QMessageBox.No: ("Nie", "btnSecondary"),
        QMessageBox.Ok: ("OK", "primaryBtn"),
        QMessageBox.Cancel: ("Anuluj", "btnSecondary"),
        QMessageBox.Close: ("Zamknij", "btnSecondary"),
    }
    for role, (text, obj_name) in mapping.items():
        btn = box.button(role)
        if btn:
            btn.setText(text)
            btn.setObjectName(obj_name)
            btn.setMinimumHeight(36)


def _make_box(
    parent: QWidget | None,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButton,
) -> QMessageBox:
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    _polish_buttons(box)
    return box


def ask_yes_no(parent: QWidget | None, title: str, text: str) -> bool:
    box = _make_box(parent, QMessageBox.Question, title, text, QMessageBox.Yes | QMessageBox.No)
    return box.exec() == QMessageBox.Yes


def show_warning(parent: QWidget | None, title: str, text: str) -> None:
    _make_box(parent, QMessageBox.Warning, title, text, QMessageBox.Ok).exec()


def show_critical(parent: QWidget | None, title: str, text: str) -> None:
    _make_box(parent, QMessageBox.Critical, title, text, QMessageBox.Ok).exec()


def show_info(parent: QWidget | None, title: str, text: str) -> None:
    _make_box(parent, QMessageBox.Information, title, text, QMessageBox.Ok).exec()


def show_about(parent: QWidget | None, title: str, text: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    _polish_buttons(box)
    box.exec()
