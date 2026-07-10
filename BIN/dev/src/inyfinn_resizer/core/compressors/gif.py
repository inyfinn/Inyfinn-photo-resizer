"""GIF compression via gifsicle — port z KOMPRESJA GIFÓW (quality / frames / ultra)."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from inyfinn_resizer.utils.paths import find_tool
from inyfinn_resizer.utils.subprocess_win import run_hidden

FREEZE_MS = 750
ULTRA_LOSSY = 70


@dataclass(frozen=True)
class QualityPreset:
    level: int
    name: str
    colors: int
    lossy: int


QUALITY_PRESETS: dict[int, QualityPreset] = {
    10: QualityPreset(10, "max — bez kompresji obrazu", 256, 0),
    9: QualityPreset(9, "bardzo wysoka", 256, 20),
    8: QualityPreset(8, "wysoka", 256, 40),
    7: QualityPreset(7, "dobra plus", 256, 60),
    6: QualityPreset(6, "dobra (zalecana)", 256, 80),
    5: QualityPreset(5, "średnia wysoka", 192, 80),
    4: QualityPreset(4, "średnia", 128, 90),
    3: QualityPreset(3, "średnia niska", 96, 110),
    2: QualityPreset(2, "niska", 64, 140),
    1: QualityPreset(1, "min — max kompresja", 48, 200),
}


@dataclass(frozen=True)
class FramePreset:
    level: int
    name: str
    keep_pct: float


FRAME_PRESETS: dict[int, FramePreset] = {
    10: FramePreset(10, "90% klatek — prawie bez zmian", 0.90),
    9: FramePreset(9, "80% klatek — minimalna redukcja", 0.80),
    8: FramePreset(8, "70% klatek — lekka redukcja", 0.70),
    7: FramePreset(7, "62% klatek — umiarkowana", 0.62),
    6: FramePreset(6, "55% klatek — 2 z 3 (domyślne)", 0.55),
    5: FramePreset(5, "48% klatek — co 2. klatka", 0.48),
    4: FramePreset(4, "40% klatek — mocna redukcja", 0.40),
    3: FramePreset(3, "33% klatek — co 3. klatka", 0.33),
    2: FramePreset(2, "25% klatek — co 4. klatka", 0.25),
    1: FramePreset(1, "15% klatek — max redukcja", 0.15),
}


def run_gifsicle(gifsicle: Path, args: list[str]) -> None:
    r = run_hidden([str(gifsicle)] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())


def read_gif_info(path: Path) -> tuple[int, list[int], tuple[int, int]]:
    with Image.open(path) as img:
        w, h = img.size
        n = img.n_frames
        durs = []
        for i in range(n):
            img.seek(i)
            durs.append(int(img.info.get("duration", 80) or 80))
    return n, durs, (w, h)


def indices_2of3(n: int) -> list[int]:
    out: list[int] = []
    i = 0
    while i < n:
        out.append(i)
        if i + 1 < n:
            out.append(i + 1)
        i += 3
    return out


def pick_indices(n: int, keep_pct: float) -> list[int]:
    target = max(2, round(n * keep_pct))
    if target >= n:
        return list(range(n))
    step = n / target
    return sorted({0, *[round(i * step) for i in range(1, target - 1)], n - 1})


def compute_delays(durs: list[int], indices: list[int]) -> list[int]:
    n = len(durs)
    return [
        sum(durs[idx : (indices[k + 1] if k + 1 < len(indices) else n)])
        for k, idx in enumerate(indices)
    ]


def freeze_threshold(durs: list[int], threshold_ms: int = FREEZE_MS) -> int:
    med = sorted(durs)[len(durs) // 2]
    return max(threshold_ms, med * 4, 400)


def freeze_blocks_chrono(durs: list[int]) -> list[tuple[int, int, int]]:
    n = len(durs)
    thr = freeze_threshold(durs)
    blocks: list[tuple[int, int, int]] = []
    i = 0
    while i < n:
        if durs[i] >= thr:
            start = i
            total = 0
            while i < n and durs[i] >= thr:
                total += durs[i]
                i += 1
            blocks.append((start, i - 1, total))
        else:
            i += 1
    return blocks


def ultra_plan(n: int, durs: list[int], max_frames: int = 4) -> tuple[list[int], list[int]]:
    if n <= max_frames:
        return list(range(n)), durs[:]

    total = sum(durs)
    last = n - 1
    blocks_chrono = freeze_blocks_chrono(durs)
    blocks_by_len = sorted(blocks_chrono, key=lambda b: -b[2])
    block_at = {b[0]: b for b in blocks_chrono}

    first_freeze_end = blocks_chrono[0][1] if blocks_chrono else n // 2
    pre_and_first_freeze = sum(durs[0 : first_freeze_end + 1])

    chosen: set[int] = {last}
    for start, _end, _dur in blocks_by_len:
        if len(chosen) >= max_frames:
            break
        if start != last:
            chosen.add(start)

    indices = sorted(chosen)
    delays: list[int] = []
    for k, idx in enumerate(indices):
        if idx == last:
            delays.append(max(total - sum(delays), durs[last]))
        elif k == 0:
            delays.append(pre_and_first_freeze)
        elif idx in block_at:
            delays.append(block_at[idx][2])
        else:
            delays.append(durs[idx])

    diff = total - sum(delays)
    if diff:
        delays[-1] += diff

    return indices, delays


def encode_gif(
    gifsicle: Path,
    src: Path,
    dst: Path,
    indices: list[int],
    durs: list[int],
    *,
    delays: list[int] | None = None,
    colors: int = 256,
    lossy: int = 0,
    dither: bool = True,
    optimize_only: bool = False,
) -> None:
    delays = delays if delays is not None else compute_delays(durs, indices)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        unopt = tmp / "unopt.gif"
        stepped = tmp / "stepped.gif"
        timed = tmp / "timed.gif"

        run_gifsicle(gifsicle, ["--unoptimize", str(src), "-o", str(unopt)])
        run_gifsicle(gifsicle, [str(unopt)] + [f"#{i}" for i in indices] + ["-o", str(stepped)])

        frames = []
        with Image.open(stepped) as img:
            for i in range(img.n_frames):
                img.seek(i)
                frames.append(img.copy())
        frames[0].save(
            timed,
            save_all=True,
            append_images=frames[1:],
            duration=delays,
            loop=0,
            optimize=False,
        )

        opt = ["-O3", "--loopcount=0"]
        if not dither:
            opt.append("--no-dither")
        if not optimize_only:
            if colors < 256:
                opt += ["--colors", str(colors), "--color-method", "blend-diversity"]
            if lossy > 0:
                opt.append(f"--lossy={lossy}")
        run_gifsicle(gifsicle, opt + [str(timed), "-o", str(dst)])


def compress_gif(
    src: Path,
    dst: Path,
    *,
    mode: str = "quality",
    level: int = 6,
    quality: int = 85,
    dither: bool = True,
    lossy: int = 0,
    colors: int | None = None,
    ultra_max_frames: int = 4,
    ultra_lossy: int = ULTRA_LOSSY,
) -> tuple[bool, str]:
    gifsicle = find_tool("gifsicle")
    if not gifsicle:
        if src != dst:
            import shutil

            shutil.copy2(src, dst)
        return False, "no_gifsicle (copied)"

    level = max(1, min(10, level))
    n, durs, _ = read_gif_info(src)

    if mode == "ultra":
        indices, delays = ultra_plan(n, durs, max_frames=ultra_max_frames)
        use_colors = 256
        use_lossy = ultra_lossy
        tag = f"ultra frames={len(indices)} lossy={use_lossy}"
    elif mode == "frames":
        preset = FRAME_PRESETS[level]
        indices = pick_indices(n, preset.keep_pct)
        delays = None
        use_colors = 256
        use_lossy = 0
        tag = f"frames L{level} ({preset.name})"
    else:
        if colors is not None and lossy > 0:
            preset_colors = colors
            preset_lossy = lossy
            indices = indices_2of3(n)
            delays = None
            tag = f"quality custom colors={preset_colors} lossy={preset_lossy}"
        else:
            preset = QUALITY_PRESETS[level]
            preset_colors = preset.colors
            preset_lossy = preset.lossy
            indices = indices_2of3(n)
            delays = None
            tag = f"quality L{level} ({preset.name})"
        use_colors = preset_colors
        use_lossy = preset_lossy

    encode_gif(
        gifsicle,
        src,
        dst,
        indices,
        durs,
        delays=delays,
        colors=use_colors,
        lossy=use_lossy,
        dither=dither,
    )
    return True, f"gifsicle {tag} dither={dither}"
