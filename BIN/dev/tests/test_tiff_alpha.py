"""TIFF z przezroczystością (CMYK+alfa z Photoshopa, RGB+alfa) ma zostać przezroczysty, nie na czarnym tle."""

from pathlib import Path

import numpy as np
import tifffile

from inyfinn_resizer.core.image_loader import open_image


def _sample(channels: int) -> np.ndarray:
    data = np.zeros((40, 60, channels), dtype=np.uint8)
    data[10:30, 20:40, :-1] = 200  # nieprzezroczysty środek
    data[10:30, 20:40, -1] = 255
    data[10:30, 19, :-1] = 100     # krawędź 50% — kolor przemnożony przez alfę (ASSOCALPHA)
    data[10:30, 19, -1] = 128
    data[15, 25] = 0              # dziura — przezroczysty piksel w środku
    return data


def test_cmyk_tiff_with_alpha_stays_transparent(tmp_path: Path) -> None:
    p = tmp_path / "cmyk.tif"
    tifffile.imwrite(p, _sample(5), photometric="separated", extrasamples=[1])
    im = open_image(p)
    assert im.mode == "RGBA"
    assert im.size == (21, 20)  # przezroczyste marginesy przycięte
    assert im.getpixel((6, 5))[3] == 0
    # krawędź po cofnięciu przemnożenia ma ten sam kolor co środek, nie ciemniejszy
    edge, inner = im.getpixel((0, 5)), im.getpixel((5, 5))
    assert edge[3] == 128 and abs(edge[0] - inner[0]) <= 2


def test_rgb_tiff_with_alpha_is_not_treated_as_cmyk(tmp_path: Path) -> None:
    p = tmp_path / "rgba.tif"
    tifffile.imwrite(p, _sample(4), photometric="rgb", extrasamples=[2])
    im = open_image(p)
    assert im.mode == "RGBA"
    assert im.getpixel((1, 5)) == (200, 200, 200, 255)
