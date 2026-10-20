"""2.6.8: zapis jawnie (S82/S83), białe pole na pliki (S79), oddech (S80) i GIF bez wyszarzonych pól (S81).

Okna dialogowe są podmieniane (monkeypatch) — żaden test nie czeka na ``exec``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QAbstractButton, QCheckBox, QComboBox, QFrame, QLabel, QSpinBox, QWidget

from inyfinn_resizer.app import main_window as mw
from inyfinn_resizer.app import save_conflicts as sc
from inyfinn_resizer.app import themes
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.core.compressors import gif as gifmod
from inyfinn_resizer.core.job import FormatOptions, JobSpec
from inyfinn_resizer.core.pipeline import unique_conv_path

from test_window_fit import make_window  # noqa: F401  (fixture: okno z zadanym ekranem)

BIG = QRect(0, 0, 1920, 1152)
ASK_TAIL = "Gdy plik o tej nazwie już istnieje, zapytam: nadpisać czy zapisać obok z dopiskiem."


def _plain(text: str) -> str:
    return text.replace(" ", " ")


def _png(path: Path) -> Path:
    Image.new("RGB", (8, 8), (10, 120, 60)).save(path)
    return path


def _spy_dialog(monkeypatch, answer):
    """Podmienia pytanie o zajęte nazwy; zwraca listę wywołań (kwargs)."""
    calls: list[dict] = []

    def fake(parent, **kwargs):
        calls.append(kwargs)
        return answer

    monkeypatch.setattr(mw, "ask_save_conflict", fake)
    return calls


def _spy_run(win, monkeypatch):
    runs: list[tuple[list[JobSpec], dict]] = []
    monkeypatch.setattr(win, "_run_jobs", lambda jobs, **kw: runs.append((jobs, kw)))
    return runs


# ——— zdania o zapisie (czysta logika) ———


def test_simple_save_info_texts_follow_folder_and_queue(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    other = tmp_path / "gotowe"
    assert _plain(sc.simple_save_info(None, [a])) == f"Zapis obok oryginałów. {ASK_TAIL}"
    assert _plain(sc.simple_save_info(None, [])) == f"Zapis obok oryginałów. {ASK_TAIL}"
    assert _plain(sc.simple_save_info(tmp_path, [a, b])) == f"To ten sam folder co zdjęcia. {ASK_TAIL}"
    assert _plain(sc.simple_save_info(other, [a, b])) == f"Zapis do folderu „gotowe”. {ASK_TAIL}"
    mixed = [a, tmp_path / "x" / "c.png"]  # nie każde zdjęcie leży w tym folderze
    assert _plain(sc.simple_save_info(tmp_path, mixed)) == f"Zapis do folderu „{tmp_path.name}”. {ASK_TAIL}"
    assert _plain(sc.simple_save_info(other, [])) == f"Zapis do folderu „gotowe”. {ASK_TAIL}"  # pusta lista nie „zgadza się”


def test_advanced_save_info_texts():
    assert _plain(sc.advanced_save_info(False, True)) == f"Zapis obok oryginałów. {ASK_TAIL}"
    assert _plain(sc.advanced_save_info(False, False)) == f"Zapis obok oryginałów. {ASK_TAIL}"
    assert _plain(sc.advanced_save_info(True, True)) == f"Zapis do folderu wyjściowego. {ASK_TAIL}"
    assert _plain(sc.advanced_save_info(True, False)) == (
        "Zapis do folderu wyjściowego. Pliki o tych samych nazwach zostaną nadpisane bez pytania."
    )


def test_save_info_has_no_internal_suffix_and_uses_hard_spaces(tmp_path):
    texts = [sc.simple_save_info(None, []), sc.advanced_save_info(True, False), sc.advanced_save_info(True, True)]
    for text in texts:
        assert "_conv" not in text and "conv" not in text.lower()
        assert " w " not in text and " z " not in text and " o " not in text and " i " not in text  # S72
    assert "o tej" in texts[0] and "z dopiskiem" in texts[0]


# ——— zajęte nazwy (czysta logika) ———


def _job(inp: Path, out: Path) -> JobSpec:
    return JobSpec(input_path=inp, output_path=out, output_format="webp")


def test_conflicts_are_existing_targets_and_batch_duplicates(tmp_path):
    taken = _png(tmp_path / "zajete.png")
    free = tmp_path / "wolne.webp"
    jobs = [
        _job(tmp_path / "a.png", taken),            # cel istnieje na dysku
        _job(tmp_path / "b.png", free),             # wolny
        _job(tmp_path / "c.jpg", free),             # ten sam cel co poprzedni w partii
    ]
    assert sc.conflicting_indices(jobs) == [0, 2]
    assert sc.conflicting_indices([jobs[1]]) == []


def test_suffix_names_are_unique_on_disk_and_inside_the_batch(tmp_path):
    existing = _png(tmp_path / "foto.webp")
    _png(tmp_path / "foto_conv.webp")  # pierwsza nazwa z dopiskiem też zajęta na dysku
    jobs = [_job(tmp_path / "foto.png", existing), _job(tmp_path / "foto.jpg", existing)]
    clash = sc.conflicting_indices(jobs)
    assert clash == [0, 1]
    names = [j.output_path.name for j in sc.with_suffix_names(jobs, clash)]
    assert names == ["foto_conv2.webp", "foto_conv3.webp"]
    assert len(set(names)) == 2 and not any((tmp_path / n).exists() for n in names)
    assert unique_conv_path(existing).name == "foto_conv2.webp"  # to samo nazewnictwo co w rdzeniu


def test_same_as_source_needs_every_conflict_beside_its_input(tmp_path):
    other = tmp_path / "out"
    other.mkdir()
    a = _png(tmp_path / "a.png")
    jobs = [_job(a, tmp_path / "a.webp"), _job(a, other / "a.webp")]
    assert sc.same_as_source(jobs, [0]) is True
    assert sc.same_as_source(jobs, [1]) is False
    assert sc.same_as_source(jobs, [0, 1]) is False
    assert sc.same_as_source(jobs, []) is False


# ——— tryb prosty: przepływ ———


def _simple(make, tmp_path, *names):
    win = make(BIG, mode="simple")
    paths = []
    for name in names:
        p = tmp_path / name
        _png(p)
        win._add_path_to_queue(p)
        paths.append(p.resolve())
    return win, paths


def test_simple_no_folder_original_format_asks_and_suffix_gives_new_name(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, (src,) = _simple(make, tmp_path, "kot.png")
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win._start_simple_convert()
    assert len(calls) == 1
    assert calls[0]["conflicts"] == [src] and calls[0]["total"] == 1 and calls[0]["same_as_source"] is True
    assert [j.output_path.name for j in runs[0][0]] == ["kot_conv.png"]
    assert (tmp_path / "kot.png").exists() and not (tmp_path / "kot_conv.png").exists()  # nic nie zapisane przed startem


def test_simple_overwrite_keeps_the_source_name(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, (src,) = _simple(make, tmp_path, "kot.png")
    _spy_dialog(monkeypatch, "overwrite")
    runs = _spy_run(win, monkeypatch)
    win._start_simple_convert()
    assert [j.output_path for j in runs[0][0]] == [src]


def test_simple_cancel_starts_nothing(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _paths = _simple(make, tmp_path, "kot.png")
    _spy_dialog(monkeypatch, None)
    runs = _spy_run(win, monkeypatch)
    win._start_simple_convert()
    assert runs == []


def test_simple_other_format_beside_does_not_ask(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _paths = _simple(make, tmp_path, "kot.png", "pies.png")
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win.simple_format_pills.set_value("webp")
    win._start_simple_convert()
    assert calls == []
    assert sorted(j.output_path.name for j in runs[0][0]) == ["kot.webp", "pies.webp"]


def test_simple_folder_same_as_source_asks(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, (src,) = _simple(make, tmp_path, "kot.png")
    win._simple_output_dir = src.parent
    win._refresh_simple_output()
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win._start_simple_convert()
    assert len(calls) == 1 and calls[0]["same_as_source"] is True
    assert runs[0][0][0].output_path.name == "kot_conv.png"


def test_simple_other_folder_asks_only_when_a_name_is_taken(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _paths = _simple(make, tmp_path, "kot.png")
    out = tmp_path / "gotowe"
    win._simple_output_dir = out
    win._refresh_simple_output()
    calls = _spy_dialog(monkeypatch, "overwrite")
    runs = _spy_run(win, monkeypatch)
    win._start_simple_convert()
    assert calls == [] and len(runs) == 1  # folder pusty: bez pytania
    _png(out / "kot.png")  # teraz nazwa w folderze docelowym jest zajęta
    win._start_simple_convert()
    assert len(calls) == 1 and calls[0]["same_as_source"] is False
    assert runs[1][0][0].output_path == out / "kot.png"


def test_simple_batch_duplicates_get_distinct_names(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _paths = _simple(make, tmp_path, "a.png", "a.jpg")  # oba chcą być a.webp
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win.simple_format_pills.set_value("webp")
    win._start_simple_convert()
    assert len(calls) == 1 and len(calls[0]["conflicts"]) == 1
    names = sorted(j.output_path.name for j in runs[0][0])
    assert names == ["a.webp", "a_conv.webp"]
    # „Nadpisz” zostawia nazwy, jakie były (użytkownik zdecydował)
    runs.clear()
    _spy_dialog(monkeypatch, "overwrite")
    win._start_simple_convert()
    assert sorted(j.output_path.name for j in runs[0][0]) == ["a.webp", "a.webp"]


def test_simple_info_label_follows_folder_and_queue(make_window, tmp_path):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    label = win.simple_save_info_label
    assert label.objectName() == "saveInfo"
    assert _plain(label.text()) == f"Zapis obok oryginałów. {ASK_TAIL}"
    src = _png(tmp_path / "a.png")
    win._add_path_to_queue(src)
    win._simple_output_dir = src.resolve().parent
    win._refresh_simple_output()
    assert _plain(label.text()) == f"To ten sam folder co zdjęcia. {ASK_TAIL}"
    win._simple_output_dir = tmp_path / "gotowe"
    win._refresh_simple_output()
    assert _plain(label.text()) == f"Zapis do folderu „gotowe”. {ASK_TAIL}"
    win._clear_simple_output()
    assert _plain(label.text()) == f"Zapis obok oryginałów. {ASK_TAIL}"
    win._simple_output_dir = src.resolve().parent  # zmiana KOLEJKI przestawia zdanie bez ruszania folderu
    win._refresh_simple_output()
    win._clear_queue()
    assert _plain(label.text()) == f"Zapis do folderu „{src.resolve().parent.name}”. {ASK_TAIL}"


# ——— tryb zaawansowany: przepływ ———


def _advanced(make, tmp_path, fmt="webp"):
    win = make(BIG, mode="advanced")
    src = _png(tmp_path / "kot.png")
    win._add_path_to_queue(src)
    win.format_combo.set_selected([fmt])
    return win, src.resolve()


def test_advanced_in_place_conflicts_use_one_dialog(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, src = _advanced(make, tmp_path, "png")
    other = _png(tmp_path / "pies.png")
    win._add_path_to_queue(other)
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win._start_convert_subset(win._queue)
    assert len(calls) == 1  # jedno pytanie o całą partię, nie po jednym na plik
    assert calls[0]["total"] == 2 and len(calls[0]["conflicts"]) == 2 and calls[0]["same_as_source"] is True
    assert sorted(j.output_path.name for j in runs[0][0]) == ["kot_conv.png", "pies_conv.png"]


def test_advanced_cancel_and_overwrite(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, src = _advanced(make, tmp_path, "png")
    runs = _spy_run(win, monkeypatch)
    _spy_dialog(monkeypatch, None)
    win._start_convert_subset(win._queue)
    assert runs == []
    _spy_dialog(monkeypatch, "overwrite")
    win._start_convert_subset(win._queue)
    assert [j.output_path for j in runs[0][0]] == [src] and runs[0][1]["overwrite"] is True


def test_advanced_no_conflict_does_not_ask(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _src = _advanced(make, tmp_path, "webp")  # kot.png -> kot.webp, wolne
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)
    win._start_convert_subset(win._queue)
    assert calls == [] and len(runs) == 1


def test_advanced_output_folder_asks_only_when_option_is_checked(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, _app, _ = make_window
    win, _src = _advanced(make, tmp_path, "webp")
    out = tmp_path / "wyjscie"
    out.mkdir()
    _png(out / "kot.webp")  # zajęta nazwa w folderze wyjściowym
    win.output_enabled_cb.setChecked(True)
    win.output_dir_edit.setText(str(out))
    calls = _spy_dialog(monkeypatch, "suffix")
    runs = _spy_run(win, monkeypatch)

    win.overwrite_cb.setChecked(False)  # bez „Pytaj przed nadpisaniem”: nadpisuje bez pytania (jak dotąd)
    win._start_convert_subset(win._queue)
    assert calls == [] and runs[0][0][0].output_path == out / "kot.webp" and runs[0][1]["overwrite"] is True

    win.overwrite_cb.setChecked(True)
    win._start_convert_subset(win._queue)
    assert len(calls) == 1 and calls[0]["same_as_source"] is False
    assert runs[1][0][0].output_path == out / "kot_conv.webp"


def test_advanced_info_label_follows_toggles(make_window, tmp_path):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="advanced")
    label = win.advanced_save_info_label
    assert label.objectName() == "saveInfo"
    assert _plain(label.text()) == f"Zapis obok oryginałów. {ASK_TAIL}"
    win.output_enabled_cb.setChecked(True)
    assert _plain(label.text()) == f"Zapis do folderu wyjściowego. {ASK_TAIL}"
    win.overwrite_cb.setChecked(False)
    assert _plain(label.text()) == "Zapis do folderu wyjściowego. Pliki o tych samych nazwach zostaną nadpisane bez pytania."
    win.output_enabled_cb.setChecked(False)
    assert _plain(label.text()) == f"Zapis obok oryginałów. {ASK_TAIL}"


def test_old_per_file_overwrite_dialog_is_gone():
    from inyfinn_resizer.app.dialogs import message_boxes

    assert not hasattr(message_boxes, "ask_overwrite_inplace")
    assert not hasattr(mw.MainWindow, "_filter_jobs_with_inplace_confirm")


# ——— białe pole na pliki (S79) ———


def test_drop_field_is_a_white_field_inside_a_normal_panel(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    themes.apply_theme(app, "dobra-kaloria-zielen-jasny")
    field = win.findChild(QFrame, "dropField")
    assert field is not None
    tile = field.parentWidget()
    while tile is not None and tile.objectName() != "bentoTile":
        tile = tile.parentWidget()
    assert tile is not None and tile.property("variant") == "panel"  # panel L1, nie jedna wielka strefa z ramką
    assert win._simple_empty.parentWidget() is field and win.simple_file_list.parentWidget() is field
    # nagłówek, przyciski i licznik zostają na panelu, nie w białym polu
    assert not field.findChildren(QLabel, "sectionStepTitle") and not field.findChildren(QLabel, "queueCount")
    app.processEvents()
    t = themes._THEME_TOKENS["dobra-kaloria-zielen-jasny"]
    assert t["@BG_PANEL_ALT@"].upper() == "#FFFFFF" and t["@BG_PANEL@"].upper() == "#F8F7F5"
    image = field.grab().toImage()
    assert image.pixelColor(40, image.height() // 2).name().upper() == "#FFFFFF"  # białe pole
    tile_image = tile.grab().toImage()
    assert tile_image.pixelColor(6, tile_image.height() // 2).name().upper() == "#F8F7F5"  # panel wokół


def test_drop_field_qss_and_rows_use_the_list_tokens():
    import re

    theme = "dobra-kaloria-zielen-jasny"
    t = themes._THEME_TOKENS[theme]
    qss = themes.render_qss(theme)
    rules = {sel.strip(): body for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", qss)}
    field = next(b for s, b in rules.items() if s.endswith("QFrame#dropField"))
    assert t["@BG_PANEL_ALT@"] in field and t["@DROP_BORDER@"] in field and "dashed" in field
    assert t["@RADIUS_DROP@"] in field
    row = next(b for s, b in rules.items() if s.endswith("QListWidget#simpleFileList::item"))
    assert t["@LIST_ROW_LINE@"] in row and t["@BG_PANEL_ALT@"] in row and "margin: 0" in row  # linia 1 px zamiast odstępu
    icon = next(b for s, b in rules.items() if s.endswith("QLabel#dropEmptyIcon"))
    assert t["@BG_PANEL@"] in icon  # kwadrat z ikoną widać na bieli


def test_window_still_takes_drops_when_files_sit_in_the_field(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="simple")
    assert win.acceptDrops()
    for w in (win.findChild(QFrame, "dropField"), win.simple_file_list.viewport(), win._simple_empty):
        p = w
        while p is not None and not p.acceptDrops():
            p = p.parentWidget()
        assert p is win


# ——— oddech (S80) ———


@pytest.mark.parametrize("level, gap", [(0, 20), (1, 16), (2, 12)])
def test_simple_rows_have_more_air_and_still_follow_density(make_window, level, gap):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    win._apply_density(level)
    assert win._simple_folder_grid._vgap == gap and win._simple_format_grid._vgap == gap
    assert win.simple_video_tile._vgap == gap and win._simple_format_lay.spacing() == gap
    assert [d.section_gap for d in mw.DENSITIES] == [70, 48, 28]  # odstęp między częściami bez zmian


def test_tile_description_does_not_touch_its_title(make_window):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    tile = win._simple_center.findChildren(QFrame, "bentoTile")[0]  # strefa plików trybu prostego
    title, hint = tile.findChild(QLabel, "sectionStepTitle"), tile.findChild(QLabel, "sectionStepHint")
    assert hint.geometry().top() - title.geometry().bottom() - 1 >= 6


def test_narrow_simple_window_still_shows_every_row_without_scrolling(make_window, tmp_path):  # noqa: F811
    make, app, _ = make_window
    win, _paths = _simple(make, tmp_path, "a.png", "b.png")
    film = tmp_path / "klip.mov"
    film.write_bytes(b"")
    win._add_path_to_queue(film)
    win._refresh_simple_file_list()
    win.resize(960, win.height())
    app.processEvents()
    win._fit_window(initial=False)
    for _ in range(4):
        app.processEvents()
    assert win.simple_video_tile.isVisible()
    assert win._simple_scroll.verticalScrollBar().maximum() == 0


# ——— GIF: jedna droga naraz, nic wyszarzonego (S81) ———


def _gif_dialog(app, opts: FormatOptions | None = None) -> FormatSettingsDialog:
    from PySide6.QtCore import Qt

    dlg = FormatSettingsDialog("gif", opts or FormatOptions())
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    for _ in range(4):
        app.processEvents()
    return dlg


def _visible(widget) -> bool:
    return widget.isVisibleTo(widget.window())


@pytest.fixture()
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


GIF_HINTS = {
    "quality": "Zostają 2 z 3 klatek, obraz traci trochę kolorów i drobnych detali. Animacja trwa tyle samo.",
    "frames": "Obraz bez zmian, wypada część klatek. Pauzy i długość animacji zostają.",
    "ultra": "Zostają tylko najdłuższe zatrzymania obrazu i ostatnia klatka. Najmniejszy plik.",
}


def test_gif_mode_is_a_single_choice_pill_group(app):
    dlg = _gif_dialog(app)
    try:
        pills = dlg._gif_mode
        assert [pills.button(k).text() for k in pills.keys()] == ["Jakość", "Mniej klatek", "ULTRA"]
        assert pills.keys() == ["quality", "frames", "ultra"] and pills.value() == "quality"
        assert not isinstance(pills, QComboBox)
        for key, text in GIF_HINTS.items():
            pills.set_value(key, emit=True)
            assert _plain(dlg._gif_mode_hint.text()) == text
    finally:
        dlg.close()


def test_gif_shows_only_the_fields_of_the_chosen_method_and_disables_nothing(app):
    dlg = _gif_dialog(app)
    try:
        everything = [dlg._gif_from_quality, dlg._gif_quality_info, dlg._gif_lossy, dlg._gif_lossy_hint, dlg._gif_level,
                      dlg._gif_ultra_frames, dlg._gif_ultra_lossy]
        expect = {
            "quality": [dlg._gif_from_quality, dlg._gif_quality_info],  # „Z suwaka” zaznaczone: ręczny lossy ukryty
            "frames": [dlg._gif_level],
            "ultra": [dlg._gif_ultra_frames, dlg._gif_ultra_lossy],
        }
        for mode, shown in expect.items():
            dlg._gif_mode.set_value(mode, emit=True)
            for _ in range(2):
                app.processEvents()
            assert [w for w in everything if _visible(w)] == shown, mode
            assert _visible(dlg._gif_dither)  # dithering zawsze
        gif = dlg._sections["gif"]
        controls = (QSpinBox, QComboBox, QCheckBox, QAbstractButton)
        stuck = [w for w in gif.findChildren(QWidget) if isinstance(w, controls) and w.isVisibleTo(dlg) and not w.isEnabled()]
        assert stuck == []  # nic „nie do kliknięcia”: pola nieużywane są ukryte, nie wyszarzone
    finally:
        dlg.close()


def test_gif_quality_method_info_line_and_manual_lossy(app):
    opts = FormatOptions(quality=50, gif_max_colors=128)
    dlg = _gif_dialog(app, opts)
    try:
        assert dlg._gif_mode.value() == "quality" and dlg._gif_from_quality.isChecked()
        assert _plain(dlg._gif_quality_info.text()) == "Teraz: 160 kolorów, lossy 100 (suwak Jakość 50%)"
        assert not _visible(dlg._gif_lossy)
        dlg._gif_from_quality.setChecked(False)
        app.processEvents()
        assert _visible(dlg._gif_lossy) and _visible(dlg._gif_lossy_hint) and dlg._gif_lossy.isEnabled()
        assert _plain(dlg._gif_lossy_hint.text()) == (
            "0 = bez lossy. Liczbę kolorów ustawiasz w oknie głównym (Liczba kolorów)."
        )
        assert dlg._gif_quality_info.text() == "Kolory: 128"
        dlg._gif_lossy.setValue(0)
        assert dlg.get_options().gif_lossy == 0 and not dlg.get_options().gif_from_quality
    finally:
        dlg.close()


def test_gif_frames_dropdown_lists_ten_to_one_and_round_trips(app):
    dlg = _gif_dialog(app, FormatOptions(gif_mode="frames", gif_level=3))
    try:
        combo = dlg._gif_level
        assert [combo.itemData(i) for i in range(combo.count())] == list(range(10, 0, -1))
        assert combo.itemText(0) == "90% klatek — prawie bez zmian" and combo.itemText(9) == "15% klatek — max redukcja"
        assert combo.currentData() == 3 and dlg._gif_mode.value() == "frames" and _visible(combo)
        combo.setCurrentIndex(combo.findData(8))
        opts = dlg.get_options()
        assert opts.gif_mode == "frames" and opts.gif_level == 8
    finally:
        dlg.close()


def test_gif_ultra_fields_round_trip_and_reset(app):
    dlg = _gif_dialog(app, FormatOptions(gif_mode="ultra", gif_ultra_max_frames=6, gif_ultra_lossy=33))
    try:
        assert dlg._gif_ultra_frames.value() == 6 and dlg._gif_ultra_lossy.value() == 33
        assert (dlg._gif_ultra_frames.minimum(), dlg._gif_ultra_frames.maximum()) == (2, 8)
        assert (dlg._gif_ultra_lossy.minimum(), dlg._gif_ultra_lossy.maximum()) == (0, 200)
        opts = dlg.get_options()
        assert (opts.gif_mode, opts.gif_ultra_max_frames, opts.gif_ultra_lossy) == ("ultra", 6, 33)
        dlg._reset()
        app.processEvents()
        assert dlg._gif_mode.value() == "quality" and _visible(dlg._gif_from_quality) and not _visible(dlg._gif_ultra_frames)
    finally:
        dlg.close()


def test_film_to_gif_pills_show_only_their_fields(app):
    dlg = _gif_dialog(app, FormatOptions(video_mode="smooth", video_fps=15.0, video_max_frames=200, video_ultra_frames=9))
    try:
        pills = dlg._video_mode
        assert [pills.button(k).text() for k in pills.keys()] == ["Płynnie", "ULTRA"] and pills.value() == "smooth"
        smooth = [dlg._video_fps, dlg._video_frames, dlg._video_frames_hint]
        assert all(_visible(w) for w in smooth) and not _visible(dlg._video_ultra_frames)
        assert dlg._video_fps.suffix() == " kl/s" and (dlg._video_fps.minimum(), dlg._video_fps.maximum()) == (1, 30)
        assert (dlg._video_frames.minimum(), dlg._video_frames.maximum()) == (2, 900)
        assert _plain(dlg._video_frames_hint.text()) == (
            "Bezpiecznik dla długich filmów: klatki rozłożą się równo, film nie zostanie ucięty."
        )
        pills.set_value("ultra", emit=True)
        app.processEvents()
        assert _visible(dlg._video_ultra_frames) and not any(_visible(w) for w in smooth)
        assert (dlg._video_ultra_frames.minimum(), dlg._video_ultra_frames.maximum()) == (2, 300)
        assert _visible(dlg._video_scale)  # rozmiar zawsze
        opts = dlg.get_options()
        assert (opts.video_mode, opts.video_fps, opts.video_max_frames, opts.video_ultra_frames) == ("ultra", 15.0, 200, 9)
    finally:
        dlg.close()


def test_gif_labels_are_explicit_with_units(app):
    dlg = _gif_dialog(app)
    try:
        gif = dlg._sections["gif"]
        labels = {lbl.text() for lbl in gif.findChildren(QLabel)}
        for wanted in ("Zostaw klatek", "Najwyżej klatek", "Klatki na sekundę", "Najwięcej klatek", "Liczba zatrzymań"):
            assert wanted in labels, wanted
        assert not any("Poziom" in t or "Tryb kompresji" in t or "ULTRA —" in t for t in labels)
    finally:
        dlg.close()


# ——— rdzeń: lossy 0 w sposobie „Jakość” ———


def _fake_gifsicle(monkeypatch, frames: int = 6):
    seen: dict = {}
    monkeypatch.setattr(gifmod, "find_tool", lambda name: Path("gifsicle.exe"))
    monkeypatch.setattr(gifmod, "read_gif_info", lambda src: (frames, [100] * frames, (8, 8)))

    def fake_encode(gifsicle, src, dst, indices, durs, **kw):
        seen.update(indices=indices, **kw)

    monkeypatch.setattr(gifmod, "encode_gif", fake_encode)
    return seen


def test_compress_gif_quality_uses_custom_colors_even_with_lossy_zero(monkeypatch, tmp_path):
    seen = _fake_gifsicle(monkeypatch)
    ok, msg = gifmod.compress_gif(tmp_path / "a.gif", tmp_path / "b.gif", mode="quality", level=6, colors=128, lossy=0)
    assert ok and seen["colors"] == 128 and seen["lossy"] == 0  # nie po cichu preset poziomu 6 (256 kolorów, lossy 80)
    assert seen["indices"] == gifmod.indices_2of3(6) and "custom colors=128 lossy=0" in msg


def test_compress_gif_quality_keeps_custom_lossy_and_falls_back_to_level_only_without_colors(monkeypatch, tmp_path):
    seen = _fake_gifsicle(monkeypatch)
    gifmod.compress_gif(tmp_path / "a.gif", tmp_path / "b.gif", mode="quality", colors=64, lossy=90)
    assert seen["colors"] == 64 and seen["lossy"] == 90
    gifmod.compress_gif(tmp_path / "a.gif", tmp_path / "b.gif", mode="quality", level=4, colors=None, lossy=0)
    preset = gifmod.QUALITY_PRESETS[4]
    assert (seen["colors"], seen["lossy"]) == (preset.colors, preset.lossy)


def test_compress_gif_other_modes_unchanged(monkeypatch, tmp_path):
    seen = _fake_gifsicle(monkeypatch, frames=10)
    gifmod.compress_gif(tmp_path / "a.gif", tmp_path / "b.gif", mode="frames", level=3, colors=128, lossy=0)
    assert seen["colors"] == 256 and seen["lossy"] == 0
    assert len(seen["indices"]) == len(gifmod.pick_indices(10, gifmod.FRAME_PRESETS[3].keep_pct))
