"""JPEG compression — binary search quality + target KB."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from inyfinn_resizer.core.compressors.png import pick_calibrated_candidate, target_bounds


# Od tej jakości kolor idzie w pełnej rozdzielczości (4:4:4). Przy 4:2:0 barwa jest wspólna
# dla bloku 2×2 — czerwone krawędzie i drobny tekst bledną (pomiar 2026-09-18: nasycenie
# krawędzi 0,817 PNG → 0,782 przy 4:2:0, 0,809 przy 4:4:4; plik ~+60%).
FULL_CHROMA_MIN_QUALITY = 70


def full_chroma(quality: int, mode: str = "auto") -> bool:
    """True = 4:4:4. mode: auto (wg jakości) | full | reduced; stare profile miały 'medium'."""
    if mode == "full":
        return True
    if mode == "reduced":
        return False
    return int(quality) >= FULL_CHROMA_MIN_QUALITY


def pil_subsampling(quality: int, mode: str = "auto") -> int:
    """Wartość `subsampling` dla Pillow: 0 = 4:4:4, 2 = 4:2:0."""
    return 0 if full_chroma(quality, mode) else 2


def encode_jpg_bytes(im: Image.Image, quality: int, *, subsampling_mode: str = "auto") -> bytes:
    buf = io.BytesIO()
    im.save(
        buf,
        format="JPEG",
        quality=int(quality),
        optimize=True,
        progressive=True,
        subsampling=pil_subsampling(quality, subsampling_mode),
    )
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
    subsampling_mode: str = "auto",
) -> tuple[bool, str]:
    """Ponowne kodowanie JPEG (wizki: celowa rekompresja; konwersja: tylko przy limicie wagi)."""
    im = Image.open(path)
    im.load()
    im = to_rgb(im)

    cap = min(100, int(quality))

    def encode(q: int) -> bytes:
        return encode_jpg_bytes(im, q, subsampling_mode=subsampling_mode)

    if target_kb:
        min_b, max_b, ideal_b = target_bounds(target_kb, target_tolerance)
        candidates = []
        for q in range(10, cap + 1):
            data = encode(q)
            if len(data) <= max_b:
                candidates.append((q, len(data), data))
            else:
                break
        pick = pick_calibrated_candidate(candidates, min_b, max_b, ideal_b)
        if pick:
            best_q, _, best_data = pick
            path.write_bytes(best_data)
            return True, f"jpg q={best_q} target"
        path.write_bytes(encode(10))
        return True, "jpg fallback q=10"

    max_bytes = int(max_kb * 1024) if max_kb else None
    lo, hi = 10, cap
    best_data = encode(lo)
    best_q = lo

    while lo <= hi:
        q = (lo + hi) // 2
        data = encode(q)
        if max_bytes is None or len(data) <= max_bytes:
            best_data = data
            best_q = q
            lo = q + 1
        else:
            hi = q - 1

    path.write_bytes(best_data)
    return True, f"jpg q={best_q}"
