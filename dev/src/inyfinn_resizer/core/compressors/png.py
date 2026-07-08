"""PNG compression via pngquant — suwak Quality + paleta kolorów."""

from __future__ import annotations

import colorsys
import shutil
import subprocess
from pathlib import Path

from inyfinn_resizer.core.job import FormatOptions
from inyfinn_resizer.utils.paths import find_tool
from inyfinn_resizer.utils.subprocess_win import run_hidden

PNGQUANT_BANDS = [
    (90, 100), (85, 100), (80, 95), (75, 90), (70, 85),
    (65, 80), (60, 75), (55, 70), (50, 65), (45, 60),
    (40, 55), (35, 50), (30, 45), (25, 40), (20, 35),
    (15, 30), (10, 25), (5, 20), (0, 15),
]

DEFAULT_TARGET_TOLERANCE = 0.2
PNGQUANT_SPEED = 2
MAX_TRIES = 6
PQ_MARKER = ".pq."
MIN_PALETTE_COLORS = 32
MAX_PALETTE_COLORS = 256


def png_max_colors_for_quality(quality_pct: int) -> int:
    """Mapuje suwak jakości (0–100) na liczbę kolorów palety."""
    q = max(5, min(100, int(quality_pct)))
    if q >= 80:
        return MAX_PALETTE_COLORS
    if q >= 50:
        return int(round(192 + (q - 50) * (256 - 192) / (80 - 50)))
    return int(round(32 + (q - 5) * (192 - 32) / (50 - 5)))


def resolve_png_max_colors(opts: FormatOptions) -> int:
    if opts.png_colors_auto:
        return png_max_colors_for_quality(opts.quality)
    return max(MIN_PALETTE_COLORS, min(MAX_PALETTE_COLORS, int(opts.png_max_colors)))


