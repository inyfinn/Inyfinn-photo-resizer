"""Regresja: animacje GIF/WebP zachowują klatki, JPEG2000 jest naprawdę JPEG2000."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from inyfinn_resizer.core.job import FormatOptions, JobSpec, ResizeMode, ResizeOptions
from inyfinn_resizer.core.pipeline import process_job

FRAMES = 9
SIZE = (320, 240)


def _make_frames() -> list[Image.Image]:
    frames = []
    for i in range(FRAMES):
        frame = Image.new("RGB", SIZE, (20, 20, 60))
        ImageDraw.Draw(frame).ellipse((10 + i * 30, 80, 70 + i * 30, 140), fill=(250, 200, 30))
        frames.append(frame)
    return frames


@pytest.fixture
def anim_gif(tmp_path: Path) -> Path:
    path = tmp_path / "anim.gif"
    frames = _make_frames()
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=80, loop=0)
    return path


@pytest.fixture
def anim_webp(tmp_path: Path) -> Path:
    path = tmp_path / "anim.webp"
    frames = _make_frames()
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=80, loop=0)
    return path


def _convert(src: Path, out: Path, fmt: str, resize: ResizeOptions | None = None) -> Path:
    job = JobSpec(
        input_path=src,
        output_path=out,
        output_format=fmt,
        resize=resize or ResizeOptions(),
        format_opts=FormatOptions(quality=50),
    )
    result = process_job(job)
    assert result.status.value == "OK", result.message
    return out


def _info(path: Path) -> tuple[int, tuple[int, int]]:
    with Image.open(path) as im:
        return int(getattr(im, "n_frames", 1)), im.size


def test_gif_to_webp_keeps_all_frames(anim_gif: Path, tmp_path: Path) -> None:
    frames, size = _info(_convert(anim_gif, tmp_path / "o.webp", "webp"))
    assert frames == FRAMES
    assert size == SIZE


def test_animated_webp_to_gif_stays_animated(anim_webp: Path, tmp_path: Path) -> None:
    frames, _ = _info(_convert(anim_webp, tmp_path / "o.gif", "gif"))
    assert frames > 1


def test_animated_webp_roundtrip_keeps_all_frames(anim_webp: Path, tmp_path: Path) -> None:
    frames, _ = _info(_convert(anim_webp, tmp_path / "o.webp", "webp"))
    assert frames == FRAMES


def test_gif_scale_slider_resizes_and_stays_animated(anim_gif: Path, tmp_path: Path) -> None:
    """Suwak Skali przy trybie „bez zmian” kopiował GIF 1:1 — wymiar się nie zmieniał."""
    frames, size = _info(
        _convert(anim_gif, tmp_path / "o.gif", "gif", ResizeOptions(scale_percent=50.0))
    )
    assert size == (SIZE[0] // 2, SIZE[1] // 2)
    assert frames > 1


def test_gif_max_dimension_stays_animated(anim_gif: Path, tmp_path: Path) -> None:
    frames, size = _info(
        _convert(
            anim_gif,
            tmp_path / "o.gif",
            "gif",
            ResizeOptions(mode=ResizeMode.MAX_DIMENSION, dimension=160),
        )
    )
    assert max(size) == 160
    assert frames > 1


def test_jp2_output_is_real_jpeg2000(tmp_path: Path) -> None:
    src = tmp_path / "src.png"
    Image.new("RGB", (200, 150), (180, 90, 40)).save(src)
    out = _convert(src, tmp_path / "o.jp2", "jp2")
    head = out.read_bytes()[:12]
    assert head != b"" and head[:3] != b"\xff\xd8\xff", "plik .jp2 jest zwykłym JPEG-iem"
    assert head == b"\x00\x00\x00\x0cjP  \r\n\x87\n" or head[:4] == b"\xff\x4f\xff\x51"
