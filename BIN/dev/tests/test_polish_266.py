"""2.6.6: poprawki po 2.6.5 — wielkość liter przycisków (S18), lista plików w jasnych motywach (S14), karty bez obrysu
(S13), odstęp między kolumnami ≥ 12 px, szerokości kolumn okna wyników, ścieżka podglądu łamana po separatorach."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QFont, QTextLayout, QTextOption
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFrame, QPushButton

from inyfinn_resizer.app import themes
from inyfinn_resizer.app.themes import typography
from inyfinn_resizer.app.widgets.layout_helpers import breakable_path, mark_quiet
from inyfinn_resizer.app.window_fit import DENSITIES

from test_window_fit import make_window  # noqa: F401  (fixture: okno z zadanym ekranem)

ZJ = "dobra-kaloria-zielen-jasny"
ZC = "dobra-kaloria-zielen-ciemny"
KJ = "dobra-kaloria-krem-jasny"
KC = "dobra-kaloria-krem-ciemny"
LIGHT = (ZJ, KJ)
DARK = (ZC, KC)
ALL = (ZJ, ZC, KJ, KC)
UP = QFont.Capitalization.AllUppercase


@pytest.fixture()
def app():
    qapp = QApplication.instance() or QApplication([])
    themes.apply_theme(qapp, ZJ)
    return qapp


def _is_upper(w) -> bool:
    return w.font().capitalization() == UP


def _shown_button(app, name: str, text: str = "Napis", *, quiet: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName(name)
    if quiet:
        mark_quiet(b)
    b.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    b.show()
    for _ in range(3):
        app.processEvents()
    return b


# ——— (a) wielkość liter przycisków ———


@pytest.mark.parametrize(
    "name,quiet,expected",
    [
        ("primaryBtn", False, True),  # zielone główne
        ("footerPrimary", False, True),
        ("saveChoicePrimary", False, True),
        ("updateDialogAction", False, True),
        ("updateToastInstall", False, True),
        ("updateStatusInstall", False, True),
        ("btnSecondary", False, True),  # jedyny z obrysem w grupie
        ("saveChoiceOutline", False, True),
        ("btnBrowse", False, True),  # „Wybierz folder…” w trybie prostym: jedyny obrys w grupie
        ("", False, True),  # domyślny przycisk (obrys)
        ("btnSecondary", True, False),  # ciche: „Przywróć preset”, „Resetuj…”
        ("btnBrowse", True, False),  # „Przeglądaj”
        ("toolBtn", False, False),  # „Dodaj pliki”, „Dodaj folder”, „Usuń”, „Wyczyść”
        ("btnUpdatePath", False, False),  # „Aktualizuj ścieżkę”
        ("iconBtn", False, False),
        ("footerConvert", False, False),  # żółty „Konwertuj”
        ("btnLink", False, False),  # linki
        ("footerClose", False, False),
        ("updateToastLater", False, False),
        ("updateStatusCancel", False, False),
        ("formatChip", False, False),
        ("cropAnchorBtn", False, False),
    ],
)
def test_wants_uppercase_per_button_class(app, name, quiet, expected):
    b = QPushButton("Napis")
    b.setObjectName(name)
    if quiet:
        mark_quiet(b)
    assert typography.wants_uppercase(b) is expected
    shown = _shown_button(app, name, quiet=quiet)
    assert _is_upper(shown) is expected
    assert shown.text() == "Napis"  # tekst w kodzie bez zmian


def test_button_name_set_after_show_follows_toolbtn_iconbtn_switch(app):
    """Rząd nad listą plików przełącza ``toolBtn`` ↔ ``iconBtn`` w trakcie życia; ``btnSecondary`` → ``toolBtn`` traci
    wersaliki, powrót je odzyskuje (decyzja z BIEŻĄCEGO stanu przy każdym Polish/Show/FontChange)."""
    b = _shown_button(app, "btnSecondary")
    assert _is_upper(b)
    b.setObjectName("toolBtn")
    b.style().unpolish(b)
    b.style().polish(b)  # to samo robi MainWindow._set_tool_mode
    for _ in range(3):
        app.processEvents()
    assert not _is_upper(b)
    b.setObjectName("btnSecondary")
    b.style().unpolish(b)
    b.style().polish(b)
    for _ in range(3):
        app.processEvents()
    assert _is_upper(b)


def test_quiet_set_after_show_removes_caps_and_unset_restores_them(app):
    b = _shown_button(app, "btnSecondary", "Przywróć preset")
    assert _is_upper(b)
    mark_quiet(b)  # ustawione PO pokazaniu (DynamicPropertyChange)
    for _ in range(3):
        app.processEvents()
    assert not _is_upper(b)
    b.setProperty("quiet", False)
    for _ in range(3):
        app.processEvents()
    assert _is_upper(b)


def test_quiet_buttons_by_name_match_the_stylesheet_list():
    """Przyciski ciche po nazwie w typografii = selektory ``QUIET_BUTTONS`` w motywie (jedno źródło prawdy: S13)."""
    by_name = {s.split("#", 1)[1] for s in themes.QUIET_BUTTONS if s.startswith("QPushButton#")}
    assert by_name <= typography.BUTTON_NO_UPPERCASE
    assert by_name == {"toolBtn", "btnUpdatePath"}


def _real_window_texts(win) -> dict[str, tuple[bool, bool]]:
    """tekst widocznego przycisku → (chce wersaliki wg reguły, ma wersaliki)."""
    return {b.text(): (typography.wants_uppercase(b), _is_upper(b)) for b in win.findChildren(QPushButton)
            if b.isVisible() and b.text()}


_LOWER_ADVANCED = {"Przywróć preset", "Aktualizuj ścieżkę", "Przeglądaj", "Konwertuj", "Dodaj pliki", "Dodaj folder",
                   "Usuń", "Wyczyść", "Zamknij"}
_UPPER_ADVANCED = {"Tryb prosty", "Ustawienia…"}
_LOWER_SIMPLE = {"Dodaj pliki", "Dodaj folder", "Wyczyść", "Konwertuj"}
_UPPER_SIMPLE = {"Zaawansowany tryb", "Wybierz folder…"}


@pytest.mark.parametrize("mode", ["advanced", "simple"])
def test_real_window_casing_matches_the_rule_also_after_real_theme_toggles(make_window, mode):  # noqa: F811
    """Napisy w prawdziwym oknie: ciche i żółty CTA zwykłą wielkością liter, zielone i jedyny obrys wersalikami —
    na starcie i po KAŻDYM kliknięciu prawdziwego przełącznika motywu (nałożenie arkusza od nowa nie może ani
    zgubić wersalików, ani ich dorobić cichym przyciskom)."""
    make, qapp, _ = make_window
    themes.apply_theme(qapp, ZJ)
    win = make(QRect(0, 0, 1920, 1152), mode=mode, fmt="png")
    win._set_theme(ZJ)
    for _ in range(4):
        qapp.processEvents()
    lower, upper = (_LOWER_ADVANCED, _UPPER_ADVANCED) if mode == "advanced" else (_LOWER_SIMPLE, _UPPER_SIMPLE)

    def check() -> dict:
        state = _real_window_texts(win)
        for text, (want, has) in state.items():
            assert want == has, (mode, text, want, has)
        for text in lower & set(state):
            assert state[text] == (False, False), (mode, text)
        for text in upper & set(state):
            assert state[text] == (True, True), (mode, text)
        assert lower & set(state) and upper & set(state), (mode, sorted(state))
        return {k: v for k, v in state.items()}

    try:
        before = check()
        toggle = win._theme_toggle
        for expected in (ZC, ZJ):
            QTest.mouseClick(toggle, Qt.MouseButton.LeftButton, pos=QPoint(toggle.width() // 2, toggle.height() // 2))
            for _ in range(6):
                qapp.processEvents()
            assert themes.current_theme() == expected
            assert check() == before
    finally:
        themes.apply_theme(qapp, ZJ)


# ——— (b) lista plików w jasnych motywach ———


@pytest.mark.parametrize("theme", ALL)
def test_file_list_alternate_matches_list_background_in_light_only(theme):
    t = themes._THEME_TOKENS[theme]
    list_bg = t["@BG_PANEL_ALT@"]
    if theme in LIGHT:
        assert t["@LIST_ALT_BG@"] == list_bg  # jeden poziom tła w panelu: białe wiersze, bez pasów
        assert t["@LIST_ROW_LINE@"] == f"1px solid {t['@SEP@']}"
    else:
        assert t["@LIST_ALT_BG@"] == t["@BG_ZEBRA@"] != list_bg  # ciemne zostają przy pasach zebra
        assert t["@LIST_ROW_LINE@"] == "none"
    assert t["@ROW_HOVER@"] != list_bg and t["@ROW_SELECTED_BG@"] != list_bg  # najechanie i zaznaczenie widać


def _row_color(tree, index: int):
    item = tree.topLevelItem(index)
    rect = tree.visualItemRect(item)
    image = tree.viewport().grab().toImage()
    # prawy skraj wiersza, poza tekstem i znaczkiem ✕ (✕ siedzi w strefie 26 px przy prawej krawędzi — bierzemy 3 px od niej)
    return image.pixelColor(image.width() - 3, rect.top() + rect.height() // 2)


@pytest.mark.parametrize("theme", (ZJ, KJ, ZC, KC))
def test_file_list_rows_are_plain_in_light_and_striped_in_dark(make_window, theme):  # noqa: F811
    make, qapp, _ = make_window
    themes.apply_theme(qapp, theme)
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    win._set_theme(theme)
    from PySide6.QtWidgets import QTreeWidgetItem

    tree = win.input_tree
    assert tree.topLevelItemCount() == 0
    for i in range(4):
        tree.addTopLevelItem(QTreeWidgetItem([f"plik-{i}.png", "1 KB"]))
    tree.setCurrentItem(None)
    tree.clearSelection()
    for _ in range(4):
        qapp.processEvents()
    t = themes._THEME_TOKENS[theme]
    c1, c2 = _row_color(tree, 1), _row_color(tree, 2)
    try:
        if theme in LIGHT:
            assert c1 == c2  # brak pasów
            assert c1.name().lower() == t["@BG_PANEL_ALT@"].lower()
        else:
            assert c1 != c2  # pasy zebra w ciemnych
    finally:
        themes.apply_theme(qapp, ZJ)


# ——— (c) karty bez obrysu ———


@pytest.mark.parametrize("theme", ALL)
def test_help_cards_and_preview_have_no_outline(theme):
    qss = themes.render_qss(theme)
    rules = re.findall(r"([^{}]+)\{([^}]*)\}", qss)
    seen = set()
    for sel, body in rules:
        for name in ("#helpGuideSection", "#previewBox", "#dialogCard", "#dialogPanel"):
            if name not in sel:
                continue
            seen.add(name)
            for m in re.finditer(r"(?<![-\w])border\s*:\s*([^;]+);", body):
                assert m.group(1).strip() == "none", (name, sel.strip(), m.group(1))
    assert {"#helpGuideSection", "#previewBox"} <= seen


def test_help_dialog_cards_are_outline_free_and_scroll_not_clip(app):
    from PySide6.QtWidgets import QScrollArea

    from inyfinn_resizer.app.dialogs.help_guide import HelpGuideDialog

    dlg = HelpGuideDialog()
    try:
        dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        dlg.show()
        for _ in range(4):
            app.processEvents()
        scroll = dlg.findChild(QScrollArea, "helpGuideScroll")
        bar = scroll.verticalScrollBar()
        assert bar.maximum() > 0  # treść dłuższa niż okno przewija się (to obszar przewijania, nie ucięcie)
        bar.setValue(bar.maximum())
        for _ in range(3):
            app.processEvents()
        cards = dlg.findChildren(QFrame, "helpGuideSection")
        assert len(cards) >= 8
        last = cards[-1]
        bottom = last.mapTo(scroll.viewport(), QPoint(0, last.height())).y()
        assert bottom <= scroll.viewport().height()  # po przewinięciu do końca ostatnia karta jest w całości
        for card in cards:
            # brak obrysu: lewy skrajny piksel karty jest przezroczysty albo biały jak okno
            img = card.grab().toImage()
            for y in (img.height() // 2, img.height() - 2):
                c = img.pixelColor(0, y)
                assert c.alpha() == 0 or c.name().lower() == "#ffffff", (card.objectName(), y, c.name())
    finally:
        dlg.close()


# ——— (d) odstęp między kolumnami ———


def test_density_column_gap_is_at_least_12_and_vertical_gap_unchanged():
    assert [d.col_gap for d in DENSITIES] == [16, 12, 12]
    assert [d.card_gap for d in DENSITIES] == [16, 12, 8]  # pion bez zmian: wysokość okna się nie zmienia
    assert all(d.col_gap >= 12 and d.col_gap >= d.card_gap for d in DENSITIES)


@pytest.mark.parametrize("level", [0, 1, 2])
def test_main_window_column_gap_at_every_density(make_window, level):  # noqa: F811
    make, qapp, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    win._apply_density(level)
    for _ in range(3):
        qapp.processEvents()
    d = DENSITIES[level]
    assert win._main_splitter.handleWidth() == d.col_gap >= 12
    grid = win._bento_grid
    assert grid.horizontalSpacing() == d.col_gap >= 12
    assert grid.verticalSpacing() == d.card_gap  # pion = odstęp kart (8 na poziomie 2)
    assert win._left_column.layout().spacing() == d.card_gap


# ——— (f) okno wyników i ścieżka podglądu ———

# Szerokości kolumn nazw plików w oknie wyników 1018 px zmierzone na kodzie 2.6.4 (becba97) przy identycznych danych
# i PUSTYCH ustawieniach (domyślna kolumna „Status” 120 px): „Plik wejściowy” 147 px, „Plik wyjściowy” 146 px
# (2.6.5: 139 / 138; 2.6.6: 153 / 152). Przy zapisanym wąskim „Statusie” (72 px) tak samo: 171/170 → 163/162 → 177/176.
RESULTS_NAME_COLS_264 = (147, 146)


def test_results_name_columns_are_not_narrower_than_in_264(app, monkeypatch):
    from inyfinn_resizer.app.dialogs.base_dialog import AppDialog
    from inyfinn_resizer.app.dialogs.results_dialog import _COL_IN, _COL_LP, _COL_OUT, ResultsDialog
    from inyfinn_resizer.core.job import JobResult, JobSpec, JobStatus

    monkeypatch.setattr(AppDialog, "fit_to_screen", lambda self, available=None: None)  # bez przycinania do ekranu testu
    names = ["CIASTO-SLIWKOWE.png", "KWIAT-SLIWKI-1.jpg", "KWIAT-SLIWKI-2.jpg", "BANER-KATEGORIA.png", "PACZKA-FRONT.png"]
    results = []
    for i, n in enumerate(names):
        p = Path("C:/tmp") / n
        spec = JobSpec(input_path=p, output_path=p.with_suffix(".avif"), output_format="avif")
        results.append(JobResult(job=spec, status=JobStatus.OK, message="", old_bytes=1_200_000 + i * 90_000,
                                 new_bytes=180_000 + i * 21_000))
    dlg = ResultsDialog(results, 12.4)
    try:
        dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        dlg.show()
        for _ in range(5):
            app.processEvents()
        assert dlg.width() == 1018
        t = dlg.table
        assert t.columnWidth(_COL_LP) == 44
        assert t.columnWidth(_COL_IN) >= RESULTS_NAME_COLS_264[0]
        assert t.columnWidth(_COL_OUT) >= RESULTS_NAME_COLS_264[1]
    finally:
        dlg.close()


def test_breakable_path_keeps_drive_prefix_together_and_text_recoverable():
    path = r"C:\Users\uzytkownik.testowy\AppData\Local\Temp\inyfinn-capture-samples"
    out = breakable_path(path)
    assert out.replace("\u200b", "").replace("\u2060", "") == path  # sama zawartość się nie zmienia
    assert out.startswith("C:\u2060\\")  # zakaz łamania między „C:” a „\”
    assert "C:\u200b" not in out and "\\\u200bUsers" in out  # okazja do łamania dopiero po „\”
    unc = breakable_path(r"\\serwer\udzial\folder")
    assert unc.startswith("\\\\") and unc.replace("\u200b", "") == r"\\serwer\udzial\folder"
    assert breakable_path("/home/u/zdjecia") == "/\u200bhome/\u200bu/\u200bzdjecia"


def _wrapped_lines(font: QFont, text: str, width: int) -> list[str]:
    layout = QTextLayout(text, font)
    opt = QTextOption()
    opt.setWrapMode(QTextOption.WrapMode.WordWrap)
    layout.setTextOption(opt)
    layout.beginLayout()
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(width)
    layout.endLayout()
    return [text[layout.lineAt(i).textStart():layout.lineAt(i).textStart() + layout.lineAt(i).textLength()]
            for i in range(layout.lineCount())]


@pytest.mark.parametrize("width", [70, 90, 120, 160, 220])
def test_preview_path_never_wraps_inside_the_drive_prefix(app, width):
    font = app.font()
    path = r"C:\Users\uzytkownik.testowy\AppData\Local\Temp\inyfinn-capture-samples"
    lines = _wrapped_lines(font, breakable_path(path), width)
    clean = [ln.replace("\u200b", "").replace("\u2060", "") for ln in lines]
    assert len(lines) > 1
    assert not clean[0].rstrip().endswith("C:"), clean  # 2.6.5 łamało właśnie tu
    assert clean[0].startswith("C:\\")
    assert "".join(clean) == path
    # żadna linia (poza pierwszą) nie zaczyna się od „\” — separator zostaje na końcu poprzedniej
    assert all(not ln.startswith("\\") for ln in clean[1:]), clean
    # stary tekst łamał po „C:” przy wąskiej etykiecie — dowód, że test coś sprawdza
    assert _wrapped_lines(font, path, 70)[0].rstrip().endswith("C:")


def test_preview_label_shows_breakable_path(make_window, tmp_path):  # noqa: F811
    from PIL import Image
    from PySide6.QtWidgets import QTreeWidgetItem

    make, qapp, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    img = tmp_path / "okno.png"
    Image.new("RGB", (8, 8), (10, 120, 60)).save(img)
    win._add_path_to_queue(img)
    item = win.input_tree.topLevelItem(0)
    assert isinstance(item, QTreeWidgetItem)
    win.input_tree.setCurrentItem(item)
    for _ in range(3):
        qapp.processEvents()
    text = win.size_info.text()
    assert text.replace("\u200b", "").replace("\u2060", "").endswith(str(img.parent))
    assert not win.size_info.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse  # kopiowanie nie dotyczy
    if re.match(r"^[A-Za-z]:", str(img.parent)):
        assert f"{str(img.parent)[:2]}\u2060\\" in text
