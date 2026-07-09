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
            btn.setMinimumWidth(88)


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


def ask_confirm_delete(parent: QWidget | None, title: str, text: str) -> bool:
    return ask_yes_no(parent, title, text)


def ask_overwrite_inplace(
    parent: QWidget | None,
    *,
    filename: str,
    remaining: int,
) -> str | None:
    """Zwraca: yes | yes_all | no | no_all (anuluj całość) albo None."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle("Nadpisać plik?")
    extra = f"\n\nPozostało do sprawdzenia: {remaining}." if remaining > 1 else ""
    box.setText(
        f"Plik już istnieje w miejscu źródłowym:\n{filename}\n\n"
        f"Nadpisać go wynikiem konwersji?{extra}"
    )
    btn_yes = box.addButton("Tak", QMessageBox.YesRole)
    btn_yes_all = box.addButton("Tak dla wszystkich", QMessageBox.ActionRole)
    btn_no = box.addButton("Nie", QMessageBox.NoRole)
    btn_no_all = box.addButton("Nie dla wszystkich", QMessageBox.RejectRole)
    _polish_buttons(box)
    for btn, obj in (
        (btn_yes, "primaryBtn"),
        (btn_yes_all, "btnSecondary"),
        (btn_no, "btnSecondary"),
        (btn_no_all, "btnSecondary"),
    ):
        if btn:
            btn.setObjectName(obj)
            btn.setMinimumHeight(36)
    box.exec()
    clicked = box.clickedButton()
    if clicked is btn_yes:
        return "yes"
    if clicked is btn_yes_all:
        return "yes_all"
    if clicked is btn_no:
        return "no"
    if clicked is btn_no_all:
        return "no_all"
    return None


def ask_yes_no(parent: QWidget | None, title: str, text: str) -> bool:
    box = _make_box(parent, QMessageBox.Question, title, text, QMessageBox.Yes | QMessageBox.No)
    return box.exec() == QMessageBox.Yes


def ask_multi_folder_output(parent: QWidget | None) -> str | None:
    """Zwraca 'single', 'beside' albo None (anuluj)."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle("Gdzie zapisać zdjęcia?")
    box.setText(
        "Masz zdjęcia w kilku różnych folderach.\n\n"
        "Powiedz mi, gdzie mam zapisać gotowe pliki:"
    )
    btn_single = box.addButton("Wszystko do jednego folderu", QMessageBox.AcceptRole)
    btn_beside = box.addButton(
        "Stwórz foldery w miejscu docelowym plików",
        QMessageBox.ActionRole,
    )
    box.addButton("Anuluj", QMessageBox.RejectRole)
    _polish_buttons(box)
    if btn_single:
        btn_single.setObjectName("primaryBtn")
        btn_single.setMinimumHeight(36)
    if btn_beside:
        btn_beside.setObjectName("btnSecondary")
        btn_beside.setMinimumHeight(36)
    box.exec()
    clicked = box.clickedButton()
    if clicked is btn_single:
        return "single"
    if clicked is btn_beside:
        return "beside"
    return None


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
