"""Tło pod JPEG — spłaszczenie przezroczystości."""

from __future__ import annotations

from typing import TYPE_CHECKING

from inyfinn_resizer.core.job import FormatOptions

if TYPE_CHECKING:
    import pyvips


def _hex_to_rgb(hex_color: str) -> list[int]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return [255, 255, 255]
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


def _linear_gradient_background(width: int, height: int, c1: list[int], c2: list[int]) -> "pyvips.Image":
    import pyvips

    row = pyvips.Image.new_from_array([c1, c2], scale=1)
    return row.resize(width, vscale=height, kernel="linear")


def _radial_gradient_background(width: int, height: int, c1: list[int], c2: list[int]) -> "pyvips.Image":
    import numpy as np
    import pyvips

    y, x = np.ogrid[:height, :width]
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_r = dist.max() or 1.0
    t = dist / max_r
    arr = np.zeros((height, width, 3), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = c1[i] * (1.0 - t) + c2[i] * t
    return pyvips.Image.new_from_array(arr)


def _maybe_noise(bg: "pyvips.Image", enabled: bool) -> "pyvips.Image":
    if not enabled:
        return bg
    try:
        noise = bg.gaussnoise(sigma=1.2)
        return bg.linear(0.92, 0).composite(noise.linear(0.08, 0), "over")
    except Exception:
        return bg


def apply_jpeg_matte(image: "pyvips.Image", opts: FormatOptions) -> "pyvips.Image":
    """Nakłada tło pod półprzezroczyste piksele przed zapisem JPG."""
    if not image.hasalpha():
        return image

    mode = opts.jpeg_matte_mode
    if mode == "gradient":
        c1 = _hex_to_rgb(opts.jpeg_matte_color)
        c2 = _hex_to_rgb(opts.jpeg_matte_color2)
        if opts.jpeg_gradient_reverse:
            c1, c2 = c2, c1
        if opts.jpeg_gradient_type == "radial":
            bg = _radial_gradient_background(image.width, image.height, c1, c2)
        else:
            bg = _linear_gradient_background(image.width, image.height, c1, c2)
        bg = _maybe_noise(bg, opts.jpeg_matte_noise)
        return bg.composite(image, "over")

    if mode == "black":
        bg = [0, 0, 0]
    elif mode == "custom":
        bg = _hex_to_rgb(opts.jpeg_matte_color)
    else:
        bg = [255, 255, 255]
    flat = image.flatten(background=bg)
    return _maybe_noise(flat, opts.jpeg_matte_noise)
