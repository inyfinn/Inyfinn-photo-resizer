"""Okno dopasowane do ekranu (2.6.5, reguła G7) + odstęp 16 px między kartami + brak podpisu „Krok po kroku”.

Część czysta (``fit_window_size``) działa bez widżetów; testy okna podmieniają ``MainWindow._available_geometry``,
więc nie zależą od ekranu maszyny testowej.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMargins, QPoint, QRect, QSettings, QSize, Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from inyfinn_resizer.app import user_settings
from inyfinn_resizer.app.widgets.layout_helpers import CARD_GAP
from inyfinn_resizer.app.window_fit import DENSITIES, FALLBACK_FRAME, fit_window_size, inside

FRAME = QMargins(8, 31, 8, 8)  # oszacowana ramka Windows 10/11 w pikselach logicznych
MIN_CLIENT = QSize(1180, 700)
# Potrzebna wysokość klienta dla poziomów 0/1/2 (stan PNG z 2.6.5); szerokość = minimum układu.
NEED = [QSize(1084, 1023), QSize(1068, 951), QSize(1056, 895)]


def _fit(avail: QRect, *, saved: QSize | None = None, pos: QPoint | None = None, need=NEED):
    return fit_window_size(
        lambda lvl: need[lvl],
        avail,
        FRAME,
        saved=saved,
        preferred_w=1280,
        min_client=MIN_CLIENT,
        pos=pos,
    )


def _outer_rect(res) -> QRect:
    return QRect(res.pos, res.outer)


# ——— część czysta ———


@pytest.mark.parametrize(
    "w,h,level,scroll",
    [
        (1920, 1152, 0, False),  # 1920×1200, pasek zadań 48 px: wszystko na poziomie domyślnym
        (1920, 1032, 1, False),  # 1920×1080: zagęszczenie 1, bez przewijania
        (1536, 816, 2, True),  # 1536×864: nawet poziom 2 (895) się nie mieści → przewijanie w prawym panelu
        (1366, 720, 2, True),  # 1366×768
    ],
)
def test_level_and_scroll_per_screen(w, h, level, scroll):
    avail = QRect(0, 0, w, h)
    res = _fit(avail)
    assert res.level == level
    assert res.scroll is scroll
    assert avail.contains(_outer_rect(res)), (res.outer, res.pos)
    if scroll:
        assert res.client.height() == h - FRAME.top() - FRAME.bottom()  # wykorzystuje całą dostępną wysokość
    else:
        assert res.client.height() == NEED[level].height()


@pytest.mark.parametrize("w,h", [(1366, 720), (1536, 816), (1920, 1032), (1920, 1152), (1093, 566), (1000, 600)])
def test_never_exceeds_available_area(w, h):
    avail = QRect(0, 0, w, h)
    res = _fit(avail)
    assert res.outer.width() <= w and res.outer.height() <= h
    assert avail.contains(_outer_rect(res))
    assert res.min_client.width() <= w - FRAME.left() - FRAME.right()
    assert res.min_client.height() <= h - FRAME.top() - FRAME.bottom()


def test_available_area_offset_by_taskbar_on_top():
    avail = QRect(0, 48, 1920, 1032)  # pasek zadań u góry
    res = _fit(avail)
    assert avail.contains(_outer_rect(res))
    assert res.pos.y() >= 48


def test_saved_size_bigger_than_screen_is_ignored():
    avail = QRect(0, 0, 1366, 720)
    res = _fit(avail, saved=QSize(1900, 1400))
    assert res.client.width() == 1280  # zapisana szerokość się nie mieści → szerokość domyślna
    assert avail.contains(_outer_rect(res))
    assert res.client.height() <= 720 - 39


def test_saved_size_smaller_than_needed_never_lowers_height():
    avail = QRect(0, 0, 1920, 1152)
    res = _fit(avail, saved=QSize(1100, 700))
    assert res.client.height() == NEED[0].height()  # wysokość nie niższa niż potrzebna, gdy ekran ma miejsce
    assert res.client.width() == 1180  # zapisana 1100 < minimum okna 1180


def test_saved_size_larger_than_needed_but_fitting_is_honoured():
    avail = QRect(0, 0, 1920, 1152)
    res = _fit(avail, saved=QSize(1500, 1100))
    assert res.client == QSize(1500, 1100)
    assert avail.contains(_outer_rect(res))


def test_saved_height_fits_only_with_frame_taken_into_account():
    avail = QRect(0, 0, 1920, 1152)
    # 1113 = 1152 − 39 (pasek tytułu + ramka): ostatnia mieszcząca się wysokość klienta
    assert _fit(avail, saved=QSize(1280, 1113)).client.height() == 1113
    assert _fit(avail, saved=QSize(1280, 1114)).client.height() == NEED[0].height()


def test_current_position_is_kept_but_moved_onto_screen():
    avail = QRect(0, 0, 1920, 1152)
    res = _fit(avail, pos=QPoint(300, 200))
    assert avail.contains(_outer_rect(res))
    assert res.pos.y() + res.outer.height() <= 1152  # było 200 + 1062 > 1152 → przesunięte w górę
    res = _fit(avail, pos=QPoint(-50, -20))
    assert res.pos == QPoint(0, 0)


def test_centered_when_no_position():
    avail = QRect(0, 0, 1920, 1152)
    res = _fit(avail)
    assert res.pos.x() == (1920 - res.outer.width()) // 2


def test_inside_helper():
    avail = QRect(0, 0, 1000, 600)
    assert inside(avail, QSize(400, 300), QPoint(800, 500)) == QPoint(600, 300)
    assert inside(avail, QSize(400, 300), QPoint(-5, -5)) == QPoint(0, 0)


def test_density_levels_keep_gaps_and_paddings_readable():
    assert [d.card_gap for d in DENSITIES] == [CARD_GAP, 12, 8]
    assert [d.col_gap for d in DENSITIES] == [CARD_GAP, 12, 12]  # 2.6.6: odstęp między kolumnami ≥ 12 px
    assert DENSITIES[0].tile_pad == 20
    for d in DENSITIES:
        assert d.card_gap >= 8 and d.tile_pad >= 10 and d.tile_pad_top >= 10 - 0
        assert d.col_gap >= 12 and d.col_gap >= d.card_gap
    assert FALLBACK_FRAME.top() >= 20


# ——— okno ———


@pytest.fixture()
def make_window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / "settings.ini"
    monkeypatch.setattr(user_settings, "_settings", lambda: QSettings(str(path), QSettings.Format.IniFormat))
    from inyfinn_resizer.app.main_window import MainWindow

    windows = []

    def _make(avail: QRect | None = None, *, mode: str = "advanced", fmt: str = "png", show: bool = True):
        if avail is not None:
            monkeypatch.setattr(MainWindow, "_available_geometry", lambda self, r=avail: QRect(r))
        w = MainWindow()
        windows.append(w)
        if avail is not None:
            # Podmiana klasowa jest potrzebna tylko na czas konstruktora. Okno dostaje własny obszar, żeby kolejne
            # ``make(...)`` w tym samym teście (inny ekran) nie przestawiło dopasowania okien już utworzonych —
            # ich opóźnione dopasowania (timer 0) liczyłyby wtedy wg cudzego ekranu.
            w._available_geometry = lambda r=QRect(avail): QRect(r)  # type: ignore[method-assign]
        w._set_ui_mode(mode, mark_dirty=False)
        w.format_combo.set_selected([fmt])
        if avail is not None:
            w._fit_window(initial=True)
        if show:
            w.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
            w.show()
            for _ in range(4):
                app.processEvents()
        return w

    yield _make, app, path
    for w in windows:
        w.hide()
        w.deleteLater()


def _outer(w) -> QRect:
    fr = w._last_fit
    return QRect(fr.pos, fr.outer)


def test_workflow_hint_removed(make_window):
    make, _app, _ = make_window
    w = make(QRect(0, 0, 1920, 1152))
    assert not w.findChildren(QLabel, "workflowHint")
    assert not [lbl for lbl in w.findChildren(QLabel) if lbl.text().startswith("Krok po kroku")]


def test_one_card_gap_everywhere(make_window):
    make, _app, _ = make_window
    w = make(QRect(0, 0, 1920, 1152))
    assert CARD_GAP == 16
    assert w._density.level == 0
    assert w._main_splitter.handleWidth() == CARD_GAP
    grid = w._bento_grid
    assert grid.horizontalSpacing() == CARD_GAP and grid.verticalSpacing() == CARD_GAP
    assert w._left_column.layout().spacing() == CARD_GAP
    assert w._bento_left_lay.spacing() == CARD_GAP and w._bento_right_lay.spacing() == CARD_GAP
    assert w._settings_body.layout().spacing() == CARD_GAP
    assert w._simple_inner.layout().spacing() == CARD_GAP


def test_right_cards_start_level_with_list_card_and_columns_have_gap(make_window):
    make, _app, _ = make_window
    w = make(QRect(0, 0, 1920, 1152))
    list_tile = w._left_column.layout().itemAt(0).widget()
    first_right = w._bento_grid.itemAtPosition(0, 0).widget()
    top_list = list_tile.mapTo(w, QPoint(0, 0)).y()
    top_right = first_right.mapTo(w, QPoint(0, 0)).y()
    assert abs(top_list - top_right) <= 2, (top_list, top_right)
    gap = first_right.mapTo(w, QPoint(0, 0)).x() - list_tile.mapTo(w, QPoint(list_tile.width(), 0)).x()
    assert gap >= CARD_GAP - 1, gap


@pytest.mark.parametrize(
    "w,h",
    [(1366, 720), (1536, 816), (1920, 1032), (1920, 1152), (1093, 566)],
)
def test_window_fits_available_area_in_both_modes(make_window, w, h):
    make, app, _ = make_window
    avail = QRect(0, 0, w, h)
    win = make(avail, mode="simple")
    for mode in ("simple", "advanced", "simple", "advanced"):
        win._set_ui_mode(mode, mark_dirty=False)
        for _ in range(4):
            app.processEvents()
        assert avail.contains(_outer(win)), (mode, _outer(win))
        assert win.size() == win._last_fit.client, (mode, win.size(), win._last_fit.client)
        assert win.minimumWidth() <= w and win.minimumHeight() <= h


def test_footer_visible_and_no_horizontal_scroll_when_panel_scrolls(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1366, 720))
    assert win._density_scroll is True
    sa = win._settings_scroll
    assert not sa.horizontalScrollBar().isVisible()
    assert sa.verticalScrollBar().maximum() > 0  # prawy panel przewija się, treść jest osiągalna
    for btn in (win.convert_btn,):
        r = QRect(btn.mapTo(win, QPoint(0, 0)), btn.size())
        assert win.rect().contains(r)
    simple = make(QRect(0, 0, 1366, 720), mode="simple")
    r = QRect(simple.simple_convert_btn.mapTo(simple, QPoint(0, 0)), simple.simple_convert_btn.size())
    assert simple.rect().contains(r)  # „Konwertuj” w trybie prostym stoi pod obszarem przewijania


def test_no_vertical_scrollbar_needed_at_1920x1152_png(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced", fmt="png")
    sa = win._settings_scroll
    assert win._density.level == 0 and not win._density_scroll
    assert sa.verticalScrollBar().maximum() == 0
    assert sa.widget().height() <= sa.viewport().height()


def test_measured_need_matches_real_scrollbar_threshold(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced", fmt="png", show=True)
    need = win._measure_needed(0)
    win._fitting = True
    win.setMinimumSize(300, 300)
    win.resize(need.width() + 100, need.height())
    for _ in range(4):
        app.processEvents()
    assert win._settings_scroll.verticalScrollBar().maximum() == 0
    win.resize(need.width() + 100, need.height() - 12)
    for _ in range(4):
        app.processEvents()
    assert win._settings_scroll.verticalScrollBar().maximum() > 0


def test_format_change_refits_window_when_screen_has_room(make_window):
    make, app, _ = make_window
    avail = QRect(0, 0, 1920, 1152)
    win = make(avail, mode="advanced", fmt="png")
    assert win._density.level == 0
    before = win.height()
    win.format_combo.set_selected(["avif"])  # bez kafelka Kolory: wyższy układ (prawdziwa potrzeba ~1192 > 1113)
    for _ in range(6):
        app.processEvents()
    assert win.height() > before  # okno urosło, zamiast zostawić przewijanie
    assert win._settings_scroll.verticalScrollBar().maximum() == 0 or win._density_scroll
    assert avail.contains(_outer(win))
    win.format_combo.set_selected(["png"])
    for _ in range(6):
        app.processEvents()
    assert win._density.level == 0  # powrót do PNG przywraca odstępy domyślne (okno nie kurczy się samo)
    assert avail.contains(_outer(win))


def test_saved_splitter_does_not_disable_fit(make_window):
    make, app, path = make_window
    QSettings(str(path), QSettings.Format.IniFormat).setValue("ui/splitter", [560, 720])
    win = make(QRect(0, 0, 1366, 720), mode="advanced", show=False)
    assert win._geometry_restored  # podział był zapisany…
    assert win._last_fit is not None  # …a okno i tak dopasowane do ekranu
    assert QRect(0, 0, 1366, 720).contains(_outer(win))


def test_saved_user_size_honoured_only_when_it_fits(make_window):
    make, app, path = make_window
    s = QSettings(str(path), QSettings.Format.IniFormat)
    s.setValue("ui/window_size_advanced", [1500, 1100])
    s.sync()
    big = make(QRect(0, 0, 1920, 1152), mode="advanced", show=False)
    assert big._last_fit.client == QSize(1500, 1100)
    small = make(QRect(0, 0, 1366, 720), mode="advanced", show=False)
    assert small._last_fit.client.width() <= 1366 - 16
    assert small._last_fit.client.height() <= 720 - 39
    assert small._last_fit.client != QSize(1500, 1100)


def test_manual_size_saved_on_close_but_not_auto_size(make_window):
    make, app, path = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    win.save_manual_window_size()
    assert user_settings.load_window_size("advanced") is None  # rozmiar ustawiony przez program się nie zapisuje
    win._fitting = True
    win.resize(1400, 1090)  # „ręczna” zmiana
    for _ in range(3):
        app.processEvents()
    win._fitting = False
    win.save_manual_window_size()
    assert user_settings.load_window_size("advanced") == QSize(1400, 1090)
    assert user_settings.load_window_size("simple") is None


def test_tool_buttons_keep_labels_until_even_two_per_row_does_not_fit(make_window):
    make, app, _ = make_window
    wide = make(QRect(0, 0, 1920, 1152))
    assert wide._tool_state == "row"
    assert all(b.text() == t and t for b, t in wide._left_tool_btns)
    narrow = make(QRect(0, 0, 1093, 566))
    one, two = narrow._tool_row_widths()
    width = narrow._left_tool_box.width()
    expected = "row" if width >= one else ("grid" if width >= two else "icons")
    assert narrow._tool_state == expected
    if expected != "icons":
        assert all(b.text() == t and t for b, t in narrow._left_tool_btns)


# ——— DS 2.0: napisy przycisków wersalikami są szersze — nic nie może zostać ucięte ———

def _uppercase_all_buttons(root) -> None:
    """Symulacja skóry 2.0.6 w teście: wersaliki + pogrubienie na każdym przycisku, który wg reguły (S18,
    ``typography.wants_uppercase``) ma wersaliki — główne zielone i jedyny obrys w grupie; ciche, CTA i linki nie."""
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QPushButton

    from inyfinn_resizer.app.themes.typography import wants_uppercase

    for b in root.findChildren(QPushButton):
        if not wants_uppercase(b):
            continue
        f = QFont(b.font())
        f.setCapitalization(QFont.Capitalization.AllUppercase)
        f.setWeight(QFont.Weight.Bold)
        b.setFont(f)
        b.updateGeometry()


def _clipped_buttons(root) -> list[tuple[str, int, int]]:
    from PySide6.QtWidgets import QPushButton

    return [
        (b.text(), b.width(), b.sizeHint().width())
        for b in root.findChildren(QPushButton)
        if b.isVisible() and b.text() and b.width() < b.sizeHint().width()
    ]


@pytest.mark.parametrize("mode", ["advanced", "simple"])
@pytest.mark.parametrize("avail", [QRect(0, 0, 1920, 1152), QRect(0, 0, 1093, 566)])
def test_uppercase_buttons_never_clipped_at_default_and_minimum_width(make_window, mode, avail):
    make, app, _ = make_window
    win = make(avail, mode=mode)
    _uppercase_all_buttons(win)
    win._fit_window(initial=False)
    for _ in range(4):
        app.processEvents()
    assert _clipped_buttons(win) == []
    assert avail.contains(_outer(win))
    assert win.minimumWidth() <= avail.width() and win.minimumHeight() <= avail.height()
    # najwęższe dozwolone okno
    win._fitting = True
    win.resize(win.minimumWidth(), win.height())
    win._fitting = False
    for _ in range(4):
        app.processEvents()
    assert _clipped_buttons(win) == [], (mode, win.size())
    if mode == "advanced":
        assert win._tool_state in ("row", "grid")  # napisy zostają (jeden rząd albo dwa), bez samych ikon
        assert all(b.text() for b, _t in win._left_tool_btns)
        assert not win._settings_scroll.horizontalScrollBar().isVisible()


def test_tool_row_state_follows_final_geometry_not_a_stale_width(make_window):
    """Regresja flaky testu: stan rzędu przycisków był liczony ze starej szerokości (przed ułożeniem kolumn) i nikt
    go potem nie poprawiał. Teraz stan wynika z szerokości kontenera przy KAŻDEJ jego zmianie — także gdy zmienia
    ją sam układ (``setSizes`` nie wysyła ``splitterMoved``)."""
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    one, two = win._tool_row_widths()
    total = sum(win._main_splitter.sizes())
    for left in (total - 700, one + 60, two + 40, two - 40, one + 60):
        win._main_splitter.setSizes([left, total - left])
        for _ in range(3):
            app.processEvents()
        width = win._left_tool_box.width()
        expected = "row" if width >= one else ("grid" if width >= two else "icons")
        assert win._tool_state == expected, (left, width, one, two, win._tool_state)
        assert all(bool(b.text()) == (expected != "icons") for b, _t in win._left_tool_btns)


def test_tool_row_wraps_to_two_rows_instead_of_dropping_labels(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    _uppercase_all_buttons(win)
    win._fit_window(initial=False)
    for _ in range(4):
        app.processEvents()
    one, two = win._tool_row_widths()
    assert two < one
    box = win._left_tool_box
    assert win._tool_state == ("row" if box.width() >= one else "grid")
    ys = {b.geometry().top() for b, _t in win._left_tool_btns}
    assert len(ys) == (1 if win._tool_state == "row" else 2)


def test_preset_delete_button_is_square_like_the_field_next_to_it(make_window):
    make, _app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    btn = win.delete_preset_btn
    assert btn.width() == btn.height()
    assert btn.height() >= win.size_combo.sizeHint().height()


def _dialog_builders():
    from inyfinn_resizer.app.changelog import ChangelogDialog
    from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
    from inyfinn_resizer.app.dialogs.custom_size_preset import CustomSizePresetDialog
    from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
    from inyfinn_resizer.app.dialogs.help_guide import HelpGuideDialog
    from inyfinn_resizer.app.dialogs.rename_dialog import RenameDialog
    from inyfinn_resizer.app.dialogs.results_dialog import ResultsDialog, WizResultsDialog
    from inyfinn_resizer.app.dialogs.simple_save_dialog import SimpleSaveChoiceDialog
    from inyfinn_resizer.app.dialogs.update_dialog import UpdateDialog
    from inyfinn_resizer.core.job import FormatOptions, RenameRule, ResizeOptions, TransformOptions

    return {
        "format": lambda: FormatSettingsDialog("gif", FormatOptions()),
        "advanced": lambda: AdvancedOptionsDialog(ResizeOptions(), TransformOptions()),
        "custom_size_preset": lambda: CustomSizePresetDialog(ResizeOptions(), TransformOptions()),
        "rename": lambda: RenameDialog(RenameRule(), [], None),
        "results": lambda: ResultsDialog([], 3.0),
        "wiz_results": lambda: WizResultsDialog([], 3.0),
        "simple_save": lambda: SimpleSaveChoiceDialog(None, file_count=5, folders=[]),
        "update": lambda: UpdateDialog(),
        "help": lambda: HelpGuideDialog(),
        "changelog": lambda: ChangelogDialog(),
    }


@pytest.mark.parametrize("avail", [QRect(0, 0, 1366, 720), QRect(0, 0, 1093, 566)])
def test_every_dialog_fits_the_available_area_and_has_ds_margins(make_window, avail):
    from inyfinn_resizer.app.dialogs.base_dialog import DIALOG_MARGIN

    _make, app, _ = make_window
    frame = (16, 39)  # ramka okna Windows 10/11: 8+8 poziomo, 31+8 pionowo
    for name, build in _dialog_builders().items():
        dlg = build()
        try:
            _uppercase_all_buttons(dlg)
            dlg.fit_to_screen(avail)
            dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
            dlg.show()
            for _ in range(3):
                app.processEvents()
            assert dlg.width() + frame[0] <= avail.width(), (name, dlg.size())
            assert dlg.height() + frame[1] <= avail.height(), (name, dlg.size())
            assert dlg.minimumWidth() + frame[0] <= avail.width() and dlg.minimumHeight() + frame[1] <= avail.height(), name
            m = dlg.layout().contentsMargins()
            assert (m.left(), m.top(), m.right(), m.bottom()) == (DIALOG_MARGIN,) * 4, name
            assert _clipped_buttons(dlg) == [], name
        finally:
            dlg.hide()
            dlg.deleteLater()


def test_dialog_button_boxes_keep_at_least_8px_between_buttons(make_window):
    from PySide6.QtWidgets import QDialogButtonBox

    _make, app, _ = make_window
    for name, build in _dialog_builders().items():
        dlg = build()
        try:
            for box in dlg.findChildren(QDialogButtonBox):
                assert box.layout().spacing() >= 8, name
        finally:
            dlg.deleteLater()


def test_message_box_text_and_icon_do_not_overlap(make_window):
    from PySide6.QtWidgets import QLabel, QMessageBox

    from inyfinn_resizer.app.dialogs.message_boxes import _make_box

    _make, app, _ = make_window
    box = _make_box(None, QMessageBox.Question, "Nadpisać plik?",
                    "Plik CIASTO-SLIWKOWE.avif już istnieje. Nadpisać go?", QMessageBox.Yes | QMessageBox.No)
    box.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    box.show()
    for _ in range(4):
        app.processEvents()
    icon = box.findChild(QLabel, "qt_msgboxex_icon_label")
    text = box.findChild(QLabel, "qt_msgbox_label")
    assert not icon.geometry().intersects(text.geometry())
    assert text.width() >= text.sizeHint().width()  # tekst w całości
    box.hide()
    box.deleteLater()


# ——— odstęp ikona ↔ napis (jedno miejsce: layout_helpers.set_themed_icon) i przyciski samą ikoną ———


def test_icon_text_gap_is_applied_in_one_place_and_survives_theme_refresh(make_window):
    from inyfinn_resizer.app.widgets.layout_helpers import ICON_TEXT_GAP, refresh_themed_icons

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    btn = win.update_output_btn  # napis + ikona
    assert btn.iconSize().width() == 16 + ICON_TEXT_GAP and btn.iconSize().height() == 16
    refresh_themed_icons(win)  # jak po zmianie motywu
    assert btn.iconSize().width() == 16 + ICON_TEXT_GAP
    assert 6 <= ICON_TEXT_GAP <= 8
    # przycisk samą ikoną nie dostaje odstępu
    assert win.delete_preset_btn.iconSize() == QSize(16, 16)


def test_icon_only_buttons_are_named_iconbtn_and_square(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    assert win.delete_preset_btn.objectName() == "iconBtn"
    assert win.simple_output_clear.objectName() == "iconBtn"
    assert win.delete_preset_btn.width() == win.delete_preset_btn.height()
    # rząd przycisków nad listą: w trybie samych ikon też kwadraty i iconBtn, a gap znika
    win._main_splitter.setSizes([280, sum(win._main_splitter.sizes()) - 280])
    for _ in range(4):
        app.processEvents()
    if win._tool_state == "icons":
        for b, _t in win._left_tool_btns:
            assert b.objectName() == "iconBtn" and b.width() == b.height() and not b.text()
            assert b.iconSize() == QSize(16, 16)
    else:
        assert all(b.objectName() == "toolBtn" for b, _t in win._left_tool_btns)


def test_advanced_options_sections_are_dialog_panels():
    from PySide6.QtWidgets import QFrame

    from inyfinn_resizer.app.dialogs.advanced_options import AdvancedSettingsPanel
    from inyfinn_resizer.core.job import ResizeOptions, TransformOptions

    app = QApplication.instance() or QApplication([])
    panel = AdvancedSettingsPanel(ResizeOptions(), TransformOptions())
    frames = [f for f in panel.findChildren(QFrame, "dialogPanel")]
    assert len(frames) == 4
    for f in frames:
        m = f.layout().contentsMargins()
        assert (m.left(), m.top(), m.right(), m.bottom()) == (20, 20, 20, 20)
        assert f.findChild(QLabel, "sectionTitle") is not None  # tytuł zostaje w środku
    panel.deleteLater()
    app.processEvents()


# ——— zakres „flush” układów (nie dotykamy nakładki ani ukrytych stron) ———


def test_layout_flush_scope_skips_overlay_hidden_page_and_update_widgets(make_window):
    from PySide6.QtWidgets import QScrollArea

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    overlay = win._conversion_overlay
    overlay_scroll = overlay.findChild(QScrollArea)
    assert overlay_scroll is not None

    def check(current_page, hidden_page):
        scope = set(win._layout_scope())
        assert overlay not in scope and overlay_scroll not in scope
        assert not any(overlay.isAncestorOf(w) for w in scope)
        assert current_page in scope
        assert hidden_page not in scope and not any(hidden_page.isAncestorOf(w) for w in scope)
        assert win._update_status not in scope  # ukryty pasek aktualizacji w pasku stanu
        assert win.menuWidget() in scope

    check(win._view_stack.widget(1), win._view_stack.widget(0))  # zaawansowany bieżący, prosty ukryty
    win._set_ui_mode("simple", mark_dirty=False)
    for _ in range(4):
        app.processEvents()
    check(win._view_stack.widget(0), win._view_stack.widget(1))  # i odwrotnie po przełączeniu


def test_overlay_scroll_area_is_not_activated_by_fit_and_shows_three_cards(make_window):
    """Nakładka nie dostaje „zapasowego” sizeHint 0×0 od dopasowania okna; 3 pliki = 3 karty bez paska."""
    from PySide6.QtWidgets import QScrollArea

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    win._set_ui_mode("simple", mark_dirty=False)
    win._set_ui_mode("advanced", mark_dirty=False)
    for _ in range(4):
        app.processEvents()
    overlay = win._conversion_overlay
    overlay.start_batch([("a.png", "png"), ("b.png", "png"), ("c.png", "png")])
    for _ in range(6):
        app.processEvents()
    scroll = overlay.findChild(QScrollArea)
    assert scroll.verticalScrollBar().maximum() == 0
    assert scroll.widget().height() <= scroll.viewport().height()
    overlay.hide()


# ——— S13: obrys tylko tam, gdzie wolno — w grupie przycisków najwyżej jeden z obrysem ———

_PRIMARY_NAMES = {"primaryBtn", "footerConvert", "footerPrimary", "saveChoicePrimary", "updateDialogAction"}
_LINK_NAMES = {"btnLink", "footerClose", "updateToastLater", "updateStatusCancel"}
_QUIET_NAMES = {"toolBtn", "btnUpdatePath"}  # ciche po nazwie obiektu (QSS Workera A)
_NOT_BUTTONS_IN_GROUP = {"formatChip", "cropAnchorBtn", "iconBtn"}


def _outlined_secondaries(root) -> dict:
    from PySide6.QtWidgets import QPushButton

    groups: dict = {}
    for b in root.findChildren(QPushButton):
        if not b.isVisibleTo(root) or not b.text():
            continue  # ukryte i same ikony (iconBtn) nie liczą się
        name = b.objectName()
        if name in _PRIMARY_NAMES or name in _LINK_NAMES or name in _QUIET_NAMES or name in _NOT_BUTTONS_IN_GROUP:
            continue
        if b.property("quiet") is True:
            continue
        groups.setdefault(b.parentWidget(), []).append(b.text())
    return {p: texts for p, texts in groups.items() if len(texts) > 1}


@pytest.mark.parametrize("mode", ["advanced", "simple"])
def test_main_window_has_at_most_one_outlined_secondary_per_button_group(make_window, mode):
    make, _app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode=mode)
    assert _outlined_secondaries(win) == {}
    if mode == "advanced":
        assert win.restore_retail_btn.property("quiet") is True
        assert win.update_output_btn.property("quiet") is True
        assert all(b.objectName() == "toolBtn" for b, _t in win._left_tool_btns)


def test_dialogs_have_at_most_one_outlined_secondary_per_button_group(make_window):
    _make, app, _ = make_window
    for name, build in _dialog_builders().items():
        dlg = build()
        try:
            dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
            dlg.show()
            for _ in range(3):
                app.processEvents()
            assert _outlined_secondaries(dlg) == {}, name
        finally:
            dlg.hide()
            dlg.deleteLater()


# ——— komunikaty liczone przy pokazaniu, ikony wierszy po zmianie motywu, tytuły Mindset z akcentami ———


def test_message_box_text_not_clipped_when_text_changes_after_build(make_window):
    """Minimum tekstu nie może zostać „zamrożone” przy budowie: tekst/czcionki zmieniają się przed pokazaniem."""
    from PySide6.QtWidgets import QLabel, QMessageBox

    from inyfinn_resizer.app.dialogs.message_boxes import _make_box

    _make, app, _ = make_window
    box = _make_box(None, QMessageBox.Question, "Nadpisać plik?", "Krótki.", QMessageBox.Yes | QMessageBox.No)
    box.setText("Plik CIASTO-SLIWKOWE-BARDZO-DLUGA-NAZWA.avif już istnieje w tym folderze. Nadpisać go?")
    box.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    box.show()
    for _i in range(4):
        app.processEvents()
    text = box.findChild(QLabel, "qt_msgbox_label")
    icon = box.findChild(QLabel, "qt_msgboxex_icon_label")
    assert not icon.geometry().intersects(text.geometry())
    if text.wordWrap():  # długi tekst: zawinięty, ale w całości (cała wysokość)
        assert text.height() >= text.heightForWidth(text.width())
    else:
        assert text.width() >= text.sizeHint().width()
    box.hide()
    box.deleteLater()


def test_row_icons_follow_theme_change(make_window, tmp_path):
    from PIL import Image

    from inyfinn_resizer.app.widgets.tool_icons import icon_folder_green, icon_image_file, icon_video_file

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    img = tmp_path / "a.png"
    Image.new("RGB", (8, 8), (200, 100, 50)).save(img)
    win._add_path_to_queue(img)
    win._refresh_simple_file_list()
    app.processEvents()

    row_icon = type(win)._row_icon  # ikony wierszy w rozmiarze ROW_ICON_PX (fabryka może, ale nie musi go przyjmować)

    def pm(icon):
        return icon.pixmap(20, 20).toImage()

    win._set_theme("dobra-kaloria-zielen-jasny")
    light_tree = pm(win.input_tree.topLevelItem(0).icon(0))
    assert light_tree == pm(row_icon(icon_image_file))
    win._set_theme("dobra-kaloria-zielen-ciemny")
    app.processEvents()
    dark_fresh = pm(row_icon(icon_image_file))
    assert pm(win.input_tree.topLevelItem(0).icon(0)) == dark_fresh  # drzewo
    assert pm(win.simple_file_list.item(0).icon()) == dark_fresh  # lista trybu prostego
    assert dark_fresh != light_tree  # motyw naprawdę zmienił kolor ikony (test nie jest pusty)
    win._set_theme("dobra-kaloria-zielen-jasny")  # przywróć dla kolejnych testów
    assert pm(icon_video_file()) is not None and pm(icon_folder_green()) is not None


@pytest.mark.parametrize("avail", [QRect(0, 0, 1920, 1152), QRect(0, 0, 1920, 1032), QRect(0, 0, 1536, 816)])
@pytest.mark.parametrize("mode", ["advanced", "simple"])
def test_mindset_titles_have_room_for_capital_accents(make_window, avail, mode):
    """Gęstość 0/1/2 (trzy ekrany) × oba tryby: nad ŚĆÓŻ zostaje miejsce w etykiecie tytułu (wysokość z metryk)."""
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import QLabel

    from inyfinn_resizer.app.themes.typography import DISPLAY_OBJECTS

    make, app, _ = make_window
    win = make(avail, mode=mode)
    titles = [lbl for lbl in win.findChildren(QLabel) if lbl.objectName() in DISPLAY_OBJECTS and lbl.isVisible() and lbl.text()]
    assert titles
    for lbl in titles:
        fm = QFontMetrics(lbl.font())
        accent_top = -fm.tightBoundingRect("ŚĆÓŻ").top()
        assert lbl.alignment() & Qt.AlignmentFlag.AlignBottom, lbl.text()
        assert lbl.height() - fm.descent() >= accent_top, (lbl.text(), lbl.height(), fm.descent(), accent_top)


def test_dialog_title_has_room_for_accents(make_window):
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import QLabel

    from inyfinn_resizer.app.dialogs.simple_save_dialog import SimpleSaveChoiceDialog

    _make, app, _ = make_window
    dlg = SimpleSaveChoiceDialog(None, file_count=5, folders=[])
    dlg.fit_to_screen(QRect(0, 0, 1366, 720))
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    for _i in range(3):
        app.processEvents()
    title = dlg.findChild(QLabel, "saveChoiceTitle")
    fm = QFontMetrics(title.font())
    assert title.height() - fm.descent() >= -fm.tightBoundingRect("ŚĆÓŻ").top()
    dlg.hide()
    dlg.deleteLater()


# ——— wzorzec „Stwórz prezentację” (2.6.5, runda zgodności): warianty kafelków, nadtytuły, linie, strefa upuszczania ———


def _tiles(win):
    from PySide6.QtWidgets import QFrame

    return [f for f in win.findChildren(QFrame, "bentoTile")]


@pytest.mark.parametrize("mode", ["advanced", "simple"])
def test_every_bento_tile_has_a_variant_and_only_one_grey_block_per_screen(make_window, mode):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode=mode)
    tiles = [t for t in _tiles(win) if t.isVisibleTo(win)]
    assert tiles
    for t in tiles:
        assert t.property("variant") in ("panel", "plain", "drop"), t.property("variant")
    grey = [t for t in tiles if t.property("variant") in ("panel", "drop")]
    assert len(grey) == 1, [(t.property("variant"), t.findChild(QLabel).text()) for t in grey]


def test_advanced_right_column_is_plain_with_eyebrow_titles_and_one_px_lines(make_window):
    from PySide6.QtWidgets import QFrame

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced", fmt="png")
    list_tile = win._left_column.layout().itemAt(0).widget()
    assert list_tile.property("variant") == "panel"
    assert win._left_column.layout().count() == 1  # podgląd leży w panelu listy, nie w drugim szarym bloku
    assert list_tile.findChild(QFrame, "groupSep") is not None  # linia nad podglądem, wewnątrz tego samego panelu
    assert list_tile.findChild(QWidget, "previewBlock") is not None
    for tile in (win._bento_grid.itemAtPosition(0, 0).widget(), win._bento_tile_bg, win._bento_tile_dims):
        assert tile.property("variant") == "plain"
        titles = [lbl for lbl in tile.findChildren(QLabel, "sectionTitle") if lbl.isVisible()]
        assert len(titles) == 1 and titles[0].text()
        assert tile.layout().contentsMargins() == QMargins(0, 0, 0, 0)  # treść równo z krawędzią kolumny
    seps = [s for s in win.findChildren(QFrame, "groupSep") if s.isVisible()]
    assert len(seps) >= 3  # między grupami: pod „Format i jakość”, nad „Zapis plików”, w kolumnie, przed podglądem
    for s in seps:
        assert s.height() == 1 and s.width() > 100


def test_simple_steps_are_numbered_in_separate_labels_and_keep_full_text_accessible(make_window):
    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="simple")
    numbers = [lbl.text() for lbl in win.findChildren(QLabel, "stepNumber") if lbl.isVisible()]
    assert numbers == ["1.", "2.", "3."]
    titles = {lbl.accessibleName() for lbl in win.findChildren(QLabel, "sectionStepTitle") if lbl.accessibleName()}
    assert {"1. Wrzuć zdjęcia albo filmy", "2. Wybierz jakość", "3. Zapisz do folderu"} <= titles
    variants = {t.findChild(QLabel, "sectionStepTitle").text(): t.property("variant")
                for t in _tiles(win) if t.findChild(QLabel, "sectionStepTitle") and t.isVisibleTo(win)}
    assert variants["Wrzuć zdjęcia albo filmy"] == "drop"
    assert variants["Wybierz jakość"] == variants["Zapisz do folderu"] == "plain"


def test_simple_empty_state_shown_only_for_empty_queue_and_drops_still_reach_the_window(make_window, tmp_path):
    from PIL import Image

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="simple")
    empty = win._simple_empty
    assert empty.isVisibleTo(win) and not win.simple_file_list.isVisibleTo(win)
    assert empty.findChild(QLabel, "dropEmptyTitle").text() == "Upuść tu zdjęcia albo filmy"
    assert empty.findChild(QLabel, "dropEmptyHint").text() == "…albo dodaj je przyciskiem"
    icon = empty.findChild(QLabel, "dropEmptyIcon")
    assert icon.size() == QSize(44, 44) and not icon.pixmap().isNull()
    img = tmp_path / "a.png"
    Image.new("RGB", (8, 8), (10, 120, 60)).save(img)
    win._add_path_to_queue(img)
    win._refresh_simple_file_list()
    app.processEvents()
    assert not empty.isVisibleTo(win) and win.simple_file_list.isVisibleTo(win)
    # Upuszczanie: żaden element kafelka ani lista nie przechwytuje zdarzenia — pierwszy rodzic z acceptDrops to okno.
    assert win.acceptDrops()
    for w in (empty, icon, win.simple_file_list, win.simple_file_list.viewport(), win.simple_queue_label):
        p = w
        while p is not None and not p.acceptDrops():
            p = p.parentWidget()
        assert p is win, (w.objectName() or type(w).__name__, p)


def test_row_icons_are_20px_in_both_lists(make_window, tmp_path):
    from PIL import Image

    from inyfinn_resizer.app.main_window import ROW_ICON_PX

    make, app, _ = make_window
    win = make(QRect(0, 0, 1920, 1152), mode="advanced")
    img = tmp_path / "a.png"
    Image.new("RGB", (8, 8), (10, 120, 60)).save(img)
    win._add_path_to_queue(img)
    win._refresh_simple_file_list()
    assert ROW_ICON_PX == 20
    assert win.input_tree.iconSize() == QSize(20, 20)
    assert win.simple_file_list.iconSize() == QSize(20, 20)
    assert win.simple_file_list.spacing() == 6


def test_message_box_uses_ds_icon_from_current_theme(make_window):
    from PySide6.QtWidgets import QMessageBox

    from inyfinn_resizer.app.dialogs.message_boxes import _make_box
    from inyfinn_resizer.app.widgets.section_icons import message_box_pixmap

    _make, app, _ = make_window
    box = _make_box(None, QMessageBox.Question, "Nadpisać plik?", "Plik już istnieje. Nadpisać go?",
                    QMessageBox.Yes | QMessageBox.No)
    assert box.icon_kind == "question"
    box.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    box.show()
    for _i in range(3):
        app.processEvents()
    assert box.iconPixmap().toImage() == message_box_pixmap("question", size=32).toImage()
    box.hide()
    box.deleteLater()


# ——— zmiana motywu w działającym programie (przełącznik „Motyw”) ———


@pytest.mark.parametrize("mode", ["advanced", "simple"])
def test_theme_toggle_keeps_uppercase_labels_and_icon_button_sizes(make_window, mode):
    """Po kliknięciu przełącznika arkusz jest nakładany od nowa: czcionki wracają do stanu sprzed naszych zmian,
    a QSS wpisuje w przyciski własne min/max. 2.6.5 przed poprawką: „Tryb prosty”, „Przywróć preset” i nadtytuł
    „Kolory” traciły wersaliki, a kwadratowy przycisk „−” kurczył się z 40×40 do 20×16."""
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QPushButton

    from inyfinn_resizer.app.themes import apply_theme, current_theme, typography

    make, app, _ = make_window
    apply_theme(app, "dobra-kaloria-zielen-jasny")
    win = make(QRect(0, 0, 1920, 1152), mode=mode, fmt="png")
    win._set_theme("dobra-kaloria-zielen-jasny")
    for _i in range(4):
        app.processEvents()

    def snapshot():
        out = {}
        for w in win.findChildren(QPushButton) + win.findChildren(QLabel):
            if not w.isVisible():
                continue
            name = w.objectName()
            if isinstance(w, QPushButton):
                wants_upper = typography.wants_uppercase(w)  # 2.6.6 (S18): z bieżącego stanu przycisku
            else:
                wants_upper = name in typography.DISPLAY_OBJECTS or name in typography.EYEBROW_OBJECTS
            if wants_upper:
                upper = w.font().capitalization() == QFont.Capitalization.AllUppercase
                out[(type(w).__name__, name, w.text())] = (upper, w.width(), w.height())
        return out

    try:
        before = snapshot()
        assert before and all(v[0] for v in before.values())
        toggle = win._theme_toggle
        for expected in ("dobra-kaloria-zielen-ciemny", "dobra-kaloria-zielen-jasny"):
            QTest.mouseClick(toggle, Qt.MouseButton.LeftButton, pos=QPoint(toggle.width() // 2, toggle.height() // 2))
            for _i in range(6):
                app.processEvents()
            assert current_theme() == expected
            after = snapshot()
            assert [k for k, v in after.items() if not v[0]] == []  # nic nie zgubiło wersalików
            assert {k: v[1:] for k, v in after.items()} == {k: v[1:] for k, v in before.items()}  # te same rozmiary
            for btn in (win.delete_preset_btn, win.simple_output_clear):
                assert btn.minimumSize() == btn.maximumSize() and btn.minimumWidth() == btn.minimumHeight() >= 36
    finally:
        apply_theme(app, "dobra-kaloria-zielen-jasny")
