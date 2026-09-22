"""Wideo → GIF: zamrożenia, liczba klatek i zachowana długość animacji."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from inyfinn_resizer.core.formats.registry import is_image_file, is_video_file, output_format_for_input
from inyfinn_resizer.core.job import FormatOptions, JobSpec
from inyfinn_resizer.core.pipeline import process_job
from inyfinn_resizer.core.video import (
    ffmpeg_exe,
    merge_static_runs,
    output_size,
    probe,
    sampling_fps,
    ultra_plan_video,
)

MOTION_FRAMES = 90   # 3 s przy 30 fps
FREEZE_FRAMES = 60   # 2 s zastygnięcia
SIZE = (320, 180)


@pytest.fixture(scope="module")
def sample_video(tmp_path_factory) -> Path:
    if ffmpeg_exe() is None:
        pytest.skip("brak ffmpeg w tools/ffmpeg — uruchom scripts/setup_tools.ps1")
    work = tmp_path_factory.mktemp("wideo")
    frames = work / "frames"
    frames.mkdir()
    for i in range(MOTION_FRAMES):
        im = Image.new("RGB", SIZE, (18, 20, 34))
        ImageDraw.Draw(im).ellipse((20 + i * 3, 60, 70 + i * 3, 110), fill=(232, 62, 74))
        im.save(frames / f"{i:04d}.png")
    last = Image.new("RGB", SIZE, (18, 20, 34))
    ImageDraw.Draw(last).ellipse((260, 60, 310, 110), fill=(232, 62, 74))
    for i in range(MOTION_FRAMES, MOTION_FRAMES + FREEZE_FRAMES):
        last.save(frames / f"{i:04d}.png")
    out = work / "klip.mov"
    subprocess.run(
        [str(ffmpeg_exe()), "-y", "-v", "error", "-framerate", "30",
         "-i", str(frames / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)],
        check=True,
    )
    return out


def _gif_frames(path: Path) -> tuple[int, int]:
    """Liczba klatek i łączny czas animacji w ms."""
    total = 0
    with Image.open(path) as im:
        assert im.format == "GIF"
        count = im.n_frames
        for i in range(count):
            im.seek(i)
            total += int(im.info.get("duration", 0))
    return count, total


def _convert(src: Path, out: Path, **opts) -> str:
    res = process_job(JobSpec(
        input_path=src, output_path=out, output_format="gif",
        format_opts=FormatOptions(quality=80, **{"video_fps": 12, **opts}),
    ))
    assert res.status.value == "OK", res.message
    return res.message


def test_video_files_are_accepted_and_map_to_gif() -> None:
    assert is_video_file("klip.MOV") and is_image_file("klip.MOV")
    assert output_format_for_input("klip.webm") == "gif"
    assert not is_video_file("zdjecie.png")


def test_probe_reads_length_and_size(sample_video: Path) -> None:
    info = probe(sample_video)
    assert info.width == SIZE[0] and info.height == SIZE[1]
    assert 4.8 <= info.duration_sec <= 5.2


def test_merge_static_runs_finds_freeze() -> None:
    moving = []
    for i in range(10):
        im = Image.new("RGB", (120, 90), (10, 10, 10))
        ImageDraw.Draw(im).rectangle((i * 10, 20, i * 10 + 20, 60), fill=(240, 60, 60))
        moving.append(im)
    frozen = [moving[-1].copy() for _ in range(20)]
    kept, durations = merge_static_runs(moving + frozen, 100)
    assert len(kept) == 10, "klatki z ruchem nie mogą się scalić"
    assert durations[-1] == 100 * 21, "zastygnięcie = jedna klatka o zsumowanym czasie"
    assert sum(durations) == 100 * 30, "łączny czas bez zmian"


def test_ultra_plan_keeps_first_and_longest() -> None:
    durations = [100] * 10 + [3000]  # ruch, potem zastygnięcie
    indices, delays = ultra_plan_video(durations, 2)
    assert indices == [0, 10]
    assert delays == [1000, 3000]
    assert sum(delays) == sum(durations)


def test_ultra_video_two_frames_keeps_length(sample_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "ultra.gif"
    _convert(sample_video, out, video_mode="ultra", video_ultra_frames=2)
    count, total = _gif_frames(out)
    assert count == 2, "kadr z ruchu + kadr zastygnięcia"
    assert 4700 <= total <= 5100, f"długość animacji ma zostać ~5 s, jest {total} ms"


def test_smooth_mode_respects_frame_limit(sample_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "smooth.gif"
    _convert(sample_video, out, video_mode="smooth", video_max_frames=8)
    count, total = _gif_frames(out)
    assert count == 8
    assert 4700 <= total <= 5100


def test_ultra_is_much_smaller_than_smooth(sample_video: Path, tmp_path: Path) -> None:
    smooth = tmp_path / "s.gif"
    ultra = tmp_path / "u.gif"
    _convert(sample_video, smooth, video_mode="smooth", video_max_frames=24)
    _convert(sample_video, ultra, video_mode="ultra", video_ultra_frames=2)
    assert ultra.stat().st_size < smooth.stat().st_size / 2


def test_other_format_for_video_is_refused(sample_video: Path, tmp_path: Path) -> None:
    res = process_job(JobSpec(
        input_path=sample_video, output_path=tmp_path / "x.png", output_format="png",
    ))
    assert res.status.value == "ERROR"
    assert "GIF" in res.message


def test_size_comes_from_source_and_only_shrinks() -> None:
    from inyfinn_resizer.core.video import VideoInfo

    info = VideoInfo(width=1000, height=500, duration_sec=3.0, fps=25.0)
    assert output_size(info, 100) == (1000, 500), "100% = wymiary filmu"
    assert output_size(info, 50) == (500, 250)
    assert output_size(info, 1) == (10, 4), "1% z 1000 px to 10 px; wysokosc parzysta"
    assert output_size(info, 400) == (1000, 500), "program nie powieksza filmu"


def test_scale_percent_reaches_the_gif(sample_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "male.gif"
    _convert(sample_video, out, video_mode="smooth", video_scale_percent=25)
    with Image.open(out) as im:
        assert im.size == (80, 44), f"25% z 320x180 to 80x44, jest {im.size}"


def test_fps_sets_the_pace_in_smooth_mode(sample_video: Path, tmp_path: Path) -> None:
    """Klatki na sekunde maja realnie sterowac tempem, a nie tylko probkowaniem."""
    rzadko = tmp_path / "rzadko.gif"
    gesto = tmp_path / "gesto.gif"
    _convert(sample_video, rzadko, video_mode="smooth", video_fps=5, video_scale_percent=50)
    _convert(sample_video, gesto, video_mode="smooth", video_fps=20, video_scale_percent=50)
    with Image.open(rzadko) as a, Image.open(gesto) as b:
        assert b.n_frames > a.n_frames, "wiecej klatek na sekunde = wiecej klatek w GIF-ie"


def test_ultra_samples_finer_than_the_gif_pace() -> None:
    assert sampling_fps(5, "smooth") == 5, "rownomiernie: probkujemy dokladnie w tempie GIF-a"
    assert sampling_fps(5, "ultra") >= 12, "ULTRA musi widziec film gesciej, inaczej gubi zatrzymania"
    assert sampling_fps(30, "ultra") <= 30
