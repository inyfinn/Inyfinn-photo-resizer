"""Wczytywanie obrazów — Pillow, tifffile (CMYK/pro TIFF), jak Photoshop (RGB)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageCms

# TIFF PhotometricInterpretation (libtiff)
_PHOTO_MINISWHITE = 0
_PHOTO_RGB = 2
_PHOTO_PALETTE = 3
_PHOTO_MINISBLACK = 1
_PHOTO_CMYK = 5

# TIFF tags — ICC z Photoshopa trafia w InterColorProfile, nie zawsze w ICCProfile
_TIFF_TAG_ICC_PROFILE = 34675
_TIFF_TAG_INTER_COLOR_PROFILE = 34675

# Jak Photoshop changeMode(RGB) dla profili CMYK→sRGB
_CMYK_TO_SRGB_INTENT = 0  # ImageCms.Intent.PERCEPTUAL


def _normalize_uint8(data):
    import numpy as np

    if data.dtype == np.uint8:
        return data
    if data.dtype == np.uint16:
        return (data / 256).astype(np.uint8)
    if np.issubdtype(data.dtype, np.floating):
        return np.clip(data * 255.0, 0, 255).astype(np.uint8)
    return data.astype(np.uint8)


def _extract_icc_from_tiff_page(page) -> bytes | None:
    """Odczyt profilu ICC z TIFF (InterColorProfile / ICCProfile)."""
    for key in ("InterColorProfile", "ICCProfile", _TIFF_TAG_INTER_COLOR_PROFILE):
        tag = page.tags.get(key)
        if tag is None:
            continue
        try:
            raw = tag.value
            if isinstance(raw, (bytes, bytearray)):
                blob = bytes(raw)
            elif isinstance(raw, memoryview):
                blob = raw.tobytes()
            else:
                blob = bytes(raw)
        except (TypeError, ValueError):
            continue
        if len(blob) >= 128 and blob[36:40] == b"acsp":
            return blob
    return None


def _cmyk_profile_to_srgb(cmyk: Image.Image, icc_bytes: bytes | None) -> Image.Image:
    """CMYK → sRGB z osadzonego ICC (jak Photoshop), fallback do Pillow."""
    if not icc_bytes:
        return cmyk.convert("RGB")
    try:
        src_prof = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
        dst_prof = ImageCms.createProfile("sRGB")
        return ImageCms.profileToProfile(
            cmyk,
            src_prof,
            dst_prof,
            renderingIntent=_CMYK_TO_SRGB_INTENT,
            outputMode="RGB",
        )
    except (ImageCms.PyCMSError, OSError, ValueError):
        return cmyk.convert("RGB")


def _unpremultiply(color, alpha):
    """TIFF ExtraSamples=1 (associated alpha): kolor jest przemnożony przez alfę — cofamy to."""
    import numpy as np

    a = alpha.astype(np.float32)[..., None]
    out = np.where(a > 0, color.astype(np.float32) * 255.0 / np.maximum(a, 1.0), 0.0)
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def _is_associated_alpha(page) -> bool:
    try:
        return int(page.extrasamples[0]) == 1
    except (AttributeError, IndexError, TypeError, ValueError):
        return False


def _trim_transparent(im: Image.Image) -> Image.Image:
    """Przycina przezroczyste marginesy — jak trim(TRANSPARENTPX) w Photoshop."""
    if im.mode not in ("RGBA", "LA"):
        return im
    bbox = im.getbbox()
    if bbox:
        return im.crop(bbox)
    return im


def _cmyk_array_to_rgb(
    data, *, icc_bytes: bytes | None = None, associated: bool = False
) -> Image.Image:
    """CMYK (+ opcjonalny kanał alfa) → RGB/RGBA, jak changeMode(RGB) w Photoshop.

    Przezroczystość zostaje (RGBA) — spłaszczenie robi dopiero zapis do formatu bez alfy.
    """
    import numpy as np

    cmyk = np.ascontiguousarray(data[:, :, :4])
    alpha = data[:, :, 4] if data.shape[2] >= 5 else None
    if alpha is not None and associated:
        cmyk = _unpremultiply(cmyk, alpha)
    im = Image.fromarray(cmyk, mode="CMYK")
    rgb = _cmyk_profile_to_srgb(im, icc_bytes)
    im.close()
    if alpha is None:
        return rgb
    rgba = rgb.convert("RGBA")
    rgb.close()
    rgba.putalpha(Image.fromarray(np.ascontiguousarray(alpha), mode="L"))
    return _trim_transparent(rgba)


def _tifffile_page_to_pil(page) -> Image.Image:
    import numpy as np
    import tifffile

    photo = int(page.photometric)
    data = page.asarray()
    if data is None:
        raise OSError("Pusty TIFF")

    data = _normalize_uint8(data)
    icc_bytes = _extract_icc_from_tiff_page(page)

    if data.ndim == 2:
        if photo == _PHOTO_MINISWHITE:
            data = 255 - data
        return Image.fromarray(data, mode="L").convert("RGB")

    if data.ndim != 3:
        raise OSError(f"Nieobsługiwany TIFF: ndim={data.ndim}")

    ch = data.shape[2]
    associated = _is_associated_alpha(page)

    if photo == _PHOTO_CMYK:
        return _cmyk_array_to_rgb(data, icc_bytes=icc_bytes, associated=associated)

    if ch >= 4:
        rgb, alpha = data[:, :, :3], data[:, :, 3]
        if associated:
            rgb = _unpremultiply(rgb, alpha)
        rgba = np.dstack([rgb, alpha])
        return _trim_transparent(Image.fromarray(np.ascontiguousarray(rgba), mode="RGBA"))
    if ch == 3:
        return Image.fromarray(data, mode="RGB")
    if ch == 2:
        gray, alpha = data[:, :, :1], data[:, :, 1]
        if associated:
            gray = _unpremultiply(gray, alpha)
        la = np.dstack([gray[:, :, 0], alpha])
        return _trim_transparent(Image.fromarray(np.ascontiguousarray(la), mode="LA")).convert("RGBA")
    if ch == 1:
        return Image.fromarray(data[:, :, 0], mode="L").convert("RGB")

    raise OSError(f"Nieobsługiwany TIFF: {ch} kanałów, photometric={photo}")


def _open_tifffile(path: Path) -> Image.Image:
    import tifffile

    with tifffile.TiffFile(str(path)) as tf:
        return _tifffile_page_to_pil(tf.pages[0])


def ensure_export_rgb(im: Image.Image, *, matte: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    """Przygotuj obraz do zapisu PNG/JPEG — jak eksport PS (RGB, tło matte)."""
    if im.mode == "CMYK":
        return im.convert("RGB")
    if im.mode in ("RGBA", "LA"):
        im = _trim_transparent(im)
        bg = Image.new("RGB", im.size, matte)
        if im.mode == "LA":
            im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        return bg
    if im.mode == "P":
        if "transparency" in im.info:
            return ensure_export_rgb(im.convert("RGBA"), matte=matte)
        return im.convert("RGB")
    if im.mode == "L":
        return im.convert("RGB")
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def open_image(path: Path) -> Image.Image:
    """Otwórz obraz; TIFF CMYK przez tifffile (jak PS), reszta przez Pillow."""
    ext = path.suffix.lower()
    last_err: Exception | None = None

    if ext in (".tif", ".tiff"):
        try:
            return _open_tifffile(path)
        except Exception as exc:
            last_err = exc

    try:
        with Image.open(path) as im:
            im.load()
            icc = im.info.get("icc_profile")
            out = im.copy()
        if out.mode == "CMYK":
            rgb = _cmyk_profile_to_srgb(out, icc)
            out.close()
            return rgb
        return out
    except Exception as exc:
        last_err = exc

    if ext in (".tif", ".tiff"):
        try:
            return _open_tifffile(path)
        except Exception as exc:
            last_err = exc

    msg = str(last_err) if last_err else "nieznany błąd"
    if "cannot identify" in msg.lower():
        raise OSError(
            f"Nie rozpoznano pliku jako obrazu ({path.name}). "
            "Spróbuj JPEG/PNG lub dołóż libvips do BIN\\dev\\tools\\libvips."
        ) from last_err
    raise OSError(msg) from last_err
