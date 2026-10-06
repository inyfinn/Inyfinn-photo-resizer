"""Polskie QMessageBox — czytelne, spójne z motywem aplikacji."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QLabel, QMessageBox, QWidget

from inyfinn_resizer.app.dialogs.base_dialog import DIALOG_ROW_GAP
from inyfinn_resizer.app.widgets.layout_helpers import mark_quiet, pin_button_min_widths
from inyfinn_resizer.app.widgets.section_icons import message_box_pixmap

_KIND_BY_ICON = {
    QMessageBox.Icon.Question: "question",
    QMessageBox.Icon.Warning: "warning",
    QMessageBox.Icon.Critical: "critical",
    QMessageBox.Icon.Information: "information",
}


# Do tej szerokości tekst komunikatu jest w jednym wierszu; dłuższy Qt zawija sam (próg zawijania Qt to 500 px
# szerokości układu, a ikona i marginesy to ponad 20 px — przy minimum 480 układ zawsze przekracza próg i zawija).
# Niższy limit (420) zostawiał tekst 421–500 px bez zawijania i ucięty.
MSGBOX_TEXT_MAX_W = 480


class AppMessageBox(QMessageBox):
    """Komunikat, którego rozmiar liczymy w chwili pokazania — z końcowymi czcionkami i napisami przycisków.

    Qt ustala rozmiar okna w ``setVisible(True)`` i przedtem go nie zna. Minimum tekstu ustawione przy budowie
    (przed nałożeniem motywu albo przed zmianą tekstu) było już nieaktualne, gdy wersaliki i nowe czcionki
    poszerzyły napisy — tekst „Plik … już istr” był ucięty. Dlatego ``_finish_box`` wołamy tuż przed pokazaniem.
    """

    vertical_buttons = False  # dłuższe napisy przycisków jeden pod drugim (ustawiane przez wywołującego)
    icon_kind = "information"  # question / warning / critical / information — ikona z design systemu

    def set_kind(self, icon: QMessageBox.Icon) -> None:
        """Rodzaj ikony wg ``QMessageBox.Icon``; sam obrazek rysujemy przy pokazaniu (kolory aktualnego motywu)."""
        self.icon_kind = _KIND_BY_ICON.get(icon, "information")

    def setVisible(self, visible: bool) -> None:  # noqa: N802 (Qt API)
        if visible:
            # Kwadrat z promieniem 4 i znakiem (DS) zamiast systemowego trójkąta/koła; nowy obraz po każdej zmianie motywu.
            self.setIconPixmap(message_box_pixmap(self.icon_kind, size=32))
            _finish_box(self, vertical=self.vertical_buttons)
        super().setVisible(visible)


def _polish_buttons(box: QMessageBox) -> None:
    mapping = {
        QMessageBox.Yes: ("Tak", "primaryBtn"),
        QMessageBox.No: ("Nie", "btnSecondary"),
        QMessageBox.Ok: ("OK", "primaryBtn"),
        QMessageBox.Cancel: ("Anuluj", "btnLink"),
        QMessageBox.Close: ("Zamknij", "btnLink"),
    }
    for role, (text, obj_name) in mapping.items():
        btn = box.button(role)
        if btn:
            btn.setText(text)
            btn.setObjectName(obj_name)
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(88)


def _finish_box(box: QMessageBox, *, vertical: bool = False) -> None:
    """Przyciski nie są ściskane poniżej napisu (wersaliki DS 2.0 są szersze) i mają odstęp ≥ 8 px."""
    pin_button_min_widths(box)
    # Styl nadaje `QMessageBox QLabel` min-width 320 px: etykieta z ikoną rosła do 320 px, a tekst miał minimum
    # niezależne od swojej treści (Qt myślał, że się mieści — i ucinał go albo ikona nachodziła na tekst na wąskim
    # ekranie). Zdejmujemy to minimum na poziomie widżetu; Qt liczy wtedy szerokość z treści i zawija tekst sam.
    for lbl in box.findChildren(QLabel):
        lbl.setStyleSheet("QLabel { min-width: 0px; }")
    icon = box.findChild(QLabel, "qt_msgboxex_icon_label")
    if icon is not None:
        icon.ensurePolished()
        icon.setMinimumWidth(icon.sizeHint().width())
    text = box.findChild(QLabel, "qt_msgbox_label")
    if text is not None:
        # Minimum tekstu = jego szerokość bez zawijania (do MSGBOX_TEXT_MAX_W); dłuższy tekst Qt zawinie sam.
        text.ensurePolished()
        text.setWordWrap(False)
        text.setMinimumWidth(min(text.sizeHint().width(), MSGBOX_TEXT_MAX_W))
    bb = box.findChild(QDialogButtonBox)
    if bb is not None and vertical:
        # Dłuższe napisy przycisków (wersaliki) nie mieszczą się obok siebie na wąskim ekranie — jeden pod drugim.
        bb.setOrientation(Qt.Orientation.Vertical)
    if bb is not None and bb.layout() is not None:
        bb.layout().setSpacing(DIALOG_ROW_GAP)


def _make_box(
    parent: QWidget | None,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButton,
) -> QMessageBox:
    box = AppMessageBox(parent)
    box.set_kind(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
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
    box = AppMessageBox(parent)
    box.set_kind(QMessageBox.Icon.Warning)
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
    # S13: jeden zielony (Tak), jeden z obrysem (Nie), pozostałe ciche.
    for btn in (btn_yes_all, btn_no_all):
        mark_quiet(btn)
    box.vertical_buttons = True
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
    box = AppMessageBox(parent)
    box.set_kind(QMessageBox.Icon.Question)
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
    btn_cancel = box.addButton("Anuluj", QMessageBox.RejectRole)
    _polish_buttons(box)
    btn_cancel.setObjectName("btnLink")
    btn_cancel.setMinimumHeight(36)
    if btn_single:
        btn_single.setObjectName("primaryBtn")
        btn_single.setMinimumHeight(36)
    if btn_beside:
        btn_beside.setObjectName("btnSecondary")
        btn_beside.setMinimumHeight(36)
    box.vertical_buttons = True
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
    box = AppMessageBox(parent)
    box.set_kind(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    _polish_buttons(box)
    box.exec()
