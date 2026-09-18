"""Presety sieci handlowych — ile % powierzchni zdjęcia ucina realny resize.

FIT_BOX działa jak „cover”: skaluje do pokrycia kwadratu i przycina nadmiar.
Test utrwala OBECNE zachowanie (nie ocenia go) — tabela trafia do raportu,
decyzję o ewentualnym „contain” + dopełnieniu tłem podejmuje użytkownik.

Pomiar: syntetyczny obraz z gradientem R = x, G = y. Po resize wartości R/G
na krawędziach wyniku mówią, który fragment źródła został zachowany.
Uruchomienie jako skrypt drukuje tabelę: python tests/test_retail_presets_crop.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inyfinn_resizer.core.job import ResizeMode  # noqa: E402
from inyfinn_resizer.core.retail_presets import (  # noqa: E402
    RETAIL_PRESETS,
    retail_snapshot_from_preset,
)
from inyfinn_resizer.core.transforms.pillow_ops import (  # noqa: E402
    apply_resize_pil,
    apply_scale_postprocess_pil,
)

# Najdłuższa krawędź 4000 px — większa od każdego presetu, więc ONE_SIDE nie jest pomijany.
ASPECTS: dict[str, tuple[int, int]] = {
    "1:1": (4000, 4000),
    "3:4": (3000, 4000),
    "4:3": (4000, 3000),
    "16:9": (4000, 2250),
}

# Obecne zachowanie: preset → wymiar wyjścia dla każdej proporcji i oczekiwany % ucięcia.
_COVER = {"1:1": 0.0, "3:4": 25.0, "4:3": 25.0, "16:9": 43.75}
_NO_CROP = {k: 0.0 for k in ASPECTS}

EXPECTED: dict[str, dict[str, object]] = {
    "aldi_cms": {"crop": _COVER, "size": {k: (1920, 1920) for k in ASPECTS}, "fmt": "png", "bg": True},
    "aldi_print": {
        "crop": _NO_CROP,
        "size": {"1:1": (2400, 2400), "3:4": (1800, 2400), "4:3": (2400, 1800), "16:9": (2400, 1350)},
        "fmt": "jpeg",
        "bg": False,
    },
    "dm": {"crop": _COVER, "size": {k: (2000, 2000) for k in ASPECTS}, "fmt": "png", "bg": True},
    "rossmann": {"crop": _COVER, "size": {k: (2500, 2500) for k in ASPECTS}, "fmt": "webp", "bg": True},
    "lidl": {"crop": _NO_CROP, "size": dict(ASPECTS), "fmt": "jpeg", "bg": False},
    "amazon_allegro": {"crop": _COVER, "size": {k: (1200, 1200) for k in ASPECTS}, "fmt": "png", "bg": True},
    "amazon_main": {"crop": _COVER, "size": {k: (3000, 3000) for k in ASPECTS}, "fmt": "jpeg", "bg": False},
    "auchan": {
        "crop": _NO_CROP,
        "size": {"1:1": (1200, 1200), "3:4": (900, 1200), "4:3": (1200, 900), "16:9": (1200, 675)},
        "fmt": "jpeg",
        "bg": False,
    },
}


@dataclass(frozen=True)
class CropRow:
    preset_id: str
    aspect: str
    out_size: tuple[int, int]
    cropped_pct: float


def _gradient_image(w: int, h: int) -> Image.Image:
    """R rośnie od lewej do prawej, G od góry do dołu."""
    vertical = Image.linear_gradient("L")
    g = vertical.resize((w, h), Image.Resampling.BILINEAR)
    # rotate(90) jest przeciwnie do wskazówek zegara: góra (0) trafia na lewą krawędź.
    r = vertical.rotate(90, expand=True).resize((w, h), Image.Resampling.BILINEAR)
    b = Image.new("L", (w, h), 0)
    return Image.merge("RGB", (r, g, b))


def _kept_fraction(out: Image.Image) -> float:
    arr = np.asarray(out.convert("RGB"), dtype=np.float64)
    # Mediana z pasa 3 px ogranicza wpływ filtra Lanczos na samej krawędzi.
    x0 = np.median(arr[:, :3, 0])
    x1 = np.median(arr[:, -3:, 0])
    y0 = np.median(arr[:3, :, 1])
    y1 = np.median(arr[-3:, :, 1])
    kept_x = min(1.0, max(0.0, (x1 - x0) / 255.0))
    kept_y = min(1.0, max(0.0, (y1 - y0) / 255.0))
    return kept_x * kept_y


def measure_preset(preset_id: str, aspect: str) -> CropRow:
    preset = next(p for p in RETAIL_PRESETS if p.id == preset_id)
    resize = retail_snapshot_from_preset(preset)["resize"]
    w, h = ASPECTS[aspect]
    out = apply_resize_pil(_gradient_image(w, h), resize)
    out = apply_scale_postprocess_pil(out, resize)
    cropped = 0.0 if out.size == (w, h) else (1.0 - _kept_fraction(out)) * 100.0
    return CropRow(preset_id, aspect, out.size, round(cropped, 1))


def crop_table() -> list[CropRow]:
    return [measure_preset(p.id, a) for p in RETAIL_PRESETS for a in ASPECTS]


def test_every_retail_preset_is_covered() -> None:
    assert {p.id for p in RETAIL_PRESETS} == set(EXPECTED)


@pytest.mark.parametrize("preset_id", sorted(EXPECTED))
def test_preset_format_and_background(preset_id: str) -> None:
    preset = next(p for p in RETAIL_PRESETS if p.id == preset_id)
    snap = retail_snapshot_from_preset(preset)
    assert snap["output_format"] == EXPECTED[preset_id]["fmt"]
    assert snap["remove_background"] is EXPECTED[preset_id]["bg"]
    assert snap["transforms"].remove_background is EXPECTED[preset_id]["bg"]


@pytest.mark.parametrize("aspect", list(ASPECTS))
@pytest.mark.parametrize("preset_id", sorted(EXPECTED))
def test_preset_crop_percentage(preset_id: str, aspect: str) -> None:
    row = measure_preset(preset_id, aspect)
    assert row.out_size == EXPECTED[preset_id]["size"][aspect]
    expected = EXPECTED[preset_id]["crop"][aspect]
    # Pomiar z gradientu 8-bit — tolerancja 1,5 pp.
    assert row.cropped_pct == pytest.approx(expected, abs=1.5)


def test_box_presets_use_cover_mode() -> None:
    """Kwadratowe presety sieci to FIT_BOX (cover) — przycinają, a nie dopełniają tłem."""
    box_ids = {pid for pid, exp in EXPECTED.items() if exp["crop"] is _COVER}
    for preset in RETAIL_PRESETS:
        resize = retail_snapshot_from_preset(preset)["resize"]
        assert (resize.mode == ResizeMode.FIT_BOX) == (preset.id in box_ids)


def test_vips_cover_crops_like_pillow() -> None:
    """Ścieżka libvips (_fit_cover_crop) daje ten sam wymiar i kadr co Pillow."""
    from inyfinn_resizer.core.pipeline import _init_vips

    if not _init_vips():
        pytest.skip("libvips niedostępny")
    import pyvips

    from inyfinn_resizer.core.transforms.image_ops import apply_resize, apply_scale_postprocess

    preset = next(p for p in RETAIL_PRESETS if p.id == "aldi_cms")
    resize = retail_snapshot_from_preset(preset)["resize"]
    w, h = ASPECTS["16:9"]
    src = _gradient_image(w, h)
    vimg = pyvips.Image.new_from_memory(src.tobytes(), w, h, 3, "uchar")
    vout = apply_scale_postprocess(apply_resize(vimg, resize), resize)
    arr = np.ndarray(
        buffer=vout.write_to_memory(), dtype=np.uint8, shape=(vout.height, vout.width, vout.bands)
    )
    out = Image.fromarray(np.ascontiguousarray(arr[:, :, :3]), "RGB")
    assert out.size == (1920, 1920)
    cropped = (1.0 - _kept_fraction(out)) * 100.0
    assert cropped == pytest.approx(43.75, abs=1.5)


if __name__ == "__main__":
    print(f"{'preset':16} {'proporcje':9} {'wyjście':>11} {'ucięte %':>9}")
    for row in crop_table():
        size = f"{row.out_size[0]}×{row.out_size[1]}"
        print(f"{row.preset_id:16} {row.aspect:9} {size:>11} {row.cropped_pct:9.1f}")
