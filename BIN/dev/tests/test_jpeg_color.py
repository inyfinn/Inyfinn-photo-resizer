"""JPEG: pełna dokładność koloru (4:4:4) od jakości 70, jeden zapis bez ponownego kodowania."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, JpegImagePlugin

from inyfinn_resizer.core.compressors.jpeg import full_chroma
from inyfinn_resizer.core.job import FormatOptions, JobSpec
from inyfinn_resizer.core.pipeline import process_job


def _red_text_png(path: Path) -> None:
    im = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 599, 299), fill=(255, 255, 255, 255))
    for i in range(0, 600, 6):
        d.line((i, 20, i, 280), fill=(219, 13, 27, 255), width=1)  # cienkie czerwone kreski
    im.save(path)


def _convert(src: Path, out: Path, quality: int, mode: str = "auto") -> Path:
    res = process_job(
        JobSpec(input_path=src, output_path=out, output_format="jpeg",
                format_opts=FormatOptions(quality=quality, subsampling=mode))
    )
    assert res.status.value == "OK", res.message
    return out


def _sampling(path: Path) -> int:
    with Image.open(path) as im:
        assert im.format == "JPEG"
        return JpegImagePlugin.get_sampling(im)


def test_full_chroma_rules() -> None:
    assert full_chroma(80) and full_chroma(70)
    assert not full_chroma(69)
    assert full_chroma(20, "full")
    assert not full_chroma(95, "reduced")
    assert full_chroma(80, "medium")  # stare profile = auto


def test_default_quality_keeps_full_color(tmp_path: Path) -> None:
    src = tmp_path / "red.png"
    _red_text_png(src)
    out = _convert(src, tmp_path / "q80.jpg", 80)
    assert _sampling(out) == 0  # 4:4:4
    assert Image.open(out).size == (600, 300)  # wymiary bez zmian


def test_low_quality_and_reduced_mode_use_420(tmp_path: Path) -> None:
    src = tmp_path / "red.png"
    _red_text_png(src)
    assert _sampling(_convert(src, tmp_path / "q50.jpg", 50)) == 2
    assert _sampling(_convert(src, tmp_path / "red80.jpg", 80, "reduced")) == 2


def test_thin_red_lines_keep_saturation(tmp_path: Path) -> None:
    src = tmp_path / "red.png"
    _red_text_png(src)
    full = np.asarray(Image.open(_convert(src, tmp_path / "f.jpg", 80)).convert("RGB")).astype(float)
    red = np.asarray(Image.open(_convert(src, tmp_path / "r.jpg", 80, "reduced")).convert("RGB")).astype(float)
    ref = np.asarray(Image.open(src).convert("RGB")).astype(float)
    mask = (ref[..., 0] > 150) & (ref[..., 1] < 60)
    err_full = np.abs(full[mask] - ref[mask]).mean()
    err_red = np.abs(red[mask] - ref[mask]).mean()
    assert err_full < err_red * 0.7, (err_full, err_red)
