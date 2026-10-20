"""2.6.7: nowy wygląd czterech części (wybór usera z rundy /design 20.10.2026).

1. Tryb prosty (wariant D): format = pigułki wyboru PRZED „Konwertuj” (dawne kolorowe kafle konwertowały od razu),
   suwak jakości w swoim rzędzie, „Wybierz folder…” zwykłym przyciskiem obok pola, ~70 px między częściami (S60).
2. Tryb zaawansowany (B + C): białe karty na szarym panelu, rozszerzenia jako pigułki wielokrotnego wyboru,
   karty zwijane z podsumowaniem i zapamiętanym stanem.
3. Okno „Ustawienia…” (D): jedna przewijana strona z kotwicami zamiast zakładek.
4. Okno „Opcje zaawansowane” (B): karty z przełącznikiem w nagłówku zamiast pola „Włącz…”.
5. Obrys przycisków drugorzędnych lżejszy (S59) — przez tokeny.
6. Siatki przestawiają się przy wąskim oknie (960 px) bez nachodzenia i ucinania.
"""

from __future__ import annotations

import pytest
from PIL import Image
from PySide6.QtCore import QPoint, QRect, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
)

from inyfinn_resizer.app import themes, user_settings
from inyfinn_resizer.app.dialogs.advanced_options import AdvancedSettingsPanel
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.themes import palettes
from inyfinn_resizer.app.widgets.form_grid import FormGrid
from inyfinn_resizer.app.widgets.pills import FormatPills, PillGroup
from inyfinn_resizer.app.window_fit import DENSITIES
from inyfinn_resizer.core.formats.registry import output_format_for_input
from inyfinn_resizer.core.job import FormatOptions, ResizeMode, ResizeOptions, TransformOptions

from test_window_fit import make_window  # noqa: F401  (fixture: okno z zadanym ekranem)

BIG = QRect(0, 0, 1920, 1152)
LEFT = Qt.MouseButton.LeftButton


def _click(widget) -> None:
    QTest.mouseClick(widget, LEFT)


def _settle(app, n: int = 4) -> None:
    for _ in range(n):
        app.processEvents()


# ——— 1. tryb prosty ———


def test_simple_format_is_pills_not_colored_tiles(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="simple")
    assert not win.findChildren(QPushButton, "formatChip")  # pastelowe kafle PNG / JPG / AVIF zniknęły
    pills = win.simple_format_pills
    assert [pills.button(k).text() for k in pills.keys()] == ["Jak oryginał", "PNG", "JPG", "AVIF", "WebP"]
    assert pills.value() == "original"
    assert all(pills.button(k).property("pigulka") is True for k in pills.keys())
    _click(pills.button("avif"))
    assert pills.value() == "avif" and pills.values() == ["avif"]  # jeden wybór naraz
    _click(pills.button("png"))
    assert pills.values() == ["png"]
    _click(pills.button("png"))
    assert pills.values() == ["png"]  # zaznaczonej nie da się wyłączyć (zawsze jakiś format)


def test_simple_pill_click_does_not_start_conversion(make_window, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="simple")
    started = []
    monkeypatch.setattr(win, "_run_jobs", lambda jobs, **kw: started.append(jobs))
    for key in win.simple_format_pills.keys():
        _click(win.simple_format_pills.button(key))
    assert started == []  # pigułka tylko wybiera; konwertuje dopiero „Konwertuj”


