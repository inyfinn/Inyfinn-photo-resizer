"""RGB-only AVIF — flatten CMYK/Pantone/layers. No default size cap."""

from __future__ import annotations

from PIL import Image

from inyfinn_resizer.core.compressors.avif import avif_max_bytes, quality_ladder
from inyfinn_resizer.core.job import FormatOptions, job_from_dict
from inyfinn_resizer.core.transforms.rgb_bitmap import rgb_bitmap


def test_rgb_bitmap_drops_cmyk_and_alpha() -> None:
    cmyk = Image.new("CMYK", (16, 16), (0, 80, 80, 0))
    out = rgb_bitmap(cmyk)
    assert out.mode == "RGB"
    rgba = Image.new("RGBA", (16, 16), (10, 20, 30, 0))
    flat = rgb_bitmap(rgba)
    assert flat.mode == "RGB"
    assert flat.getpixel((0, 0)) == (255, 255, 255)


def test_format_options_avif_has_no_default_size_cap() -> None:
    opts = FormatOptions()
    assert opts.rgb_bitmap_only is True
    assert opts.avif_max_kb is None
    assert avif_max_bytes(opts.avif_max_kb) is None


def test_job_dict_keeps_rgb_bitmap_flag() -> None:
    spec = job_from_dict(
        {
            "input_path": "in.jpg",
            "output_path": "out.avif",
            "output_format": "avif",
            "format_opts": {"quality": 30, "rgb_bitmap_only": True},
        }
    )
    assert spec.format_opts.rgb_bitmap_only is True
    assert spec.format_opts.avif_max_kb is None


def test_quality_ladder_starts_at_requested() -> None:
    steps = quality_ladder(30)
    assert steps[0] == 30
    assert 5 in steps
