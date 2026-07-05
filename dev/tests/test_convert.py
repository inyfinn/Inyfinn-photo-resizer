"""Conversion tests — quality 75 / 50 / 35."""

from __future__ import annotations

from pathlib import Path

import pytest

from inyfinn_resizer.core.job import FormatOptions, JobSpec
from inyfinn_resizer.core.pipeline import process_job
from inyfinn_resizer.utils.paths import find_tool

FIXTURE = Path(__file__).parent / "fixtures" / "IMG_0113.jpg"
OUTPUT = Path(__file__).parent / "output"

QUALITIES = [75, 50, 35]


@pytest.fixture
def fixture_path():
    assert FIXTURE.is_file(), f"Missing test fixture: {FIXTURE}"
    return FIXTURE


@pytest.fixture(scope="module", autouse=True)
def require_pngquant():
    pq = find_tool("pngquant")
    assert pq is not None, "pngquant required at tools/pngquant/pngquant.exe"


def _run(fixture_path: Path, fmt: str, quality: int) -> tuple:
    OUTPUT.mkdir(exist_ok=True)
    ext = {"jpeg": "jpg", "png": "png", "webp": "webp"}[fmt]
    out = OUTPUT / f"IMG_0113_{fmt}_q{quality}.{ext}"
    job = JobSpec(
        input_path=fixture_path,
        output_path=out,
        output_format=fmt,
        format_opts=FormatOptions(quality=quality),
    )
    result = process_job(job, overwrite=True)
    return result, out


@pytest.mark.parametrize("quality", QUALITIES)
def test_jpeg_recompress_smaller_than_source(fixture_path, quality):
    result, out = _run(fixture_path, "jpeg", quality)
    assert result.status.value == "OK", result.message
    assert out.is_file()
    assert result.new_bytes < result.old_bytes


@pytest.mark.parametrize("quality", QUALITIES)
def test_png_pngquant_real_compression(fixture_path, quality):
    """PNG po pngquant musi być wyraźnie mniejszy od źródłowego JPEG."""
    result, out = _run(fixture_path, "png", quality)
    assert result.status.value == "OK", result.message
    assert out.is_file()
    assert result.new_bytes < result.old_bytes, (
        f"PNG q={quality}: {result.new_kb:.0f} KB nie mniejszy od JPEG {result.old_kb:.0f} KB"
    )
    # q=50: oczekujemy co najmniej ~3× mniej niż JPEG (~1.2 MB → ~400 KB lub mniej)
    min_ratio = {75: 0.50, 50: 0.35, 35: 0.30}[quality]
    assert result.new_bytes <= result.old_bytes * min_ratio, (
        f"PNG q={quality}: za słaba kompresja — {result.new_kb:.0f} KB "
        f"(oczekiwano <= {result.old_kb * min_ratio:.0f} KB)"
    )


@pytest.mark.parametrize("quality", QUALITIES)
def test_webp_smaller_than_source(fixture_path, quality):
    result, out = _run(fixture_path, "webp", quality)
    assert result.status.value == "OK", result.message
    assert out.is_file()
    assert result.new_bytes < result.old_bytes


def test_lower_quality_means_smaller_jpeg(fixture_path):
    sizes = [(_run(fixture_path, "jpeg", q)[0].new_bytes, q) for q in QUALITIES]
    sizes.sort(key=lambda x: x[1], reverse=True)
    assert sizes[0][0] > sizes[1][0] > sizes[2][0], f"JPEG: {sizes}"


def test_lower_quality_means_smaller_png(fixture_path):
    sizes = [(_run(fixture_path, "png", q)[0].new_bytes, q) for q in QUALITIES]
    sizes.sort(key=lambda x: x[1], reverse=True)
    assert sizes[0][0] > sizes[1][0] > sizes[2][0], f"PNG: {sizes}"


def test_png_q50_strong_compression(fixture_path):
    """Przy q=50 plik PNG powinien być drastycznie mniejszy (jak pngquant ~5× na PNG)."""
    result, _ = _run(fixture_path, "png", 50)
    assert result.new_kb < result.old_kb * 0.4, (
        f"PNG q=50: {result.new_kb:.0f} KB — oczekiwano wyraźnej kompresji (JPEG {result.old_kb:.0f} KB)"
    )
