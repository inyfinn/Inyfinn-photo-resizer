"""AVIF encode: RGB bitmap only (no CMYK, spot/Pantone, layers).

Optional size ladder runs only when avif_max_kb is set. Resizer has no default cap.
"""

from __future__ import annotations

import os
from pathlib import Path

from inyfinn_resizer.core.compressors.external import compress_avif_avifenc
from inyfinn_resizer.core.job import DEFAULT_AVIF_QUALITY
from inyfinn_resizer.core.transforms.rgb_bitmap import rgb_bitmap
AVIF_QUALITY_STEPS = (30, 24, 18, 12, 8, 5)
AVIF_SIDE_STEPS = (960, 720, 560, 480, 400, 320, 256, 192, 160)


def avif_max_bytes(max_kb: float | None) -> int | None:
    if max_kb is None:
        return None
    kb = float(max_kb)
    if kb <= 0:
        return None
    return int(kb * 1024)


def quality_ladder(start_quality: int) -> tuple[int, ...]:
    q = max(0, min(100, int(start_quality)))
    steps = [q]
    for item in AVIF_QUALITY_STEPS:
        if item not in steps and item <= q:
            steps.append(item)
    if 5 not in steps:
        steps.append(5)
    return tuple(steps)


def save_avif_capped(
    rgb,
    dest_avif: Path,
    *,
    max_bytes: int | None,
    quality: int = DEFAULT_AVIF_QUALITY,
    lossless: bool = False,
) -> bool:
    """Save metadata-free RGB AVIF, reducing quality/size until the cap is met."""
    from PIL import Image

    dest_avif.parent.mkdir(parents=True, exist_ok=True)
    base = rgb_bitmap(rgb)
    if lossless or max_bytes is None:
        return _save_one(base, dest_avif, quality=quality, lossless=lossless)

    side_steps = (max(base.size),) + AVIF_SIDE_STEPS
    seen: set[tuple[int, int]] = set()
    smallest: Path | None = None
    smallest_size = 0
    for max_side in side_steps:
        candidate = base.copy()
        if max(candidate.size) > max_side:
            candidate.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        if candidate.size in seen:
            continue
        seen.add(candidate.size)
        for q in quality_ladder(quality):
            tmp = dest_avif.with_suffix(f".{q}.{candidate.size[0]}.tmp")
            try:
                if not _save_one(candidate, tmp, quality=q, lossless=False):
                    continue
                size = tmp.stat().st_size
                if size <= max_bytes:
                    os.replace(tmp, dest_avif)
                    return True
                if smallest is None or size < smallest_size:
                    if smallest and smallest.exists():
                        smallest.unlink(missing_ok=True)
                    smallest = tmp
                    smallest_size = size
                    tmp = None  # keep
            finally:
                if tmp is not None:
                    tmp.unlink(missing_ok=True)
    if smallest and smallest.exists():
        os.replace(smallest, dest_avif)
        return True
    return dest_avif.exists()


def _save_one(rgb, dest: Path, *, quality: int, lossless: bool) -> bool:
    from PIL import Image

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        rgb.save(dest, format="AVIF", quality=max(0, min(100, quality)))
        return dest.is_file() and dest.stat().st_size > 0
    except Exception:
        pass
    png = dest.with_suffix(".rgb.tmp.png")
    try:
        rgb.save(png, format="PNG")
        ok, _ = compress_avif_avifenc(png, dest, quality, lossless)
        return bool(ok and dest.is_file() and dest.stat().st_size > 0)
    finally:
        png.unlink(missing_ok=True)


def save_vips_avif_capped(image, dest: Path, *, max_bytes: int | None, quality: int, lossless: bool) -> bool:
    """pyvips heifsave with the same RGB-only + size ladder."""
    from inyfinn_resizer.core.transforms.rgb_bitmap import vips_rgb_bitmap

    dest.parent.mkdir(parents=True, exist_ok=True)
    image = vips_rgb_bitmap(image)
    if lossless or max_bytes is None:
        image.heifsave(str(dest), Q=max(0, min(100, quality)), lossless=lossless, strip=True)
        return dest.is_file() and dest.stat().st_size > 0

    q_steps = quality_ladder(quality)
    longest = max(int(image.width), int(image.height))
    side_steps = (longest,) + AVIF_SIDE_STEPS
    seen: set[tuple[int, int]] = set()
    last_ok: Path | None = None
    for max_side in side_steps:
        candidate = image
        if longest > max_side:
            try:
                candidate = image.thumbnail_image(int(max_side))
            except Exception:
                continue
        size = (int(candidate.width), int(candidate.height))
        if size in seen:
            continue
        seen.add(size)
        for q in q_steps:
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            try:
                candidate.heifsave(str(tmp), Q=q, lossless=False, strip=True)
            except Exception:
                tmp.unlink(missing_ok=True)
                continue
            if not tmp.is_file() or tmp.stat().st_size == 0:
                tmp.unlink(missing_ok=True)
                continue
            last_ok = tmp
            if tmp.stat().st_size <= max_bytes:
                os.replace(tmp, dest)
                return True
            tmp.unlink(missing_ok=True)
    if last_ok and last_ok.exists():
        os.replace(last_ok, dest)
        return True
    return dest.exists()
