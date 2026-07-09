"""Test mapowania jakości → paleta kolorów PNG."""

from __future__ import annotations

from inyfinn_resizer.core.compressors.png import (
    accents_preserved,
    analyze_accent_palette_boost,
    apply_pngquant,
    count_rare_green_accents,
    effective_png_palette,
    png_max_colors_for_quality,
    resolve_png_max_colors,
)
from inyfinn_resizer.core.job import FormatOptions


def test_palette_anchors() -> None:
    assert png_max_colors_for_quality(100) == 256
    assert png_max_colors_for_quality(80) == 218
    assert png_max_colors_for_quality(50) == 160
    assert png_max_colors_for_quality(10) == 24
    assert png_max_colors_for_quality(5) == 24
    assert png_max_colors_for_quality(0) == 24


def test_palette_midpoints() -> None:
    assert png_max_colors_for_quality(65) == 189
    assert png_max_colors_for_quality(27) == 82


def test_resolve_auto_and_manual() -> None:
    auto = FormatOptions(quality=50, png_colors_auto=True)
    assert resolve_png_max_colors(auto) == 160

    manual = FormatOptions(quality=50, png_colors_auto=False, png_max_colors=128)
    assert resolve_png_max_colors(manual) == 128


def test_accent_palette_boost_detects_green(tmp_path) -> None:
    from PIL import Image

    img_path = tmp_path / "accent.png"
    pixels = [(140, 60, 40)] * 8000 + [(30, 160, 45)] * 400
    img = Image.new("RGB", (100, 84))
    img.putdata(pixels[: 100 * 84])
    img.save(img_path, format="PNG")

    boost = analyze_accent_palette_boost(img_path)
    assert boost >= 8
    assert effective_png_palette(img_path, 192) >= 200


def test_accent_guard_skips_lossy_quantization(tmp_path, monkeypatch) -> None:
    import shutil

    from PIL import Image

    src = tmp_path / "greens.png"
    pixels = []
    for i in range(100 * 50):
        if i % 250 == 0:
            pixels.append((35, 170, 50))
        else:
            pixels.append((150, 55, 35))
    img = Image.new("RGB", (100, 50))
    img.putdata(pixels)
    img.save(src, format="PNG")

    assert count_rare_green_accents(src) >= 10

    def fake_pngquant(_pngquant, src_path, dst, *_args, **_kwargs):
        flat = [(150, 55, 35)] * (100 * 50)
        Image.new("RGB", (100, 50)).putdata(flat)
        Image.new("RGB", (100, 50), (150, 55, 35)).save(dst, format="PNG")
        return dst.stat().st_size

    monkeypatch.setattr(
        "inyfinn_resizer.core.compressors.png.run_pngquant",
        fake_pngquant,
    )
    monkeypatch.setattr(
        "inyfinn_resizer.core.compressors.png.find_tool",
        lambda _: tmp_path / "pngquant.exe",
    )

    work = tmp_path / "work.png"
    shutil.copy2(src, work)
    ok, msg = apply_pngquant(work, quality_pct=85, max_colors=256)
    assert not ok
    assert "accent preserved" in msg
    assert accents_preserved(src, work)


def test_run_pngquant_cmd_uses_ncolors_before_separator(tmp_path, monkeypatch) -> None:
    from inyfinn_resizer.core.compressors.png import run_pngquant

    captured: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr("inyfinn_resizer.core.compressors.png.run_hidden", fake_run)
    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    src.write_bytes(b"x")
    dst.write_bytes(b"ok")

    run_pngquant(tmp_path / "pngquant.exe", src, dst, 50, 80, speed=2, max_colors=192)

    assert captured
    cmd = captured[0]
    out_idx = cmd.index("--output")
    assert cmd[out_idx - 1] == "192"
    assert cmd[out_idx + 1] == str(dst)
    sep = cmd.index("--")
    assert cmd[sep + 1] == str(src)
    assert "--floyd" not in cmd
    assert "--nofs" not in cmd


def test_png_auto_target_kb() -> None:
    from inyfinn_resizer.core.compressors.png import png_auto_target_kb

    target = png_auto_target_kb(1374 * 1024, 50)
    assert 340 <= target <= 350


def test_scale_accent_boost_at_half_quality() -> None:
    from inyfinn_resizer.core.compressors.png import scale_accent_boost

    assert scale_accent_boost(48, 50) == 24
    assert scale_accent_boost(48, 100) == 48


def test_run_pngquant_nofs_only_for_accent_preservation(tmp_path, monkeypatch) -> None:
    from inyfinn_resizer.core.compressors.png import run_pngquant

    captured: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr("inyfinn_resizer.core.compressors.png.run_hidden", fake_run)
    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    src.write_bytes(b"x")
    dst.write_bytes(b"ok")
    pq = tmp_path / "pngquant.exe"

    run_pngquant(pq, src, dst, 50, 80, preserve_accents=True)
    assert captured
    assert "--nofs" in captured[0]
    assert "--floyd" not in captured[0]


if __name__ == "__main__":
    test_palette_anchors()
    test_palette_midpoints()
    test_resolve_auto_and_manual()
    print("OK: test_png_palette")
