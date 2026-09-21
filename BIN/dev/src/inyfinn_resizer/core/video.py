"""Wideo → GIF (ffmpeg + logika zamrożeń z KOMPRESJA GIFÓW).

W filmie każda klatka trwa tyle samo, więc „najdłuższa klatka” nie istnieje wprost.
Najpierw scalamy sąsiednie klatki, które niczym się nie różnią (`merge_static_runs`) —
dopiero wtedy powstają bloki zamrożenia i działa `ultra_plan` z core/compressors/gif.py.
Długość animacji zawsze zostaje taka jak w filmie.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from inyfinn_resizer.utils.paths import find_tool, tool_env_path

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mpg", ".mpeg", ".mts", ".wmv",
}

# Klatka „taka sama jak poprzednia”: mniej niż 0,2% pikseli zmieniło się zauważalnie.
# Średnia różnica całego kadru nie wystarcza — mały ruchomy obiekt na dużym tle jej nie rusza.
STATIC_PIXEL_DELTA = 12      # o tyle musi zmienić się jasność piksela, żeby to był ruch
STATIC_PIXEL_RATIO = 0.002   # ułamek pikseli w ruchu, poniżej którego klatka to zastygnięcie
COMPARE_SIZE = 128           # rozdzielczość porównania (szybkie, a widzi drobny ruch)
MIN_FRAME_MS = 20  # GIF liczy czas w setnych sekundy — poniżej 2 cs przeglądarki zwalniają
MAX_SAMPLE_FPS = 60.0


def is_video_file(path) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration_sec: float
    fps: float


def ffmpeg_exe() -> Path | None:
    return find_tool("ffmpeg")


def _run_ffmpeg(args: list[str], *, capture_stdout: bool = False) -> subprocess.CompletedProcess:
    exe = ffmpeg_exe()
    if exe is None:
        raise OSError("Brak ffmpeg — wideo wymaga narzędzia ffmpeg w paczce (tools/ffmpeg).")
    import os

    env = dict(os.environ)
    env["PATH"] = tool_env_path(exe)
    creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    return subprocess.run(
        [str(exe), "-hide_banner", *args],
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        env=env,
        timeout=1800,
        creationflags=creationflags,
    )


def probe(path: Path) -> VideoInfo:
    """Wymiary, długość i liczba klatek na sekundę — z komunikatu ffmpeg."""
    proc = _run_ffmpeg(["-i", str(path)])
    text = proc.stderr.decode("utf-8", "replace")

    size = re.search(r",\s(\d{2,5})x(\d{2,5})[\s,]", text)
    if not size:
        raise OSError(f"To nie jest plik wideo albo format jest nieobsługiwany: {path.name}")
    width, height = int(size.group(1)), int(size.group(2))

    duration = 0.0
    dur = re.search(r"Duration:\s(\d+):(\d+):(\d+\.?\d*)", text)
    if dur:
        duration = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))

    fps = 0.0
    rate = re.search(r"(\d+(?:\.\d+)?)\s(?:fps|tbr)", text)
    if rate:
        fps = float(rate.group(1))
    return VideoInfo(width=width, height=height, duration_sec=duration, fps=fps or 25.0)


def output_size(info: VideoInfo, max_width: int) -> tuple[int, int]:
    """Szerokość ograniczona do max_width, proporcje zachowane, wymiary parzyste (wymóg ffmpeg)."""
    width = min(int(max_width), info.width) if max_width else info.width
    width = max(2, width - (width % 2))
    height = max(2, round(info.height * width / info.width))
    height -= height % 2
    return width, height


def extract_frames(path: Path, *, fps: float, max_width: int):
    """Klatki jako obrazy Pillow, informacje o filmie i czas jednej próbki w ms."""
    from PIL import Image

    info = probe(path)
    width, height = output_size(info, max_width)
    sample_fps = max(1.0, min(float(fps), MAX_SAMPLE_FPS))
    proc = _run_ffmpeg(
        [
            "-v", "error",
            "-i", str(path),
            "-vf", f"fps={sample_fps},scale={width}:{height}:flags=lanczos",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        capture_stdout=True,
    )
    if proc.returncode != 0:
        raise OSError(proc.stderr.decode("utf-8", "replace").strip() or "ffmpeg nie odczytał wideo")

    stride = width * height * 3
    raw = proc.stdout
    frames = [
        Image.frombytes("RGB", (width, height), raw[i : i + stride])
        for i in range(0, len(raw) - stride + 1, stride)
    ]
    if not frames:
        raise OSError("Wideo nie zawiera klatek do odczytu")
    return frames, info, int(round(1000.0 / sample_fps))


def merge_static_runs(frames: list, frame_ms: int, pixel_ratio: float = STATIC_PIXEL_RATIO):
    """Scala sąsiednie, nieróżniące się klatki w jedną o zsumowanym czasie (bloki zamrożenia)."""
    import numpy as np

    kept: list = []
    durations: list[int] = []
    previous = None
    for frame in frames:
        small = np.asarray(
            frame.resize((COMPARE_SIZE, COMPARE_SIZE)).convert("L"), dtype=np.int16
        )
        if previous is not None:
            moving = float((np.abs(small - previous) > STATIC_PIXEL_DELTA).mean())
            if moving < pixel_ratio:
                durations[-1] += frame_ms
                continue
        kept.append(frame)
        durations.append(frame_ms)
        previous = small
    return kept, durations


def ultra_plan_video(durations: list[int], max_frames: int):
    """Zostaw pierwszą klatkę i te trzymane najdłużej; czasy sumują się do długości filmu.

    Film „3 s ruchu + 2 s zastygnięcia” przy 2 klatkach daje: kadr początkowy na 3 s
    i kadr zastygnięcia na 2 s. Wersja z GIF-ów (`ultra_plan`) zakłada zamrożenia w środku
    animacji i przy zamrożeniu na końcu zostawiała jedną klatkę.
    """
    from inyfinn_resizer.core.compressors.gif import compute_delays

    total = len(durations)
    limit = max(1, min(int(max_frames), total))
    keep = {0}
    for index in sorted(range(total), key=lambda i: (-durations[i], i)):
        if len(keep) >= limit:
            break
        keep.add(index)
    indices = sorted(keep)
    return indices, compute_delays(durations, indices)


def plan_frames(durations: list[int], max_frames: int, mode: str):
    """Które klatki zostają i na jak długo. Suma czasów zawsze = długość filmu."""
    from inyfinn_resizer.core.compressors.gif import compute_delays, pick_indices

    total = len(durations)
    if mode == "ultra":
        return ultra_plan_video(durations, max_frames)
    if max_frames and total > int(max_frames):
        indices = pick_indices(total, int(max_frames) / total)
        return indices, compute_delays(durations, indices)
    return list(range(total)), list(durations)


def save_gif(frames: list, delays: list[int], out_path: Path) -> None:
    """Zapis animacji GIF z własnym czasem każdej klatki.

    Animowany WebP z Pillow nie zapisuje czasów klatek (sprawdzone 2026-09-21: plik ma klatki,
    ale zerowe opóźnienia), więc film zapisujemy wyłącznie jako GIF.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    safe = [max(MIN_FRAME_MS, int(d)) for d in delays]
    frames[0].save(
        out_path, format="GIF", save_all=True, append_images=frames[1:],
        duration=safe, loop=0, disposal=2, optimize=False,
    )


