"""Mapowanie suwaka jakości (0–100) na parametry kompresji formatów."""

from __future__ import annotations

from inyfinn_resizer.core.compressors.png import png_max_colors_for_quality


def palette_colors_for_quality(quality: int) -> int:
    """Liczba kolorów PNG/GIF z suwaka jakości."""
    return png_max_colors_for_quality(quality)


def gif_lossy_for_quality(quality: int) -> int:
    """Lossy gifsicle 0–200 z suwaka jakości."""
    return max(0, min(200, int((100 - quality) * 2)))


def apply_quality_to_format_opts(opts) -> None:
    """Synchronizuje pola zależne od suwaka jakości (PNG + GIF)."""
    q = int(opts.quality)
    colors = palette_colors_for_quality(q)
    if getattr(opts, "png_colors_auto", True):
        opts.png_max_colors = colors
    if getattr(opts, "gif_from_quality", True):
        opts.gif_lossy = gif_lossy_for_quality(q)
        opts.gif_max_colors = colors
