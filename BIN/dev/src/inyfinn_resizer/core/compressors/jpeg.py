"""JPEG compression — binary search quality + target KB."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from inyfinn_resizer.core.compressors.png import pick_calibrated_candidate, target_bounds


def encode_jpg_bytes(im: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=int(quality), optimize=True, progressive=True)
    return buf.getvalue()


def to_rgb(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        src = im.convert("RGBA") if im.mode == "P" else im
        if "A" in src.getbands():
            bg.paste(src, mask=src.split()[-1])
        else:
            bg.paste(src)
        return bg
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def compress_jpeg_file(
    path: Path,
    *,
    quality: int = 85,
    max_kb: float | None = None,
    target_kb: float | None = None,
    target_tolerance: float = 0.2,
) -> tuple[bool, str]:
    im = Image.open(path)
    im.load()
    im = to_rgb(im)

    cap = min(100, int(quality))

    if target_kb:
        min_b, max_b, ideal_b = target_bounds(target_kb, target_tolerance)
        candidates = []
        for q in range(10, cap + 1):
            data = encode_jpg_bytes(im, q)
            if len(data) <= max_b:
                candidates.append((q, len(data), data))
            else:
                break
        pick = pick_calibrated_candidate(candidates, min_b, max_b, ideal_b)
        if pick:
            best_q, _, best_data = pick
            path.write_bytes(best_data)
            return True, f"jpg q={best_q} target"
        path.write_bytes(encode_jpg_bytes(im, 10))
        return True, "jpg fallback q=10"

    max_bytes = int(max_kb * 1024) if max_kb else None
    lo, hi = 10, cap
    best_data = encode_jpg_bytes(im, lo)
    best_q = lo

    while lo <= hi:
        q = (lo + hi) // 2
        data = encode_jpg_bytes(im, q)
        if max_bytes is None or len(data) <= max_bytes:
            best_data = data
            best_q = q
            lo = q + 1
        else:
            hi = q - 1

    path.write_bytes(best_data)
    return True, f"jpg q={best_q}"