def optimize_gif(path: Path, *, colors: int, lossy: int, dither: bool) -> str:
    """gifsicle na gotowym GIF-ie — bez zmiany klatek i czasów."""
    from inyfinn_resizer.core.compressors.gif import run_gifsicle

    gifsicle = find_tool("gifsicle")
    if not gifsicle:
        return "bez gifsicle"
    args = ["-O3", "--loopcount=0"]
    if not dither:
        args.append("--no-dither")
    if colors < 256:
        args += ["--colors", str(int(colors)), "--color-method", "blend-diversity"]
    if lossy > 0:
        args.append(f"--lossy={int(lossy)}")
    tmp = path.with_suffix(".gifsicle.tmp.gif")
    try:
        run_gifsicle(gifsicle, args + [str(path), "-o", str(tmp)])
        if tmp.is_file() and tmp.stat().st_size > 0:
            tmp.replace(path)
            return f"gifsicle {colors} kolorów, lossy={lossy}"
    except Exception:  # narzędzie zewnętrzne jest opcjonalne
        tmp.unlink(missing_ok=True)
    return "bez optymalizacji"


def convert_video(src: Path, dst: Path, opts) -> str:
    """Wideo → GIF. Zwraca krótki opis tego, co powstało."""
    frames, info, frame_ms = extract_frames(
        src, fps=opts.video_fps, max_width=opts.video_max_width
    )
    merged, durations = merge_static_runs(frames, frame_ms)
    indices, delays = plan_frames(durations, opts.video_max_frames, opts.video_mode)
    chosen = [merged[i] for i in indices]

    save_gif(chosen, delays, dst)
    detail = (
        f"{info.duration_sec:.1f}s → {len(chosen)} klatek "
        f"(próbki: {len(frames)}, po scaleniu zamrożeń: {len(merged)})"
    )
    from inyfinn_resizer.core.quality_map import gif_lossy_for_quality, palette_colors_for_quality

    colors = opts.gif_max_colors
    lossy = opts.gif_lossy
    if opts.gif_from_quality:
        colors = palette_colors_for_quality(opts.quality)
        lossy = gif_lossy_for_quality(opts.quality)
    detail += " · " + optimize_gif(dst, colors=colors, lossy=lossy, dither=opts.gif_dither)
    return detail
