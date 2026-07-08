"""PNG compression via pngquant — suwak Quality + paleta kolorów."""

from __future__ import annotations

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
PNGQUANT_SPEED = 4
MAX_TRIES = 6
PQ_MARKER = ".pq."
MIN_PALETTE_COLORS = 32
MAX_PALETTE_COLORS = 256


def png_max_colors_for_quality(quality_pct: int) -> int:
    """
    Mapuje suwak jakości (0–100) na liczbę kolorów palety.

    - >= 80%: 256 kolorów
    - 50%: 192 kolorów
    - 5%: 32 kolory (minimum)
    - Poniżej 5%: nadal 32
    """
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

PNGQUANT_BANDS = [
    (90, 100), (85, 100), (80, 95), (75, 90), (70, 85),
    (65, 80), (60, 75), (55, 70), (50, 65), (45, 60),
    (40, 55), (35, 50), (30, 45), (25, 40), (20, 35),
    (15, 30), (10, 25), (5, 20), (0, 15),
]

DEFAULT_TARGET_TOLERANCE = 0.2
PNGQUANT_SPEED = 4
MAX_TRIES = 6
PQ_MARKER = ".pq."


def cleanup_pngquant_artifacts_for(path: Path) -> None:
    """Usuwa pliki tymczasowe pngquant powiązane z danym PNG."""
    if not path.parent.is_dir():
        return
    prefix = f"{path.stem}.pq."
    for candidate in path.parent.iterdir():
        if candidate.is_file() and (
            candidate.name.startswith(prefix) or PQ_MARKER in candidate.name and candidate.stem.startswith(path.stem)
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


def pngquant_params_for_quality(quality_pct: int, max_colors: int = MAX_PALETTE_COLORS) -> tuple[int, int, int]:
    """
    Mapuje suwak UI na parametry pngquant — łagodniejsze pasma przy większej palecie.

    q=50 + 192 kolory → ok. 40–70 (zachowanie detali).
    """
    q = max(5, min(100, int(quality_pct)))
    anchors: list[tuple[int, tuple[int, int, int]]] = [
        (100, (75, 100, PNGQUANT_SPEED)),
        (80, (65, 95, PNGQUANT_SPEED)),
        (50, (40, 70, PNGQUANT_SPEED)),
        (35, (22, 52, 2)),
        (5, (8, 32, 1)),
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
    lift = int(round(palette_boost * 18))
    qmin = min(95, qmin + lift)
    qmax = min(100, max(qmin + 5, qmax + lift))
    return (max(0, qmin), qmax, speed)


def bands_for_quality(quality_pct: int, max_colors: int = MAX_PALETTE_COLORS) -> list[tuple[int, int, int]]:
    """Główne + zapasowe pasma do wypróbowania (qmin, qmax, speed)."""
    primary = pngquant_params_for_quality(quality_pct, max_colors)
    fallbacks: list[tuple[int, int, int]] = []
    qmin, qmax, speed = primary
    for band in PNGQUANT_BANDS:
        if (band[0], band[1], speed) != (qmin, qmax, speed):
            if abs(band[0] - qmin) <= 15:
                fallbacks.append((band[0], band[1], speed))
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
        str(pngquant), "--force",
        "--quality", f"{int(qmin)}-{int(qmax)}",
        "--speed", str(int(speed)),
        str(palette),
        "--output", str(dst), str(src),
    ]
    try:
        result = run_hidden(cmd, timeout=90)
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
    bands = [b for b in PNGQUANT_BANDS if b[0] >= floor] + [b for b in PNGQUANT_BANDS if b[0] < floor]
    tmp = path.with_suffix(".pq.tmp.png")
    candidates = []
    try:
        for qmin, qmax in bands[:12]:
            if tmp.exists():
                tmp.unlink()
            sz = run_pngquant(pngquant, path, tmp, qmin, qmax, max_colors=max_colors)
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
            return True, f"pngquant {band[0]}-{band[1]} {max_colors}c target {sz // 1024}KB"
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

    palette = max_colors if max_colors is not None else png_max_colors_for_quality(quality_pct)
    palette = max(MIN_PALETTE_COLORS, min(MAX_PALETTE_COLORS, int(palette)))

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
            for qmin, qmax in PNGQUANT_BANDS:
                if tmp.exists():
                    tmp.unlink()
                sz = run_pngquant(pngquant, src_copy, tmp, qmin, qmax, max_colors=palette)
                if sz is not None and sz <= max_bytes:
                    shutil.move(str(tmp), str(path))
                    return True, f"pngquant {qmin}-{qmax} {palette}c max_kb"
            return False, "pngquant max_kb not reached"

        bands = bands_for_quality(quality_pct, palette)
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

        primary = pngquant_params_for_quality(quality_pct, palette)
        primary_hit = next((r for r in valid if r[0] == primary), None)
        best = primary_hit if primary_hit else valid[0]

        for r in results:
            if r[2] != best[2] and r[2].exists():
                r[2].unlink()
        shutil.move(str(best[2]), str(path))
        fold = round(orig_size / best[1], 1)
        return True, (
            f"pngquant {best[0][0]}-{best[0][1]} {palette}c s{best[0][2]} "
            f"{best[1] // 1024}KB ({fold}× mniej)"
        )
    finally:
        src_copy.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)
        cleanup_pngquant_artifacts_for(path)