def analyze_accent_palette_boost(path: Path) -> int:
    """
    Wykrywa rzadkie, nasycone akcenty (np. zieleń w potrawie) i podbija paletę.

    Małe plamy koloru giną przy zbyt agresywnej kwantyzacji — dodatkowe sloty
    palety + wolniejszy pngquant je zachowują.
    """
    try:
        from PIL import Image
    except ImportError:
        return 0

    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((480, 480), Image.Resampling.BILINEAR)
        if hasattr(img, "get_flattened_data"):
            pixels = list(img.get_flattened_data())
        else:
            pixels = list(img.getdata())
        if not pixels:
            return 0

        step = max(1, len(pixels) // 10000)
        hue_buckets: set[int] = set()
        saturated_pixels = 0
        samples = 0

        for i in range(0, len(pixels), step):
            r, g, b = pixels[i]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            samples += 1
            if s >= 0.25 and 0.12 <= v <= 0.98:
                saturated_pixels += 1
                hue_buckets.add(int(h * 48))

        if samples == 0:
            return 0

        sat_ratio = saturated_pixels / samples
        distinct_hues = len(hue_buckets)

        boost = 0
        if distinct_hues >= 10 or sat_ratio >= 0.08:
            boost = 48
        elif distinct_hues >= 6 or sat_ratio >= 0.04:
            boost = 32
        elif distinct_hues >= 3 or sat_ratio >= 0.015:
            boost = 16
        return boost
    except OSError:
        return 0


def effective_png_palette(path: Path, base_palette: int) -> int:
    return max(
        MIN_PALETTE_COLORS,
        min(MAX_PALETTE_COLORS, int(base_palette) + analyze_accent_palette_boost(path)),
    )


def speed_for_quality(quality_pct: int, accent_boost: int) -> int:
    q = max(5, min(100, int(quality_pct)))
    if accent_boost >= 16 or q >= 75:
        return 1
    if accent_boost >= 8 or q >= 50:
        return 2
    return 3


def cleanup_pngquant_artifacts_for(path: Path) -> None:
    """Usuwa pliki tymczasowe pngquant powiązane z danym PNG."""
    if not path.parent.is_dir():
        return
    prefix = f"{path.stem}.pq."
    for candidate in path.parent.iterdir():
        if candidate.is_file() and (
            candidate.name.startswith(prefix)
            or PQ_MARKER in candidate.name and candidate.stem.startswith(path.stem)
        ):
            candidate.unlink(missing_ok=True)


def cleanup_pngquant_artifacts_in_folder(folder: Path) -> int:
    """Usuwa wszystkie pozostałości pngquant w folderze."""
    if not folder.is_dir():
        return 0
    removed = 0
    for candidate in folder.iterdir():
        if candidate.is_file() and PQ_MARKER in candidate.name:
            candidate.unlink(missing_ok=True)
            removed += 1
    return removed


def target_bounds(target_kb: float, tolerance: float = DEFAULT_TARGET_TOLERANCE) -> tuple[int, int, int]:
    t = float(target_kb)
    tol = float(tolerance)
    return (
        int(t * (1.0 - tol) * 1024),
        int(t * (1.0 + tol) * 1024),
        int(t * 1024),
    )


def pngquant_params_for_quality(
    quality_pct: int,
    max_colors: int = MAX_PALETTE_COLORS,
    *,
    accent_boost: int = 0,
) -> tuple[int, int, int]:
    """Mapuje suwak UI na parametry pngquant."""
    q = max(5, min(100, int(quality_pct)))
    anchors: list[tuple[int, tuple[int, int, int]]] = [
        (100, (72, 100, speed_for_quality(100, accent_boost))),
        (80, (62, 98, speed_for_quality(80, accent_boost))),
        (50, (48, 78, speed_for_quality(50, accent_boost))),
        (35, (30, 58, speed_for_quality(35, accent_boost))),
        (5, (12, 38, speed_for_quality(5, accent_boost))),
    ]
    for i, (aq, params) in enumerate(anchors):
        if q >= aq:
            if i == 0:
                qmin, qmax, speed = params
                break
            prev_q, prev_params = anchors[i - 1]
            if prev_q == aq:
                qmin, qmax, speed = params
                break
            t = (q - aq) / (prev_q - aq)
            qmin = int(round(params[0] + t * (prev_params[0] - params[0])))
            qmax = int(round(params[1] + t * (prev_params[1] - params[1])))
            speed = prev_params[2] if t >= 0.5 else params[2]
            break
    else:
        qmin, qmax, speed = anchors[-1][1]

    palette_boost = max(0.0, (max_colors - MIN_PALETTE_COLORS) / (MAX_PALETTE_COLORS - MIN_PALETTE_COLORS))
    accent_lift = min(22, accent_boost // 2)
    lift = int(round(palette_boost * 16)) + accent_lift
    qmin = min(95, qmin + lift)
    qmax = min(100, max(qmin + 8, qmax + lift))
    return (max(0, qmin), qmax, speed)


def bands_for_quality(
    quality_pct: int,
    max_colors: int = MAX_PALETTE_COLORS,
    *,
    accent_boost: int = 0,
) -> list[tuple[int, int, int]]:
    primary = pngquant_params_for_quality(quality_pct, max_colors, accent_boost=accent_boost)
    fallbacks: list[tuple[int, int, int]] = []
    qmin, qmax, speed = primary
    for band in PNGQUANT_BANDS:
        candidate = (band[0], band[1], speed)
        if candidate != (qmin, qmax, speed) and abs(band[0] - qmin) <= 12:
            fallbacks.append(candidate)
    seen = {primary}
    ordered = [primary]
    for fb in sorted(fallbacks, key=lambda b: abs(b[0] - qmin)):
        if fb not in seen:
            ordered.append(fb)
            seen.add(fb)
        if len(ordered) >= MAX_TRIES:
            break
    return ordered


def pick_calibrated_candidate(candidates, min_b: int, max_b: int, ideal_b: int):
    if not candidates:
        return None
    in_zone = [c for c in candidates if min_b <= c[1] <= max_b]
    pool = in_zone if in_zone else candidates
    return min(pool, key=lambda c: (abs(c[1] - ideal_b), -c[0][0] if isinstance(c[0], tuple) else -c[0]))


def run_pngquant(
    pngquant: Path,
    src: Path,
    dst: Path,
    qmin: int,
    qmax: int,
    speed: int = PNGQUANT_SPEED,
    max_colors: int = MAX_PALETTE_COLORS,
) -> int | None:
    palette = max(MIN_PALETTE_COLORS, min(MAX_PALETTE_COLORS, int(max_colors)))
    cmd = [
        str(pngquant), "--force", "--floyd",
        "--quality", f"{int(qmin)}-{int(qmax)}",
        "--speed", str(int(speed)),
        str(palette),
        "--output", str(dst), str(src),
    ]
    try:
        result = run_hidden(cmd, timeout=120)
        if result.returncode == 0 and dst.is_file():
            return dst.stat().st_size
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return None


def _apply_target_kb(
    pngquant: Path,
    path: Path,
    target_kb: float,
    quality_pct: int,
    tolerance: float,
    max_colors: int,
) -> tuple[bool, str]:
    min_b, max_b, ideal_b = target_bounds(target_kb, tolerance)
    q_pct = max(10, min(100, int(quality_pct or 50)))
    floor = max(10, q_pct - 25)
    accent_boost = analyze_accent_palette_boost(path)
    palette = effective_png_palette(path, max_colors)
    speed = speed_for_quality(q_pct, accent_boost)
    bands = [b for b in PNGQUANT_BANDS if b[0] >= floor] + [b for b in PNGQUANT_BANDS if b[0] < floor]
    tmp = path.with_suffix(".pq.tmp.png")
    candidates = []
    try:
        for qmin, qmax in bands[:12]:
            if tmp.exists():
                tmp.unlink()
            sz = run_pngquant(pngquant, path, tmp, qmin, qmax, speed, max_colors=palette)
            if sz is not None and sz <= max_b:
                staged = path.with_suffix(f".pq.staging.{qmin}-{qmax}.png")
                shutil.copy2(tmp, staged)
                candidates.append(((qmin, qmax), sz, staged))
            if tmp.exists():
                tmp.unlink()
        pick = pick_calibrated_candidate(candidates, min_b, max_b, ideal_b)
        if pick:
            band, sz, staged = pick
            shutil.move(str(staged), str(path))
            for c in candidates:
                if c[2] != staged and Path(c[2]).exists():
                    Path(c[2]).unlink()
            return True, f"pngquant {band[0]}-{band[1]} {palette}c target {sz // 1024}KB"
        for c in candidates:
            Path(c[2]).unlink(missing_ok=True)
        return False, "pngquant target not reached"
    finally:
        tmp.unlink(missing_ok=True)
        cleanup_pngquant_artifacts_for(path)


def apply_pngquant(
    path: Path,
    *,
    max_kb: float | None = None,
    target_kb: float | None = None,
    target_tolerance: float = DEFAULT_TARGET_TOLERANCE,
    quality_pct: int = 50,
    max_colors: int | None = None,
) -> tuple[bool, str]:
    pngquant = find_tool("pngquant")
    if not pngquant:
        return False, "no_pngquant"

    base_palette = max_colors if max_colors is not None else png_max_colors_for_quality(quality_pct)
    accent_boost = analyze_accent_palette_boost(path)
    palette = effective_png_palette(path, base_palette)

    orig_size = path.stat().st_size
    src_copy = path.with_suffix(".pq.src.png")
    tmp = path.with_suffix(".pq.tmp.png")
    shutil.copy2(path, src_copy)

    try:
        if target_kb is not None:
            ok, msg = _apply_target_kb(
                pngquant, path, target_kb, quality_pct, target_tolerance, palette,
            )
            return ok, msg

        if max_kb is not None:
            max_bytes = int(max_kb * 1024)
            speed = speed_for_quality(quality_pct, accent_boost)
            for qmin, qmax in PNGQUANT_BANDS:
                if tmp.exists():
                    tmp.unlink()
                sz = run_pngquant(pngquant, src_copy, tmp, qmin, qmax, speed, max_colors=palette)
                if sz is not None and sz <= max_bytes:
                    shutil.move(str(tmp), str(path))
                    return True, f"pngquant {qmin}-{qmax} {palette}c max_kb"
            return False, "pngquant max_kb not reached"

        bands = bands_for_quality(quality_pct, palette, accent_boost=accent_boost)
        results: list[tuple[tuple[int, int, int], int, Path]] = []

        for band in bands:
            if tmp.exists():
                tmp.unlink()
            sz = run_pngquant(
                pngquant, src_copy, tmp, band[0], band[1], band[2], max_colors=palette,
            )
            if sz is None:
                continue
            staged = path.with_suffix(f".pq.staging.{band[0]}-{band[1]}.png")
            shutil.copy2(tmp, staged)
            results.append((band, sz, staged))
            tmp.unlink()

        valid = [r for r in results if r[1] < orig_size]
        if not valid:
            for r in results:
                if r[2].exists():
                    r[2].unlink()
            return False, "pngquant no gain"

        primary = pngquant_params_for_quality(quality_pct, palette, accent_boost=accent_boost)
        primary_hit = next((r for r in valid if r[0] == primary), None)
        best = primary_hit if primary_hit else valid[0]

        for r in results:
            if r[2] != best[2] and r[2].exists():
                r[2].unlink()
        shutil.move(str(best[2]), str(path))
        fold = round(orig_size / best[1], 1)
        accent_note = f" +{accent_boost}c" if accent_boost else ""
        return True, (
            f"pngquant {best[0][0]}-{best[0][1]} {palette}c{accent_note} s{best[0][2]} "
            f"{best[1] // 1024}KB ({fold}× mniej)"
        )
    finally:
        src_copy.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)
        cleanup_pngquant_artifacts_for(path)
