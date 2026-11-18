"""2.6.11: preset sieci w trybie prostym (Rossmann): EAN sam, role plików do zmiany, kolizje przy pliku."""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QRect

from test_window_fit import make_window  # noqa: F401  (fixture: okno z zadanym ekranem)

BIG = QRect(0, 0, 1920, 1152)
EAN = "5903548004897"


def _product(tmp_path):
    prod = tmp_path / "2026-02-24-6300754-KULKI-65g"
    (prod / "1-MATERIAŁY").mkdir(parents=True)
    (prod / "1-MATERIAŁY" / f"6300754 - EAN{EAN}.txt").write_text("", encoding="utf-8")
    wiz = prod / "4-WIZKI" / "INTERNET-PREZENTACJE-RGB"
    wiz.mkdir(parents=True)
    files = []
    for side, size in (("FRONT", (40, 60)), ("TYŁ", (40, 60)), ("FRONT-S", (20, 30))):
        p = wiz / f"DK-KULKI-6300754-RGB-{side}.png"
        im = Image.new("RGBA", size, (0, 0, 0, 0))
        im.paste((200, 40, 90, 255), (2, 2, size[0] - 2, size[1] - 2))
        im.save(p)
        files.append(p.resolve())
    jpg = wiz / "DK-KULKI-6300754-RGB-FRONT.jpg"  # ten sam front jako JPG: PNG ma pierwszeństwo
    Image.new("RGB", (80, 120), (200, 40, 90)).save(jpg)
    files.append(jpg.resolve())
    return files


def test_simple_mode_rossmann_names_roles_and_collisions(make_window, tmp_path, monkeypatch):  # noqa: F811
    make, app, _ = make_window
    win = make(BIG, mode="simple")
    files = _product(tmp_path)
    for p in files:
        win._add_path_to_queue(p)
    win._update_queue_label()
    win.simple_retail_combo.setCurrentIndex(win.simple_retail_combo.findData("rossmann"))
    app.processEvents()
    assert win.retail_preset_combo.currentData() == "rossmann"  # jeden wybór sieci w obu trybach
    assert win._retail_panel.isVisible() and win._retail_panel.parent() is not None
    assert not win.simple_format_pills.isVisible()  # format ustala preset
    assert win._retail_panel.ean_edit.text() == EAN
    assert win._retail_panel.verdict.property("state") == "ok"
    # FRONT, FRONT-S i FRONT.jpg: program sam wybiera FRONT.png (PNG przed JPG, potem większy), reszta „Pomiń”
    from inyfinn_resizer.core.ean import SKIP_ROLE

    assert win._role_for(files[0]) == "g" and win._role_for(files[1]) == "t"
    assert win._role_for(files[2]) == SKIP_ROLE and win._role_for(files[3]) == SKIP_ROLE
    assert win._retail_problems(files) == {}
    assert "pominę 2 duplikaty" in win._retail_panel.summary.text()
    item = win.simple_file_list.item(0)
    assert win.simple_file_list.itemWidget(item) is not None  # rola wybierana w wierszu listy plików
    assert not win._retail_panel._rows_box.isVisible()  # drugiej listy w trybie prostym nie ma
    runs = []
    monkeypatch.setattr(win, "_run_jobs", lambda jobs, **kw: runs.append(jobs))
    win._start_simple_convert()
    assert sorted(j.output_path.name for j in runs[-1]) == [f"{EAN}_g.png", f"{EAN}_t.png"]
    assert win._skipped_dupes == 2
    # ręcznie ta sama rola co inny plik = czerwony błąd przy pliku i konwersja nie rusza
    win._on_role_changed(files[2], "g")
    app.processEvents()
    assert set(win._retail_problems(files)) == {files[0], files[2]}
    warnings = []
    monkeypatch.setattr("inyfinn_resizer.app.main_window.show_warning", lambda *a, **k: warnings.append(a))
    win._start_simple_convert()
    assert warnings and len(runs) == 1
    # rola zmieniona na „front”: trzy pliki, jeden pominięty
    win._on_role_changed(files[2], "fr")
    app.processEvents()
    win._start_simple_convert()
    jobs = runs[-1]
    assert sorted(j.output_path.name for j in jobs) == [f"{EAN}_fr.png", f"{EAN}_g.png", f"{EAN}_t.png"]
    assert {j.retail_id for j in jobs} == {"rossmann"} and {j.output_format for j in jobs} == {"png"}


def test_jpg_without_model_asks_before_conversion(make_window, tmp_path, monkeypatch):  # noqa: F811
    from inyfinn_resizer.core.transforms import rmbg_models

    make, app, _ = make_window
    win = make(BIG, mode="simple")
    jpg = tmp_path / "X-6300754-RGB-TYŁ.jpg"
    Image.new("RGB", (60, 80), (200, 40, 90)).save(jpg)
    win._add_path_to_queue(jpg)
    win._update_queue_label()
    win.simple_retail_combo.setCurrentIndex(win.simple_retail_combo.findData("rossmann"))
    win._on_ean_edited(EAN)
    monkeypatch.setattr(rmbg_models, "is_ready", lambda _m: False)
    asked = []
    monkeypatch.setattr("inyfinn_resizer.app.main_window.ask_yes_no", lambda *a, **k: asked.append(a) or False)
    runs = []
    monkeypatch.setattr(win, "_run_jobs", lambda jobs, **kw: runs.append(jobs))
    win._start_simple_convert()
    assert asked and "nie ma przezroczystego tła" in asked[0][2] and not runs


def test_manual_ean_is_validated(make_window):  # noqa: F811
    make, _app, _ = make_window
    win = make(BIG, mode="advanced")
    win.retail_preset_combo.setCurrentIndex(win.retail_preset_combo.findData("rossmann"))
    win._on_ean_edited("5903548004898")  # zła cyfra kontrolna
    assert win._retail_panel.verdict.property("state") == "bad"
    win._on_ean_edited(EAN)
    assert win._retail_panel.verdict.property("state") == "ok" and win._retail_card.isVisibleTo(win)
