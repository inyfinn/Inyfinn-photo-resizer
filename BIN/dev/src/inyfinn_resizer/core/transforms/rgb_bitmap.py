"""Flatten source images to a display-only RGB bitmap.

Ported from DAM `dam_thumb_cache.py` (2026-09-10): layers, CMYK, spot/Pantone
and extra channels must not survive into a web encode. Output is a new RGB
canvas — no source ICC, EXIF or layer payload.
"""

from __future__ import annotations

from PIL import Image


def flatten_white(im: Image.Image) -> Image.Image:
    """Composite transparency onto white; force RGB."""
    if im.mode in ("RGBA", "LA"):
        rgba = im.convert("RGBA") if im.mode == "LA" else im
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg
    if im.mode == "P" and "transparency" in im.info:
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg
    if im.mode == "CMYK":
        return im.convert("RGB")
    if im.mode == "YCbCr":
        return im.convert("RGB")
    if im.mode in ("LAB", "HSV"):
        return im.convert("RGB")
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def rgb_bitmap(im: Image.Image) -> Image.Image:
    """Detach a display-only RGB bitmap from layers, profiles and extra channels."""
    flattened = flatten_white(im)
    rgb = Image.new("RGB", flattened.size, (255, 255, 255))
    rgb.paste(flattened)
    return rgb


def vips_rgb_bitmap(image):
    """Same rule for pyvips: sRGB, flatten alpha, drop spot/extra bands."""
    try:
        if image.interpretation in ("cmyk", "cmyk-alpha"):
            image = image.colourspace("srgb")
    except Exception:
        pass
    try:
        if image.hasalpha():
            image = image.flatten(background=[255, 255, 255])
    except Exception:
        pass
    try:
        if image.bands > 3:
            image = image.extract_band(0, n=3)
        elif image.bands == 1:
            image = image.colourspace("srgb")
    except Exception:
        pass
    return image
