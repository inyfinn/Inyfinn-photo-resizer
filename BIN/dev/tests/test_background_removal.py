"""Usuwanie tła — pipeline + zachowanie flag przy presecie Oryginalny."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from inyfinn_resizer.core.job import FormatOptions, JobSpec, ResizeOptions, TransformOptions
from inyfinn_resizer.core.pipeline import process_job
from inyfinn_resizer.core.size_presets import PRESET_ORIGINAL, apply_size_preset
from inyfinn_resizer.core.transforms.background_removal import alpha_matting_available, model_is_ready

FIXTURE = Path(__file__).parent / "fixtures" / "IMG_0113.jpg"
OUTPUT = Path(__file__).parent / "output"


def _alpha_transparent_ratio(path: Path) -> float:
    with Image.open(path) as im:
        assert im.mode in ("RGBA", "LA"), f"Expected alpha, got {im.mode}"
        alpha = np.array(im.split()[-1])
    return float((alpha < 10).sum()) / alpha.size


@pytest.fixture
def fixture_path():
    assert FIXTURE.is_file(), f"Missing test fixture: {FIXTURE}"
    return FIXTURE


@pytest.fixture(scope="module")
def require_rmbg_model():
    assert model_is_ready("birefnet-general-lite"), (
        "Brak modelu lite — uruchom BIN\\dev\\scripts\\setup_rmbg_models.ps1"
    )


def test_original_preset_does_not_clear_remove_background_flag():
    """Regresja: preset Oryginalny nie może kasować remove_background z UI."""
    ui_transforms = TransformOptions(remove_background=True, bg_model="birefnet-general-lite")
    _, preset_transforms = apply_size_preset(PRESET_ORIGINAL)
    assert preset_transforms.remove_background is False

    preserved = replace(
        preset_transforms,
        remove_background=ui_transforms.remove_background,
        bg_model=ui_transforms.bg_model,
        bg_alpha_matting=True,
        bg_post_process_mask=True,
    )
    assert preserved.remove_background is True
    assert preserved.bg_model == "birefnet-general-lite"


def test_alpha_matting_available_in_dev_env():
    assert alpha_matting_available() is True


def test_remove_background_works_without_alpha_matting_metadata(monkeypatch, fixture_path, require_rmbg_model):
    """Regresja EXE: brak metadanych pymatting nie może wywalić konwersji."""
    import inyfinn_resizer.core.transforms.background_removal as bg

    bg._ALPHA_MATTING_READY = None
    monkeypatch.setattr(bg, "alpha_matting_available", lambda: False)

    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / "IMG_0113_bg_no_matting_meta.png"
    job = JobSpec(
        input_path=fixture_path,
        output_path=out,
        output_format="png",
        format_opts=FormatOptions(quality=50, png_mode="png8"),
        transforms=TransformOptions(
            remove_background=True,
            bg_model="birefnet-general-lite",
            bg_alpha_matting=True,
            bg_post_process_mask=True,
        ),
    )
    result = process_job(job, overwrite=True)
    assert result.status.value == "OK", result.message
    assert _alpha_transparent_ratio(out) > 0.10


def test_remove_background_retries_after_unicode_decode_error(monkeypatch, fixture_path, require_rmbg_model):
    """Regresja: błąd utf-8 z DirectML nie może zabić trybu Szybko."""
    import rembg

    calls = {"n": 0}
    real_remove = rembg.remove

    def flaky_remove(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise UnicodeDecodeError("utf-8", b"\xc0", 0, 1, "invalid start byte")
        return real_remove(*args, **kwargs)

    monkeypatch.setattr(rembg, "remove", flaky_remove)

    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / "IMG_0113_bg_unicode_retry.png"
    job = JobSpec(
        input_path=fixture_path,
        output_path=out,
        output_format="png",
        transforms=TransformOptions(
            remove_background=True,
            bg_model="birefnet-general-lite",
            bg_alpha_matting=False,
        ),
    )
    result = process_job(job, overwrite=True)
    assert result.status.value == "OK", result.message
    assert calls["n"] >= 2


def test_png_with_background_removal_has_transparent_pixels(fixture_path, require_rmbg_model):
    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / "IMG_0113_bg_lite.png"
    job = JobSpec(
        input_path=fixture_path,
        output_path=out,
        output_format="png",
        format_opts=FormatOptions(quality=50, png_mode="png8"),
        resize=ResizeOptions(scale_percent=22.0, min_longest_enabled=True, min_longest_px=1080),
        transforms=TransformOptions(
            remove_background=True,
            bg_model="birefnet-general-lite",
            bg_alpha_matting=True,
            bg_post_process_mask=True,
        ),
    )
    result = process_job(job, overwrite=True)
    assert result.status.value == "OK", result.message
    assert out.is_file()

    ratio = _alpha_transparent_ratio(out)
    assert ratio > 0.15, f"Za mało przezroczystych pikseli: {ratio:.1%}"
