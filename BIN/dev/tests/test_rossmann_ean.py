"""Preset Rossmann 2026: kadr do treści, wymiary, 5 MB, nazwy EAN_rola, źródła EAN."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from inyfinn_resizer.core.ean import (
    detect_ean,
    ean13_valid,
    ean_from_excel,
    ean_from_txt,
    find_product_dir,
    output_name,
    role_collisions,
    role_from_name,
)
from inyfinn_resizer.core.retail_export import export_retail, target_size, trim_to_content
from inyfinn_resizer.core.retail_presets import retail_preset_by_id

EAN = "5903548004897"


def _product(tmp_path: Path, index: str = "6300754") -> Path:
    prod = tmp_path / f"2026-02-24-{index}-MAGNEZ-&-ŻELAZO-65g"
    (prod / "1-MATERIAŁY" / "KARTA-WPROWADZENIA").mkdir(parents=True)
    (prod / "4-WIZKI" / "INTERNET-PREZENTACJE-RGB").mkdir(parents=True)
    return prod


def _packshot(path: Path, size=(900, 1400), box=(100, 150, 800, 1250)) -> Path:
    im = Image.new("RGBA", size, (255, 255, 255, 0))
    im.paste((120, 60, 160, 255), box)
    im.putpixel((5, 5), (255, 255, 255, 3))  # mgiełka tła, niewidoczna na jasnym
    im.save(path)
    return path


def test_ean13_checksum():
    assert ean13_valid(EAN) and ean13_valid("5903548004903")
    assert not ean13_valid("5903548004898") and not ean13_valid("590354800489")


def test_roles_names_and_collisions():
    assert role_from_name("DK-DOY-KULKI-MALINA-65-G-MAGNEZ-ŻELAZO-6300754-RGB-FRONT.png") == "g"
    assert role_from_name("DK-DOY-KULKI-MALINA-65-G-6300754-RGB-TYŁ.png") == "t"
    assert role_from_name("cos.png") == ""
    assert output_name(EAN, "g") == "5903548004897_g.png"
    clash = role_collisions({Path("a-FRONT.png"): "g", Path("a-FRONT-S.png"): "g", Path("a-TYŁ.png"): "t"})
    assert list(clash) == ["g"]


def test_trim_and_size_rules():
    im = trim_to_content(Image.open(_packshot_mem()))
    assert im.size == (700, 1100)
    assert target_size(700, 1100, 1200, 3800)[:2] == (1200, 1886)  # krótszy bok do 1200
    w, h, note = target_size(500, 4000, 1200, 3800)  # konflikt: wygrywa 3800 + komunikat
    assert h == 3800 and w < 1200 and "Proporcje" in note


def _packshot_mem():
    import io

    buf = io.BytesIO()
    im = Image.new("RGBA", (900, 1400), (255, 255, 255, 0))
    im.paste((120, 60, 160, 255), (100, 150, 800, 1250))
    im.putpixel((5, 5), (255, 255, 255, 3))
    im.save(buf, "PNG")
    buf.seek(0)
    return buf


def test_export_rossmann_zero_margin_and_limits(tmp_path):
    src = _packshot(tmp_path / "X-FRONT.png")
    out = tmp_path / output_name(EAN, "g")
    export_retail(src, out, retail_preset_by_id("rossmann"))
    im = Image.open(out)
    a = np.asarray(im.convert("RGBA").getchannel("A"))
    assert im.format == "PNG" and min(im.size) == 1200 and max(im.size) <= 3800
    assert a[0].any() and a[-1].any() and a[:, 0].any() and a[:, -1].any()  # 0 px marginesu
    assert out.stat().st_size <= 5 * 1024 * 1024


def test_export_noise_over_5mb_is_compressed(tmp_path):
    rng = np.random.default_rng(1)
    arr = rng.integers(0, 255, (2400, 2400, 4), dtype=np.uint8)
    arr[..., 3] = 255
    arr[:, :40, 3] = 0  # przezroczysty pasek = plik ma już wycięte tło
    src = tmp_path / "szum-FRONT.png"
    Image.fromarray(arr, "RGBA").save(src)
    out = tmp_path / "o.png"
    notes = export_retail(src, out, retail_preset_by_id("rossmann"))
    assert out.stat().st_size <= 5 * 1024 * 1024
    assert min(Image.open(out).size) >= 1200
    assert notes


def test_ean_sources_excel_txt_barcode(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    prod = _product(tmp_path)
    wiz = prod / "4-WIZKI" / "INTERNET-PREZENTACJE-RGB" / "X-6300754-RGB-FRONT.png"
    _packshot(wiz)
    assert find_product_dir(wiz) == prod
    # karta innego produktu jest pomijana
    wb = openpyxl.Workbook()
    wb.active["B19"] = "5903548004941"
    wb.save(prod / "1-MATERIAŁY" / "KARTA-WPROWADZENIA" / "Karta-wprowadzenia_inne-6300726.xlsx")
    found, notes = ean_from_excel(prod, "6300754")
    assert not found and "6300726" in notes[0]
    wb = openpyxl.Workbook()
    wb.active["B19"] = EAN
    wb.save(prod / "1-MATERIAŁY" / "KARTA-WPROWADZENIA" / "Karta-wprowadzenia_kulki-6300754.xlsx")
    assert ean_from_excel(prod, "6300754")[0][0].ean == EAN
    (prod / "1-MATERIAŁY" / "6300726 - EAN5903548004941.txt").write_text("", encoding="utf-8")
    (prod / "1-MATERIAŁY" / "6300754 - EAN5903548004903.txt").write_text("", encoding="utf-8")
    txt, notes = ean_from_txt(prod, "6300754")
    assert [f.ean for f in txt] == ["5903548004903"] and "6300726" in notes[0]
    res = detect_ean([wiz])
    # plik <indeks> - EAN….txt ma pierwszeństwo przed kartą; karta i plik się różnią: program pyta
    assert res.ean == "5903548004903" and res.source == "z pliku 6300754 - EAN5903548004903.txt" and res.conflict


def test_ean_from_barcode(tmp_path):
    zxingcpp = pytest.importorskip("zxingcpp")
    code = zxingcpp.create_barcode(EAN, zxingcpp.BarcodeFormat.EAN13)
    img = Image.fromarray(np.asarray(zxingcpp.write_barcode_to_image(code, scale=4)))
    prod = _product(tmp_path)
    back = prod / "4-WIZKI" / "INTERNET-PREZENTACJE-RGB" / "X-RGB-TYŁ.png"
    canvas = Image.new("RGB", (img.width + 80, img.height + 80), "white")
    canvas.paste(img.convert("RGB"), (40, 40))
    canvas.save(back)
    res = detect_ean([back])
    assert res.ean == EAN and res.source == "z kodu kreskowego na zdjęciu tyłu"


def test_presets_json_matches_source(tmp_path):
    import json
    from dataclasses import asdict

    from inyfinn_resizer.core.ean import ROLE_WORDS
    from inyfinn_resizer.core.retail_presets import RETAIL_PRESETS, SCHEMA_VERSION, write_presets_json

    out = tmp_path / "retail_presets.json"
    write_presets_json(out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert [{k: v for k, v in p.items() if k != "resize"} for p in data["presets"]] == [
        asdict(p) for p in RETAIL_PRESETS
    ]
    assert [(tuple(r["words"]), r["role"]) for r in data["roles"]] == ROLE_WORDS
    assert data["naming"]["ean_role"].format(ean=EAN, role="g", ext=".png") == output_name(EAN, "g")


@pytest.mark.parametrize("preset_id", ["aldi_cms", "dm", "amazon_allegro", "amazon_main"])
def test_canvas_presets_keep_whole_product(tmp_path, preset_id):
    """Wysoka wizka (jak DOY 2268x2480): po presecie sieci cały produkt jest w kadrze, kwadrat N x N."""
    preset = retail_preset_by_id(preset_id)
    src = tmp_path / "doy-FRONT.png"
    im = Image.new("RGBA", (1134, 1240), (0, 0, 0, 0))
    im.paste((200, 40, 90, 255), (60, 20, 1074, 1220))  # produkt prawie do góry i dołu
    im.paste((10, 10, 10, 255), (60, 20, 1074, 40))  # ciemny pasek na samej górze produktu
    im.paste((10, 10, 10, 255), (60, 1200, 1074, 1220))  # i na samym dole
    im.save(src)
    out = tmp_path / f"o.{'jpg' if preset.output_format == 'jpeg' else 'png'}"
    export_retail(src, out, preset)
    res = Image.open(out)
    assert res.size == (preset.canvas_px, preset.canvas_px)
    rgb = np.asarray(res.convert("RGB")).astype(int)
    dark = (rgb.sum(axis=2) < 120).any(axis=1)
    assert dark[:3].any() and dark[-3:].any()  # góra i dół produktu są w kadrze (nie obcięte)
    if preset.output_format == "png":
        a = np.asarray(res.convert("RGBA").getchannel("A"))
        assert a[:, 0].max() == 0 and a[:, -1].max() == 0  # boki dopełnione przezroczystością
    else:
        assert tuple(rgb[preset.canvas_px // 2, 0]) == (255, 255, 255)  # boki białe


def test_resolve_roles_picks_png_then_bigger_and_keeps_ties(tmp_path):
    from inyfinn_resizer.core.ean import SKIP_ROLE, resolve_roles

    big, small, jpg = tmp_path / "A-FRONT.png", tmp_path / "A-FRONT-S.png", tmp_path / "A-FRONT.jpg"
    Image.new("RGBA", (40, 60)).save(big)
    Image.new("RGBA", (20, 30)).save(small)
    Image.new("RGB", (400, 600)).save(jpg)
    res = resolve_roles([small, jpg, big])
    assert res[big] == ("g", "") and res[small][0] == SKIP_ROLE and res[jpg][0] == SKIP_ROLE
    assert res[small][1] == "wybrano większy plik: A-FRONT.png"
    assert resolve_roles([small, big], manual={small: "g"})[small] == ("g", "")  # ręczna rola zostaje
    twin = tmp_path / "B-FRONT.png"
    Image.new("RGBA", (40, 60)).save(twin)
    tie = resolve_roles([big, twin])
    assert tie[big][0] == tie[twin][0] == "g"  # remis: nie zgadujemy, człowiek wybiera