def test_simple_convert_uses_the_selected_pill(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    jobs = []
    monkeypatch.setattr(win, "_run_jobs", lambda j, **kw: jobs.extend(j))
    photo = tmp_path / "kot.jpg"
    Image.new("RGB", (8, 8), (10, 120, 60)).save(photo)
    win._add_path_to_queue(photo)
    win._simple_output_dir = tmp_path / "gotowe"  # z folderem nie pyta o nadpisanie
    win._refresh_simple_output()

    _click(win.simple_convert_btn)  # „Jak oryginał”: format wg pliku wejściowego
    assert [j.output_format for j in jobs] == [output_format_for_input(photo)]
    jobs.clear()

    _click(win.simple_format_pills.button("png"))
    _click(win.simple_convert_btn)
    assert [(j.output_format, j.output_path.suffix) for j in jobs] == [("png", ".png")]
    jobs.clear()

    _click(win.simple_format_pills.button("webp"))
    film = tmp_path / "klip.mov"
    film.write_bytes(b"")
    win._add_path_to_queue(film)
    _click(win.simple_convert_btn)
    by_name = {j.input_path.name: j.output_format for j in jobs}
    assert by_name == {"kot.jpg": "webp", "klip.mov": "gif"}  # film zawsze jako GIF, zdjęcia wg pigułki


@pytest.mark.parametrize("level", [0, 1, 2])
def test_simple_parts_are_separated_by_section_gap(make_window, level):  # noqa: F811
    """S60: ~70 px między plikami / folderem / formatem i jakością / Konwertuj (na niskim ekranie 48 → 28 px)."""
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    assert [d.section_gap for d in DENSITIES] == [70, 48, 28]
    win._apply_density(level)
    win._flush_layouts()
    _settle(app)
    gap = DENSITIES[level].section_gap
    center = win._simple_center
    assert center.layout().spacing() == gap and win._simple_page_lay.spacing() == gap
    tile = win._simple_center.findChildren(QFrame, "bentoTile")[0]  # strefa plików trybu prostego
    folder = win._simple_folder_grid
    fmt_part = win._simple_format_grid.parentWidget()
    assert folder.y() - (tile.y() + tile.height()) == gap
    assert fmt_part.y() - (folder.y() + folder.height()) == gap
    scroll = win._simple_scroll
    assert win._simple_footer.y() - (scroll.y() + scroll.height()) == gap


@pytest.mark.parametrize("width", [1280, 960])
def test_simple_folder_button_is_regular_and_stays_next_to_the_field(make_window, width):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    win.resize(width, win.height())
    _settle(app)
    browse = next(b for b in win.findChildren(QPushButton, "btnBrowse") if b.text().startswith("Wybierz folder"))
    edit = win.simple_output_edit
    assert abs(browse.geometry().center().y() - edit.mapTo(browse.parentWidget(), edit.rect().center()).y()) <= 2
    assert browse.x() >= edit.x() + edit.width() - 1  # obok pola, nie pod nim, także w wąskim oknie
    assert browse.width() <= browse.sizeHint().width() + 8  # szerokość napisu, nie na całą szerokość
    assert browse.height() == edit.height()  # S48: równa wysokość w jednym rzędzie


def test_simple_quality_has_its_own_row_with_label_and_value(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    grid = win._simple_format_grid
    labels = [lbl.text() for lbl, _f in grid._rows if lbl is not None]
    assert labels == ["Format", "Jakość"]
    pills_bottom = win.simple_format_pills.mapTo(win, QPoint(0, win.simple_format_pills.height())).y()
    slider_top = win.simple_quality_slider.mapTo(win, QPoint(0, 0)).y()
    assert slider_top >= pills_bottom - 4  # suwak pod pigułkami, w osobnym rzędzie
    value = win.simple_quality_label
    assert value.isVisible() and value.text() == str(win.simple_quality_slider.value())
    slider_right = win.simple_quality_slider.mapTo(win, QPoint(win.simple_quality_slider.width(), 0)).x()
    assert value.mapTo(win, QPoint(0, 0)).x() >= slider_right  # liczba obok suwaka, nie na nim
    assert value.width() >= 40


def test_simple_quality_still_drives_the_shared_quality(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="simple")
    win.simple_quality_slider.setValue(63)
    assert win.quality_slider.value() == 63 and win._simple_format_opts().quality == 63


# ——— 2. tryb zaawansowany: pigułki rozszerzeń ———


def test_advanced_extensions_are_multi_select_pills(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, fmt="png")
    combo = win.format_combo
    assert isinstance(combo, FormatPills) and not win.findChildren(QPushButton, "formatMultiCombo")
    assert [combo.pill(k).text() for k in ("png", "jpeg", "webp", "avif", "gif")] == ["PNG", "JPG", "WebP", "AVIF", "GIF"]
    assert combo.selected_formats() == ["png"]
    _click(combo.pill("jpeg"))
    assert combo.selected_formats() == ["jpeg", "png"]  # kolejność jak w dawnej liście rozwijanej (PRIMARY_FORMATS)
    _click(combo.pill("avif"))
    assert combo.selected_formats() == ["jpeg", "png", "avif"]
    assert win._selected_formats() == ["jpeg", "png", "avif"]  # to samo widzi silnik (zadania konwersji)
    _click(combo.pill("png"))
    assert combo.selected_formats() == ["jpeg", "avif"]
    _click(combo.pill("jpeg"))
    _click(combo.pill("avif"))
    assert combo.selected_formats() == ["avif"]  # ostatniego formatu nie da się odznaczyć
    assert combo.first_selected() == "avif"


def test_extension_change_updates_colors_row_and_session_formats(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, fmt="avif")
    assert not win._show_colors_tile
    _click(win.format_combo.pill("gif"))
    assert win._show_colors_tile and win._colors_row.isVisibleTo(win)
    snap = user_settings.snapshot_from_window(win)
    assert snap["ui"]["formats"] == ["avif", "gif"]
    win.format_combo.set_selected(["webp"])
    user_settings.restore_to_window(win, snap)  # przywrócenie sesji ustawia te same pigułki
    assert win.format_combo.selected_formats() == ["avif", "gif"]


def test_rare_extensions_sit_behind_inne_and_stay_visible_when_selected(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, fmt="png")
    combo = win.format_combo
    group = combo._group
    assert not group.is_expanded() and not combo.pill("tiff").isVisibleTo(win)
    _click(group.more_button())
    _settle(app)
    assert group.is_expanded() and all(combo.pill(k).isVisibleTo(win) for k in ("tiff", "heic", "bmp", "jp2", "pdf"))
    _click(combo.pill("pdf"))
    assert combo.selected_formats() == ["png", "pdf"]
    _click(group.more_button())  # z zaznaczonym rzadkim formatem rząd nie zwija się (zaznaczenia nie da się ukryć)
    assert group.is_expanded()
    _click(combo.pill("pdf"))
    _click(group.more_button())
    assert not group.is_expanded()
    combo.set_selected(["bmp"])  # format z ukrytego rzędu (np. z sesji) sam go rozwija
    assert group.is_expanded() and combo.selected_formats() == ["bmp"]


def test_transparency_only_mode_keeps_working_with_pills(make_window):  # noqa: F811
    """Usuwanie tła ogranicza wybór do formatów z przezroczystością — jak przy dawnej liście rozwijanej."""
    make, app, _ = make_window
    win = make(BIG, fmt="jpeg")
    combo = win.format_combo
    _click(combo.pill("gif"))
    win.remove_bg_cb.setChecked(True)
    assert combo.selected_formats() == ["png"]  # jpeg / gif odpadają, zostaje format z alfa
    assert not combo.pill("jpeg").isEnabled() and not combo.pill("gif").isEnabled() and not combo.pill("tiff").isEnabled()
    assert combo.pill("png").isEnabled() and combo.pill("webp").isEnabled() and combo.pill("avif").isEnabled()
    _click(combo.pill("webp"))
    assert combo.selected_formats() == ["webp", "png"]  # kolejność jak w dawnej liście (PRIMARY_FORMATS)
    QTest.mouseClick(combo.pill("jpeg"), LEFT)  # wyłączona pigułka niczego nie zmienia
    assert combo.selected_formats() == ["webp", "png"]
    assert win._selected_formats() == ["webp", "png"]
    win.remove_bg_cb.setChecked(False)
    assert combo.pill("jpeg").isEnabled() and combo.pill("gif").isEnabled()
    assert combo.selected_formats()  # coś zostaje zaznaczone


# ——— 2. tryb zaawansowany: karty zwijane ———


def test_cards_are_white_cards_on_a_grey_panel_in_one_column(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG)
    assert list(win._cards) == ["format", "background", "dimensions", "save"]
    panel = win._settings_body
    assert panel.objectName() == "cardPanel"
    ys = []
    for card in win._cards.values():
        assert card.objectName() == "sectionCard" and panel.isAncestorOf(card)
        assert card.title_label.text()
        ys.append(card.mapTo(win, QPoint(0, 0)).y())
    assert ys == sorted(ys) and len(set(ys)) == 4  # jedna kolumna, jedna pod drugą
    assert win._cards["format"].isAncestorOf(win.settings_btn)  # „Ustawienia…” w nagłówku karty


def test_card_header_click_collapses_to_summary_and_expands_again(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG)
    card = win._cards["background"]
    assert not card.is_collapsed() and card.body.isVisibleTo(win) and not card.summary_label.isVisibleTo(win)
    middle = QPoint(card.header.width() // 2, card.header.height() // 2)  # pusty środek nagłówka
    QTest.mouseClick(card.header, LEFT, Qt.KeyboardModifier.NoModifier, middle)
    _settle(app)
    assert card.is_collapsed() and not card.body.isVisibleTo(win)
    assert card.summary_label.isVisibleTo(win)
    assert "Tło zostaje" in card.summary_label.text()
    _click(card.chevron)  # strzałka też zwija / rozwija
    assert not card.is_collapsed() and card.body.isVisibleTo(win) and not card.summary_label.isVisibleTo(win)
    # kontrolki zwiniętej karty nadal istnieją i trzymają stan
    card.set_collapsed(True)
    win.segregate_cb.setChecked(True)
    assert "segreguj do podfolderów" in card.summary_label.text()
    assert win.segregate_cb.isChecked() and win._selected_formats()


def test_card_summaries_follow_the_controls(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, fmt="avif")
    win.quality_slider.setValue(63)
    assert win._cards["format"].summary().replace(" ", " ") == "AVIF · jakość 63"
    win.scale_slider.setValue(50)
    assert "skala 50%" in win._cards["dimensions"].summary().replace("\u00a0", " ")
    win.output_enabled_cb.setChecked(True)
    assert win._cards["save"].summary().startswith("Do folderu wyjściowego")


def test_collapsed_state_is_remembered_between_sessions(make_window):  # noqa: F811
    make, app, path = make_window
    win = make(BIG)
    assert user_settings.load_collapsed_sections() == set()  # domyślnie wszystko rozwinięte
    win._cards["save"].set_collapsed(True)
    win._cards["background"].set_collapsed(True)
    stored = QSettings(str(path), QSettings.Format.IniFormat).value("ui/collapsed_sections")
    assert sorted(stored) == ["background", "save"]
    win2 = make(BIG)  # nowe okno = nowe uruchomienie programu
    assert win2._cards["save"].is_collapsed() and win2._cards["background"].is_collapsed()
    assert not win2._cards["format"].is_collapsed() and not win2._cards["dimensions"].is_collapsed()
    assert not win2._cards["save"].body.isVisibleTo(win2)
    win2._cards["save"].set_collapsed(False)
    win2._cards["background"].set_collapsed(False)
    assert user_settings.load_collapsed_sections() == set()  # pusta lista też się zapisuje
    assert not make(BIG)._cards["save"].is_collapsed()


def test_collapsed_sections_settings_accept_single_string_value(monkeypatch, tmp_path):
    """INI zwraca listę jednoelementową jak zwykły napis, pustą listę jak pusty napis."""
    ini = tmp_path / "s.ini"
    monkeypatch.setattr(user_settings, "_settings", lambda: QSettings(str(ini), QSettings.Format.IniFormat))
    user_settings.save_collapsed_sections(["save"])
    assert user_settings.load_collapsed_sections() == {"save"}
    user_settings.save_collapsed_sections([])
    assert user_settings.load_collapsed_sections() == set()


# ——— 4. Opcje zaawansowane ———


def test_options_switch_changes_the_same_as_the_old_checkbox(make_window):  # noqa: F811
    make, app, _ = make_window
    panel = AdvancedSettingsPanel(ResizeOptions(), TransformOptions())
    panel.show()
    _settle(app)
    try:
        for name in ("resize_enable", "crop_enable"):
            sw = getattr(panel, name)
            assert isinstance(sw, QCheckBox) and sw.objectName() == "sectionSwitch"  # przełącznik DS, nie zwykłe pole
            assert not sw.isChecked()
        assert panel.get_resize().mode == ResizeMode.NONE
        _click(panel.resize_enable)
        assert panel.resize_enable.isChecked()
        panel.dim_spin.setValue(900)
        panel.side_combo.setCurrentIndex(2)
        r = panel.get_resize()
        assert (r.mode, r.dimension, r.side) == (ResizeMode.ONE_SIDE, 900, "longer")
        _click(panel.resize_enable)
        assert panel.get_resize().mode == ResizeMode.NONE  # wyłączony przełącznik = bez własnej zmiany rozmiaru

        assert panel.get_transforms().crop_w == 0
        panel.crop_w.setValue(300)
        panel.crop_h.setValue(200)
        assert panel.get_transforms().crop_w == 0  # prostokąt liczy się dopiero po włączeniu
        _click(panel.crop_enable)
        t = panel.get_transforms()
        assert (t.crop_w, t.crop_h) == (300, 200)
        # opcje kadrowania niezależne od prostokąta działają tak jak dotąd, także przy wyłączonym przełączniku
        _click(panel.crop_enable)
        panel.trim_transparent.setChecked(True)
        panel.trim_margin.setValue(12)
        t = panel.get_transforms()
        assert t.trim_transparent and t.trim_margin == 12 and t.crop_w == 0
    finally:
        panel.deleteLater()


def test_options_off_content_is_dimmed_and_inactive(make_window):  # noqa: F811
    make, app, _ = make_window
    panel = AdvancedSettingsPanel(ResizeOptions(), TransformOptions())
    panel.show()
    _settle(app)
    try:
        body = panel._resize_body
        assert not panel.dim_spin.isEnabled() and body.graphicsEffect() is not None  # przygaszone i nieaktywne
        assert body.graphicsEffect().opacity() < 1.0
        assert not panel.crop_x.isEnabled()
        assert panel.trim_transparent.isEnabled() and panel.preserve_aspect.isEnabled()  # niezależne od przełącznika
        _click(panel.resize_enable)
        assert panel.dim_spin.isEnabled() and body.graphicsEffect() is None
        _click(panel.crop_enable)
        assert panel.crop_x.isEnabled()
    finally:
        panel.deleteLater()


def test_options_panel_loads_state_and_resets(make_window):  # noqa: F811
    make, app, _ = make_window
    resize = ResizeOptions(mode=ResizeMode.ONE_SIDE, side="width", dimension=640)
    transforms = TransformOptions(crop_w=100, crop_h=50, flip_h=True, grayscale=True)
    panel = AdvancedSettingsPanel(resize, transforms)
    try:
        assert panel.resize_enable.isChecked() and panel.crop_enable.isChecked()  # stan z ustawień trafia na przełączniki
        assert panel.dim_spin.isEnabled() and panel.crop_x.isEnabled()
        assert panel.get_transforms().flip_h and panel.get_transforms().grayscale
        panel.reset_all()
        assert not panel.resize_enable.isChecked() and not panel.crop_enable.isChecked()
        assert panel.get_resize().mode == ResizeMode.NONE and not panel.get_transforms().flip_h
    finally:
        panel.deleteLater()


# ——— 3. okno Ustawienia ———


def test_format_settings_is_one_scrolling_page_with_anchors(make_window):  # noqa: F811
    make, app, _ = make_window
    dlg = FormatSettingsDialog("png", FormatOptions())
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    QTest.qWait(80)
    _settle(app)
    try:
        assert not dlg.findChildren(QTabWidget)  # zakładki nad pustym polem zniknęły
        anchors = dlg.findChildren(QPushButton, "anchorTab")
        assert [a.text() for a in anchors] == ["JPEG", "PNG", "WebP", "AVIF", "GIF", "Zaawansowane"]
        titles = [lbl.text() for lbl in dlg.findChildren(QLabel, "settingsSectionTitle")]
        assert titles == ["JPEG", "PNG", "WebP", "AVIF", "GIF", "Zaawansowane"]  # wszystkie sekcje na jednej stronie
        sections = [dlg._sections[k] for k in ("jpeg", "png", "webp", "avif", "gif", "advanced")]
        ys = [s.y() for s in sections]
        assert ys == sorted(ys) and len(set(ys)) == 6
        bar = dlg._scroll.verticalScrollBar()
        # otwarte na sekcji formatu z okna głównego
        assert abs(bar.value() - min(dlg._sections["png"].y() - 8, bar.maximum())) <= 2
        assert dlg._anchor_btns["png"].isChecked()
        _click(dlg._anchor_btns["webp"])
        _settle(app)
        assert abs(bar.value() - min(dlg._sections["webp"].y() - 8, bar.maximum())) <= 2
        assert dlg._anchor_btns["webp"].isChecked()
        _click(dlg._anchor_btns["jpeg"])
        _settle(app)
        assert bar.value() <= 6  # pierwsza sekcja: góra strony (8 px powietrza i tak nie mieści się nad nią)
        bar.setValue(bar.maximum())  # przewijanie przełącza aktywną kotwicę
        _settle(app)
        assert dlg._anchor_btns["advanced"].isChecked()
        # opis formatu stoi na górze sekcji, nie na dole okna
        jpeg = dlg._sections["jpeg"]
        assert any("zdjęcie bez przezroczystości" in lbl.text() for lbl in jpeg.findChildren(QLabel))
    finally:
        dlg.close()


def test_format_settings_has_no_giant_empty_area(make_window):  # noqa: F811
    make, app, _ = make_window
    dlg = FormatSettingsDialog("webp", FormatOptions())
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    _settle(app)
    try:
        assert dlg.height() <= 900  # nie rośnie do wysokości całej strony (6 sekcji), reszta się przewija
        assert dlg._scroll.verticalScrollBar().maximum() > 0
    finally:
        dlg.close()


def test_format_settings_options_round_trip(make_window):  # noqa: F811
    """Mechanika opcji bez zmian: te same kontrolki czytają i zapisują te same pola FormatOptions."""
    make, app, _ = make_window
    dlg = FormatSettingsDialog("jpeg", FormatOptions())
    try:
        dlg._jpeg_progressive.setChecked(True)
        dlg._subsampling.setCurrentIndex(dlg._subsampling.findData("full"))
        dlg._png_mode.setCurrentIndex(2)
        dlg._png_lossless.setChecked(True)
        dlg._gif_level.setValue(3)
        dlg._avif_cap.setChecked(True)
        dlg._avif_max_kb.setValue(300)
        opts = dlg.get_options()
        assert opts.progressive and opts.subsampling == "full" and opts.png_mode == "png24"
        assert opts.lossless and opts.gif_level == 3 and opts.avif_max_kb == 300.0
        dlg._reset()
        fresh, defaults = dlg.get_options(), FormatOptions()
        assert fresh.progressive == defaults.progressive and fresh.png_mode == defaults.png_mode == "auto"
        assert fresh.avif_max_kb is None and fresh.gif_level == defaults.gif_level and not fresh.lossless
        # sekcja Zaawansowane żyje w tym samym oknie i oddaje te same typy co dotąd
        dlg._advanced_panel.resize_enable.setChecked(True)
        dlg._advanced_panel.dim_spin.setValue(1111)
        assert dlg.get_resize().mode == ResizeMode.ONE_SIDE and dlg.get_resize().dimension == 1111
        assert isinstance(dlg.get_transforms(), TransformOptions)
    finally:
        dlg.deleteLater()


# ——— 5. obrys przycisków drugorzędnych (S59) ———


@pytest.mark.parametrize("theme", ["dobra-kaloria-zielen-jasny", "dobra-kaloria-krem-jasny"])
def test_secondary_button_outline_is_the_light_grey_token(theme):
    key = theme.removeprefix("dobra-kaloria-")
    assert palettes.ROLES[key]["color_btn2_border"] == "#868E96"  # DS 2.0.10: grey-500 zamiast #222222
    qss = themes.render_qss(theme)
    start = qss.index("QPushButton {")
    rule = qss[start:qss.index("}", start)]
    border = next(line for line in rule.splitlines() if line.strip().startswith("border:"))
    assert "#868E96" in border and "#222222" not in border.lower()  # obrys z tokenu; tekst przycisku zostaje #222222
    assert "@BTN2_BORDER@" not in qss  # wszystkie znaczniki podstawione z tokenów, nic na sztywno


# ——— 6. responsywność ———


def _squeezed(root: QWidget) -> list[str]:
    bad = []
    for w in root.findChildren(QWidget):
        if not w.isVisible() or w.width() <= 0:
            continue
        if isinstance(w, (QPushButton, QCheckBox, QLabel)) and w.minimumSizeHint().width() > w.width() + 1:
            if isinstance(w, QLabel) and w.wordWrap():
                continue
            bad.append(f"{type(w).__name__}:{w.objectName() or getattr(w, 'text', lambda: '')()}")
    return bad


@pytest.mark.parametrize("width", [1280, 960])
def test_advanced_grids_rearrange_without_overlap_or_clipping(make_window, width):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, fmt="png")
    assert win.minimumWidth() <= 960  # okno da się zwęzić do 960 px
    win.resize(width, win.height())
    _settle(app, 6)
    assert win.width() == width or win.width() >= win.minimumWidth()
    grids = [g for g in win.findChildren(FormGrid) if g.isVisibleTo(win)]  # bez siatek ukrytego trybu prostego
    assert len(grids) == 4
    for grid in grids:
        for lbl, field in grid._rows:
            if lbl is None or not field.isVisibleTo(win):
                continue
            lr, fr = lbl.geometry(), field.geometry()
            assert fr.right() <= grid.width() and fr.left() >= 0, (width, lbl.text(), fr, grid.width())  # nic nie wystaje
            assert not lr.intersects(fr), (width, lbl.text(), lr, fr)  # etykieta nie nachodzi na pole
            if not grid.is_wide():
                assert lr.bottom() <= fr.top()  # wąsko: etykieta nad polem
    if width == 960:
        assert not win._format_grid.is_wide()  # rząd pigułek jest za szeroki na układ z etykietą z boku → etykieta nad polem
    else:
        assert all(g.is_wide() for g in grids)
    assert _squeezed(win) == []  # żaden napis ani przycisk nie jest ściśnięty poniżej swojej szerokości
    combo = win.bg_model_combo
    assert combo.width() >= combo.sizeHint().width(), (width, combo.width(), combo.sizeHint().width())  # „Najlepsza jakość” w całości


def test_simple_window_narrow_keeps_everything_visible(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    win.resize(960, win.height())
    _settle(app, 6)
    assert _squeezed(win) == []
    footer = win._simple_footer
    assert win.simple_convert_btn.geometry().right() <= footer.width()


def test_pill_group_min_width_is_the_widest_row():
    """Dwa rzędy pigułek: minimum szerokości = najszerszy rząd (żaden nie jest ściskany)."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from inyfinn_resizer.app.widgets.layout_helpers import pin_button_min_widths

    group = PillGroup([[("a", "AAAA", ""), ("b", "BBBB", "")], [("c", "CCCCCCCCCCCC", "")]], multi=True)
    pin_button_min_widths(group)  # okno robi to samo przy każdym pomiarze: minimum przycisku = jego napis
    widest = max(sum(g.sizeHint().width() for g in (group.button("a"), group.button("b"))), group.button("c").sizeHint().width())
    assert group.minimumSizeHint().width() >= widest
    group.deleteLater()
