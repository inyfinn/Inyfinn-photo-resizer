"""Eksport wg specyfikacji sieci: kadr do treści, limity wymiarów i wagi pliku (np. Rossmann 2026)."""

from __future__ import annotations

import io
import math
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

# Piksele z alfą poniżej progu (ok. 3%) są niewidoczne na jasnym tle, ale w trybie ciemnym
# sklepu tworzą mgiełkę i poszerzają kadr. Zerujemy je przed przycięciem.
ALPHA_FLOOR = 8


def has_real_alpha(im: Image.Image) -> bool:
    """Czy obraz ma już przezroczyste tło (wtedy nie uruchamiamy usuwania tła)."""
    if im.mode not in ("RGBA", "LA", "PA") and not (im.mode == "P" and "transparency" in im.info):
        return False
    alpha = im.convert("RGBA").getchannel("A")
    return alpha.getextrema()[0] < 255


def needs_background_removal(path: Path) -> bool:
    """Szybko, z nagłówka: plik bez kanału przezroczystości (np. JPG) potrzebuje usuwania tła."""
    try:
        with Image.open(path) as im:
            return im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info
    except OSError:
        return False


def trim_to_content(im: Image.Image, floor: int = ALPHA_FLOOR) -> Image.Image:
    """Zeruje alfę < floor i przycina do prostokąta widocznych pikseli (0 px marginesu)."""
    im = im.convert("RGBA")
    alpha = im.getchannel("A").point(lambda a: 0 if a < floor else a)
    im.putalpha(alpha)
    box = alpha.getbbox()
    return im.crop(box) if box else im


def target_size(w: int, h: int, min_short: int, max_long: int) -> tuple[int, int, str]:
    """Wymiar docelowy: krótsza >= min_short, dłuższa <= max_long. Przy konflikcie wygrywa max_long."""
    scale = 1.0
    note = ""
    if min_short and min(w, h) < min_short:
        scale = min_short / min(w, h)
        note = f"Powiększyłem z {w}×{h} px, żeby krótszy bok miał {min_short} px."
    if max_long and max(w, h) * scale > max_long:
        scale = max_long / max(w, h)
        if min_short and min(w, h) * scale < min_short:
            note = (f"Proporcje nie pozwalają na krótszy bok {min_short} px przy dłuższym {max_long} px: "
                    f"krótszy ma {round(min(w, h) * scale)} px.")
        else:
            note = f"Zmniejszyłem z {w}×{h} px do dłuższego boku {max_long} px."
    return max(1, round(w * scale)), max(1, round(h * scale)), note


def _to_srgb(im: Image.Image) -> Image.Image:
    icc = im.info.get("icc_profile")
    if not icc:
        return im
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        if "srgb" in ImageCms.getProfileDescription(src).lower():
            return im
        mode = "RGBA" if im.mode in ("RGBA", "LA", "PA", "P") else "RGB"
        return ImageCms.profileToProfile(im.convert(mode), src, ImageCms.createProfile("sRGB"), outputMode=mode)
    except Exception:
        return im


def _srgb_icc() -> bytes:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def contain_on_canvas(im: Image.Image, size: int) -> Image.Image:
    """Cały produkt na kwadracie ``size`` px: dłuższy bok = ``size``, reszta przezroczysta, produkt na środku.
    Nigdy nie obcina produktu (dawne pudełko „cover” ucinało górę i dół wysokiej wizki)."""
    im = im.convert("RGBA")
    k = size / max(im.size)
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.paste(im.resize((w, h), Image.LANCZOS), ((size - w) // 2, (size - h) // 2))
    return canvas


def _save(im: Image.Image, path: Path, preset) -> None:
    dpi = preset.dpi or 72
    if preset.output_format == "jpeg":
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im, mask=im.convert("RGBA").getchannel("A"))
        # 4:4:4 bez podpróbkowania koloru (memory.md: JPEG chroma)
        flat.save(path, format="JPEG", quality=preset.quality, optimize=True, subsampling=0,
                  icc_profile=_srgb_icc(), dpi=(dpi, dpi))
        return
    im.save(path, format="PNG", compress_level=9, icc_profile=_srgb_icc(), dpi=(dpi, dpi))


def _pngquant(out: Path, limit: int) -> bool:
    """pngquant na kopii w krótkim folderze tymczasowym: nie otwiera ścieżek dłuższych niż 260 znaków
    (głębokie foldery produktów z polskimi znakami)."""
    import shutil
    import tempfile

    from inyfinn_resizer.core.compressors.png import apply_pngquant

    with tempfile.TemporaryDirectory(prefix="inyfinn-pq-") as tmp:
        work = Path(tmp) / "a.png"
        shutil.copyfile(out, work)
        ok, _ = apply_pngquant(work, max_kb=limit / 1024, quality_pct=90, max_colors=256)
        if ok:
            shutil.copyfile(work, out)
    return ok


def _short_label(preset) -> str:
    return preset.label.split(" \u2014 ")[0]


def export_retail(src: Path, out: Path, preset, *, bg_model: str | None = None) -> list[str]:
    """Zapisuje ``src`` wg presetu sieci (PNG albo JPEG). Zwraca listę komunikatów dla handlowca."""
    notes: list[str] = []
    with Image.open(src) as raw:
        raw.load()
        im = _to_srgb(ImageOps.exif_transpose(raw))
    if not has_real_alpha(im) and preset.output_format != "jpeg":
        from inyfinn_resizer.core.transforms.background_removal import downscale_for_rembg, remove_background

        im = downscale_for_rembg(im.convert("RGB"), preset.max_longest_px or preset.canvas_px or 3800)
        im = remove_background(im, model_name=bg_model or preset.bg_model)
        notes.append("Usunąłem tło (plik nie miał przezroczystości).")
    floor = getattr(preset, "alpha_floor", ALPHA_FLOOR)
    im = trim_to_content(im, floor)
    if preset.canvas_px:
        im = contain_on_canvas(im, preset.canvas_px)
    else:
        w, h, note = target_size(*im.size, preset.min_shortest_px, preset.max_longest_px)
        if note:
            notes.append(note)
        if (w, h) != im.size:
            im = trim_to_content(im.resize((w, h), Image.LANCZOS), floor)

    out.parent.mkdir(parents=True, exist_ok=True)
    _save(im, out, preset)
    limit = int(preset.max_file_mb * 1024 * 1024) if preset.max_file_mb else 0
    if limit and preset.output_format == "png" and out.stat().st_size > limit:
        before = out.stat().st_size
        if _pngquant(out, limit):
            notes.append(f"Plik miał {before / 1048576:.1f} MB, {_short_label(preset)} przyjmuje do "
                         f"{preset.max_file_mb:g} MB: skompresowałem do {out.stat().st_size / 1048576:.1f} MB "
                         "(pngquant, bez zmiany wymiaru).")
        while out.stat().st_size > limit:
            short = min(im.size)
            min_short = preset.min_shortest_px or 1
            if preset.canvas_px or short <= min_short:
                notes.append(f"Plik ma {out.stat().st_size / 1048576:.1f} MB, a {_short_label(preset)} przyjmuje do "
                             f"{preset.max_file_mb:g} MB: nie zmniejszę go bardziej bez zmiany wymaganego wymiaru.")
                break
            k = max(min_short / short, math.sqrt(limit / out.stat().st_size) * 0.95)
            im = trim_to_content(im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS), floor)
            _save(im, out, preset)
            _pngquant(out, limit)
            notes.append(f"Zmniejszyłem do {im.width}×{im.height} px, żeby zmieścić się w {preset.max_file_mb:g} MB.")
    return notes
