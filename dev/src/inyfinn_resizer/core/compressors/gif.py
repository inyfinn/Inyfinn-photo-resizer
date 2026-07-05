"""GIF compression via gifsicle — ported from GIF-COMPRESOR gif_core.py."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from inyfinn_resizer.utils.paths import find_tool

FREEZE_MS = 750
ULTRA_LOSSY = 70


def run_gifsicle(gifsicle: Path, args: list[str]) -> None:
    r = subprocess.run([str(gifsicle)] + args, capture_output=True, text=True, check=False)
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
            timed, save_all=True, append_images=frames[1:],
            duration=delays, loop=0, optimize=False,
        )

        opt = ["-O3", "--no-dither", "--loopcount=0"]
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
    quality: int = 85,
) -> tuple[bool, str]:
    gifsicle = find_tool("gifsicle")
    if not gifsicle:
        if src != dst:
            import shutil
            shutil.copy2(src, dst)
        return False, "no_gifsicle (copied)"

    n, durs, _ = read_gif_info(src)
    keep_pct = max(0.15, quality / 100.0)

    if mode == "ultra":
        indices = list(range(min(4, n)))
        colors = 64
        lossy = ULTRA_LOSSY
    elif mode == "frames":
        indices = pick_indices(n, keep_pct)
        colors = 256
        lossy = 0
    else:
        indices = pick_indices(n, max(0.5, keep_pct))
        colors = max(32, int(256 * keep_pct))
        lossy = max(0, int((100 - quality) * 0.8))

    encode_gif(gifsicle, src, dst, indices, durs, colors=colors, lossy=lossy)
    return True, f"gifsicle mode={mode} colors={colors} lossy={lossy}"
