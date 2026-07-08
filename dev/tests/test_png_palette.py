"""Test mapowania jakości → paleta kolorów PNG."""

from __future__ import annotations

from inyfinn_resizer.core.compressors.png import png_max_colors_for_quality, resolve_png_max_colors
from inyfinn_resizer.core.job import FormatOptions


def test_palette_anchors() -> None:
    assert png_max_colors_for_quality(100) == 256
    assert png_max_colors_for_quality(80) == 256
    assert png_max_colors_for_quality(50) == 192
    assert png_max_colors_for_quality(5) == 32
    assert png_max_colors_for_quality(0) == 32


def test_palette_midpoints() -> None:
    assert png_max_colors_for_quality(65) == 224
    assert png_max_colors_for_quality(27) == 110


def test_resolve_auto_and_manual() -> None:
    auto = FormatOptions(quality=50, png_colors_auto=True)
    assert resolve_png_max_colors(auto) == 192

    manual = FormatOptions(quality=50, png_colors_auto=False, png_max_colors=128)
    assert resolve_png_max_colors(manual) == 128


if __name__ == "__main__":
    test_palette_anchors()
    test_palette_midpoints()
    test_resolve_auto_and_manual()
    print("OK: test_png_palette")
