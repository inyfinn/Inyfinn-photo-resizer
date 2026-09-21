"""Processing pipeline — load, transform, encode, post-compress."""

from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path

try:
    from PIL import Image as _PilImage

    _PilImage.MAX_IMAGE_PIXELS = 300_000_000
except Exception:
    pass

from inyfinn_resizer.core.compressors import (
    apply_pngquant,
    compress_avif_avifenc,
    compress_gif,
    compress_jpeg_file,
    compress_webp_cwebp,
    optimize_png_oxipng,
    save_avif_capped,
    save_vips_avif_capped,
)
from inyfinn_resizer.core.compressors.avif import avif_max_bytes
from inyfinn_resizer.core.compressors.jpeg import FULL_CHROMA_MIN_QUALITY, full_chroma, pil_subsampling
from inyfinn_resizer.core.formats.registry import output_extension
from inyfinn_resizer.core.job import JobResult, JobSpec, JobStatus
from inyfinn_resizer.core.metadata.exif import strip_metadata_file
from inyfinn_resizer.core.transforms.image_ops import apply_resize, apply_scale_postprocess, apply_transforms
from inyfinn_resizer.core.transforms.matte import apply_jpeg_matte
from inyfinn_resizer.core.transforms.background_removal import (
    downscale_for_rembg,
    rembg_max_edge,
    remove_background,
)
from inyfinn_resizer.core.image_loader import open_image
from inyfinn_resizer.core.video import convert_video, is_video_file
from inyfinn_resizer.core.transforms.rgb_bitmap import rgb_bitmap, vips_rgb_bitmap
from inyfinn_resizer.core.transforms.pillow_ops import apply_resize_pil, apply_scale_postprocess_pil, apply_transforms_pil
from inyfinn_resizer.core.compressors.png import (
    MAX_PALETTE_COLORS,
    count_rare_green_accents,
    resolve_png_max_colors,
)
from inyfinn_resizer.utils.paths import bootstrap_runtime_paths, bundled_libvips, ensure_vips_lib

_VIPS_READY = False
_VIPS_LOCK = threading.Lock()


def _init_vips() -> bool:
    global _VIPS_READY
    with _VIPS_LOCK:
        if _VIPS_READY:
            return True
        if not bundled_libvips():
            return False
        bootstrap_runtime_paths()
        ensure_vips_lib()
        try:
            import pyvips

            pyvips.Image.black(1, 1)
            _VIPS_READY = True
            return True
        except Exception:
            return False


def _polish_error(exc: Exception) -> str:
    if isinstance(exc, UnicodeDecodeError):
        return (
            "Błąd DirectML/ONNX przy usuwaniu tła — spróbuj ponownie "
            "(aplikacja przełączy się na CPU)."
        )
    msg = str(exc).strip() or exc.__class__.__name__
    low = msg.lower()
    if "decompressionbomb" in low or "exceeds limit" in low:
        return "Obraz jest za duży — zmniejsz wymiary w Formacie lub Zaawansowane."
    if "cannot identify image" in low:
        return "Nie rozpoznano pliku jako obrazu."
    if "nie można odnaleźć" in low or "nie mozna odnalezc" in low:
        return "Brak biblioteki narzędzia (pngquant/gifsicle) — przebuduj BIN\\build.bat."
    if "permission" in low or "odmowa dostępu" in low:
        return "Brak uprawnień do zapisu w folderze wyjściowym."
    if "truncated file read" in low or "truncated" in low:
        return "Błąd odczytu pliku (uszkodzony lub nadpisany w trakcie zapisu)."
    if "libvips" in low or "dll" in low or "vips" in low:
        return f"Błąd dekodowania obrazu: {msg}"
    if "rembg" in low or "onnx" in low or "u2net" in low or "birefnet" in low:
        return f"Usuwanie tła: {msg}"
    if "brak modelu" in low:
        return msg
    return msg


def _is_cmyk_tiff(path: Path) -> bool:
    """CMYK TIFF wymaga ICC z image_loader — pyvips daje złe kolory."""
    if path.suffix.lower() not in (".tif", ".tiff"):
        return False
    try:
        import tifffile

        with tifffile.TiffFile(str(path)) as tf:
            page = tf.pages[0]
            if int(page.photometric) == 5:
                return True
            data = page.asarray()
            return data is not None and getattr(data, "ndim", 0) == 3 and data.shape[2] in (4, 5)
    except Exception:
        return False


def _load_image(job: JobSpec):
    import pyvips

    access = "sequential"
    image = pyvips.Image.new_from_file(str(job.input_path), access=access)
    if job.transforms.auto_rotate_exif:
        try:
            image = image.autorot()
        except Exception:
            pass
    try:
        if image.interpretation in ("cmyk", "cmyk-alpha"):
            image = image.colourspace("srgb")
    except Exception:
        pass
    image = apply_transforms(image, job.transforms)
    image = apply_resize(image, job.resize)
    image = apply_scale_postprocess(image, job.resize)
    return image


def _effective_lossy_quality(source: Path, quality: int) -> int:
    """Podbija jakość do 92, gdy źródło ma rzadkie zielone akcenty — tylko przy jakości ≥ 70.

    Poniżej 70 użytkownik chce małego pliku: podbicie nadpisywało suwak (35/50/75 → ten sam plik).
    """
    if quality < FULL_CHROMA_MIN_QUALITY:
        return quality
    if count_rare_green_accents(source) > 0:
        return max(quality, 92)
    return quality


def _save_vips(image, path: Path, fmt: str, opts, *, source_path: Path | None = None) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    q = max(0, min(100, opts.quality))
    if source_path and fmt in ("webp", "jpeg") and not opts.lossless:
        q = _effective_lossy_quality(source_path, q)

    if fmt == "jpeg":
        image = apply_jpeg_matte(image, opts)
        image.jpegsave(
            str(path), Q=q, strip=not opts.keep_metadata,
            optimize_coding=opts.optimize, interlace=opts.progressive,
            subsample_mode="off" if full_chroma(q, opts.subsampling) else "on",
        )
    elif fmt == "png":
        image.pngsave(str(path), compression=6, strip=not opts.keep_metadata)
    elif fmt == "webp":
        image.webpsave(str(path), Q=q, lossless=opts.lossless, strip=not opts.keep_metadata)
    elif fmt == "avif":
        if getattr(opts, "rgb_bitmap_only", True):
            image = vips_rgb_bitmap(image)
        cap = None if opts.lossless else avif_max_bytes(opts.avif_max_kb)
        if not save_vips_avif_capped(
            image,
            path,
            max_bytes=cap,
            quality=q,
            lossless=opts.lossless,
        ):
            image.heifsave(str(path), Q=q, lossless=opts.lossless, strip=True)
    elif fmt == "heic":
        image.heifsave(str(path), Q=q, strip=not opts.keep_metadata)
    elif fmt == "tiff":
        image.tiffsave(str(path), compression="jpeg" if not opts.lossless else "none", Q=q)
    elif fmt == "bmp":
        image.bmpsave(str(path))
    elif fmt == "gif":
        image = image.colourspace("srgb") if image.bands >= 3 else image
        image.gifsave(str(path))
    elif fmt == "jp2":
        # jpegsave zapisywał zwykły JPEG pod rozszerzeniem .jp2 — JPEG2000 idzie przez Pillow (OpenJPEG).
        raise OSError("JPEG2000 przez Pillow")
    elif fmt == "pdf":
        image.pdfsave(str(path))
    else:
        image.write_to_file(str(path))


def _save_png(im, path: Path) -> None:
    """Pillow optimize=True na dużym RGBA potrafi trwać minuty — zlib 6 wystarcza."""
    im.save(path, format="PNG", optimize=False, compress_level=6)


def _save_pillow_rgba(job: JobSpec, out_path: Path) -> None:
    """Pipeline z usunięciem tła — zachowuje kanał alpha."""
    from PIL import Image

    im = open_image(job.input_path)
    try:
        im = apply_transforms_pil(im, job.transforms)
        im = apply_resize_pil(im, job.resize)
        im = apply_scale_postprocess_pil(im, job.resize)
        cap = rembg_max_edge(
            box_w=job.resize.box_w,
            box_h=job.resize.box_h,
            width=job.resize.width,
            height=job.resize.height,
            dimension=job.resize.dimension,
        )
        im = downscale_for_rembg(im, cap)
        im = remove_background(
            im,
            model_name=job.transforms.bg_model,
            alpha_matting=job.transforms.bg_alpha_matting,
            post_process_mask=job.transforms.bg_post_process_mask,
        )
        if im.mode != "RGBA":
            im = im.convert("RGBA")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = job.output_format.lower()
        opts = job.format_opts
        quality = max(0, min(100, opts.quality))
        if not opts.lossless and fmt in ("webp", "jpeg"):
            quality = _effective_lossy_quality(job.input_path, quality)

        if fmt == "png":
            _save_png(im, out_path)
        elif fmt == "webp":
            im.save(
                out_path,
                format="WEBP",
                quality=quality,
                method=4,
                lossless=opts.lossless,
            )
        elif fmt == "avif":
            cap = None if opts.lossless else avif_max_bytes(opts.avif_max_kb)
            if getattr(opts, "rgb_bitmap_only", True):
                flat = rgb_bitmap(im)
                if not save_avif_capped(
                    flat, out_path, max_bytes=cap, quality=quality, lossless=opts.lossless
                ):
                    _save_avif_rgba(flat, out_path, quality, opts.lossless, max_bytes=cap)
            else:
                _save_avif_rgba(im, out_path, quality, opts.lossless, max_bytes=cap)
        elif fmt == "jpeg":
            flat = Image.new("RGB", im.size, (255, 255, 255))
            flat.paste(im, mask=im.split()[-1])
            flat.save(
                out_path, format="JPEG", quality=quality, optimize=True,
                subsampling=pil_subsampling(quality, opts.subsampling),
            )
        else:
            _save_png(im, out_path)
    finally:
        im.close()


def _save_avif_rgba(im, out_path: Path, quality: int, lossless: bool, max_bytes: int | None = None) -> None:
    if im.mode in ("RGB", "RGBA") and not lossless:
        if save_avif_capped(im, out_path, max_bytes=max_bytes, quality=quality, lossless=False):
            return
    tmp = out_path.with_suffix(".rgba.tmp.png")
    try:
        im.save(tmp, format="PNG")
        ok, msg = compress_avif_avifenc(tmp, out_path, quality, lossless)
        if ok:
            return
        raise OSError(msg or "avifenc")
    finally:
        tmp.unlink(missing_ok=True)


def _save_pillow_fallback(job: JobSpec, out_path: Path) -> None:
    im = open_image(job.input_path)
    try:
        im = apply_transforms_pil(im, job.transforms)
        im = apply_resize_pil(im, job.resize)
        im = apply_scale_postprocess_pil(im, job.resize)
        fmt = job.output_format.lower()
        if fmt in ("jpeg", "jpg", "bmp", "pdf", "jp2"):
            im = rgb_bitmap(im)
        elif fmt == "avif" and job.format_opts.rgb_bitmap_only:
            im = rgb_bitmap(im)
        elif im.mode == "CMYK":
            im = im.convert("RGB")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fmt_save = job.output_format.upper()
        quality = job.format_opts.quality
        if not job.format_opts.lossless and fmt_save in ("WEBP", "JPEG", "JPG"):
            quality = _effective_lossy_quality(job.input_path, quality)
        if fmt_save in ("JPEG", "JPG"):
            fmt_save = "JPEG"
            im.save(
                out_path, format=fmt_save, quality=quality, optimize=True,
                progressive=job.format_opts.progressive,
                subsampling=pil_subsampling(quality, job.format_opts.subsampling),
            )
        elif fmt_save == "WEBP":
            im.save(out_path, format="WEBP", quality=quality)
        elif fmt_save == "PNG":
            _save_png(im, out_path)
        elif fmt_save == "AVIF":
            cap = None if job.format_opts.lossless else avif_max_bytes(job.format_opts.avif_max_kb)
            if not save_avif_capped(
                im, out_path, max_bytes=cap, quality=quality, lossless=job.format_opts.lossless
            ):
                _save_png(im, out_path)
                raise OSError("AVIF: nie udało się zapisać w limicie wagi")
        elif fmt_save == "TIFF":
            im.save(out_path, format="TIFF", compression="tiff_lzw")
        elif fmt_save == "HEIC":
            _save_heic_pillow(im, out_path, quality)
        elif fmt_save == "JP2":
            _save_jp2_pillow(im, out_path, quality)
        else:
            im.save(out_path)
    finally:
        im.close()


_ANIMATED_INPUTS = (".gif", ".webp", ".png", ".apng")
_ANIMATED_OUTPUTS = ("gif", "webp")


def _animated_frame_count(path: Path) -> int:
    if path.suffix.lower() not in _ANIMATED_INPUTS:
        return 1
    try:
        from PIL import Image

        with Image.open(path) as im:
            return int(getattr(im, "n_frames", 1) or 1)
    except Exception:
        return 1


def _has_pixel_changes(job: JobSpec) -> bool:
    """Czy obraz trzeba przeliczyć (wymiary/obrót/kadr), czy wystarczy kopia pliku."""
    r, t = job.resize, job.transforms
    if r.mode.value != "none" or float(r.scale_percent) != 100.0 or r.min_longest_enabled:
        return True
    return bool(
        t.rotate % 360
        or t.flip_h
        or t.flip_v
        or t.trim_transparent
        or (t.crop_w > 0 and t.crop_h > 0)
        or t.grayscale
    )


def _save_animated(job: JobSpec, out_path: Path) -> None:
    """Animacja GIF/WebP/APNG → GIF/WebP: każda klatka przechodzi te same transformacje."""
    from dataclasses import replace

    from PIL import Image

    from inyfinn_resizer.core.job import ResizeMode

    # Przycinanie do przezroczystości liczy inny kadr dla każdej klatki — animacja by skakała.
    transforms = replace(job.transforms, trim_transparent=False, auto_rotate_exif=False)
    resize = job.resize
    if resize.mode == ResizeMode.CROP_SMART:
        resize = replace(resize, mode=ResizeMode.FIT_BOX)

    frames: list = []
    durations: list[int] = []
    with Image.open(job.input_path) as src:
        loop = int(src.info.get("loop", 0) or 0)
        for index in range(int(getattr(src, "n_frames", 1))):
            src.seek(index)
            durations.append(int(src.info.get("duration", 80) or 80))
            frame = src.convert("RGBA")
            frame = apply_transforms_pil(frame, transforms)
            frame = apply_resize_pil(frame, resize)
            frame = apply_scale_postprocess_pil(frame, resize)
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            frames.append(frame)

    if not frames:
        raise OSError("Animacja nie zawiera klatek")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = job.output_format.lower()
    opts = job.format_opts
    try:
        if fmt == "gif":
            frames[0].save(
                out_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop,
                disposal=2,
                optimize=False,
            )
        else:
            frames[0].save(
                out_path,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop,
                quality=max(0, min(100, opts.quality)),
                method=4,
                lossless=opts.lossless,
            )
    finally:
        for frame in frames:
            frame.close()


def _save_heic_pillow(im: Image.Image, out_path: Path, quality: int) -> None:
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        im.save(out_path, format="HEIF", quality=quality)
        return
    except Exception:
        pass
    tmp = out_path.with_suffix(".png")
    im.save(tmp, format="PNG")
    try:
        from inyfinn_resizer.core.compressors.external import convert_with_tool

        if convert_with_tool("heif-enc", tmp, out_path, quality):
            return
    finally:
        tmp.unlink(missing_ok=True)
    raise OSError("Brak enkodera HEIC — zainstaluj pillow-heif lub heif-enc w tools/")


def _save_jp2_pillow(im: Image.Image, out_path: Path, quality: int) -> None:
    try:
        q = max(0, min(100, int(quality)))
        if q >= 100:
            im.save(out_path, format="JPEG2000", irreversible=False)
            return
        # PSNR w dB: 50% ≈ 36 dB, 90% ≈ 44 dB — „rates” z ułamkiem <1 dawał plik bez kompresji.
        im.save(
            out_path,
            format="JPEG2000",
            irreversible=True,
            quality_mode="dB",
            quality_layers=[26.0 + 0.2 * q],
        )
    except Exception as exc:
        raise OSError(f"JPEG2000: {exc}") from exc


def unique_conv_path(path: Path) -> Path:
    """photo.png → photo_conv.png; zajęte → photo_conv2.png, photo_conv3.png…"""
    stem, ext = path.stem, path.suffix
    candidate = path.with_name(f"{stem}_conv{ext}")
    n = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem}_conv{n}{ext}")
        n += 1
    return candidate


def _post_compress(path: Path, fmt: str, opts, *, source_bytes: int = 0) -> str:
    detail = ""
    if fmt == "png" and not opts.lossless:
        if opts.png_mode == "png24":
            optimize_png_oxipng(path)
            return "oxipng (png24)"
        target_kb = opts.target_kb
        force_colors = resolve_png_max_colors(opts)
        if opts.png_mode == "png8":
            force_colors = min(force_colors or MAX_PALETTE_COLORS, MAX_PALETTE_COLORS)
        if force_colors is None:
            optimize_png_oxipng(path)
            return detail or "oxipng (pełna głębia)"
        ok, detail = apply_pngquant(
            path,
            target_kb=target_kb,
            target_tolerance=opts.target_tolerance,
            quality_pct=opts.quality,
            max_colors=force_colors,
        )
        if not ok:
            optimize_png_oxipng(path)
    elif fmt == "jpeg" and opts.target_kb:
        # Bez limitu wagi JPG jest gotowy po pierwszym zapisie — każde ponowne kodowanie
        # to kolejna strata (wcześniej 6–7 przebiegów wyszukiwania przy każdym pliku).
        compress_jpeg_file(
            path,
            quality=opts.quality,
            target_kb=opts.target_kb,
            target_tolerance=opts.target_tolerance,
            subsampling_mode=opts.subsampling,
        )
    elif fmt == "webp":
        tmp = path.with_suffix(".cwebp.tmp.webp")
        ok, msg = compress_webp_cwebp(path, tmp, opts.quality, opts.lossless)
        if ok and tmp.exists() and tmp.stat().st_size < path.stat().st_size:
            shutil.move(str(tmp), str(path))
            detail = msg
        else:
            tmp.unlink(missing_ok=True)
    elif fmt == "avif":
        cap = avif_max_bytes(opts.avif_max_kb)
        if not cap:
            return detail
        if path.is_file() and path.stat().st_size <= cap:
            return detail
        from PIL import Image as _AvifIm

        try:
            with _AvifIm.open(path) as im:
                rgb = rgb_bitmap(im) if opts.rgb_bitmap_only else im.convert("RGB")
                save_avif_capped(
                    rgb,
                    path,
                    max_bytes=cap,
                    quality=opts.quality,
                    lossless=opts.lossless,
                )
                detail = "avif-capped"
        except Exception:
            tmp = path.with_suffix(".avif.tmp.avif")
            ok, msg = compress_avif_avifenc(path, tmp, opts.quality, opts.lossless)
            if ok and tmp.exists():
                shutil.move(str(tmp), str(path))
                detail = msg
            else:
                tmp.unlink(missing_ok=True)
    elif fmt == "gif":
        tmp = path.with_suffix(".gif.tmp.gif")
        gif_lossy = opts.gif_lossy
        gif_colors = opts.gif_max_colors
        if opts.gif_from_quality and opts.gif_mode == "quality":
            from inyfinn_resizer.core.quality_map import gif_lossy_for_quality, palette_colors_for_quality

            gif_lossy = gif_lossy_for_quality(opts.quality)
            gif_colors = palette_colors_for_quality(opts.quality)
        ok, msg = compress_gif(
            path,
            tmp,
            mode=opts.gif_mode,
            level=opts.gif_level,
            quality=opts.quality,
            dither=opts.gif_dither,
            lossy=gif_lossy,
            colors=gif_colors if opts.gif_mode == "quality" else None,
            ultra_max_frames=opts.gif_ultra_max_frames,
            ultra_lossy=opts.gif_ultra_lossy,
        )
        if ok and tmp.exists():
            shutil.move(str(tmp), str(path))
            detail = msg
    return detail


def process_job(job: JobSpec, *, overwrite: bool = True) -> JobResult:
    result = JobResult(job=job)
    inp = job.input_path.resolve()
    out = job.output_path.resolve()
    job = JobSpec(
        input_path=inp,
        output_path=out,
        output_format=job.output_format,
        resize=job.resize,
        transforms=job.transforms,
        watermark=job.watermark,
        metadata=job.metadata,
        format_opts=job.format_opts,
        rename=job.rename,
        preserve_folder_structure=job.preserve_folder_structure,
        ask_before_overwrite=job.ask_before_overwrite,
    )
    result.job = job

    from inyfinn_resizer.utils.frozen_stdio import ensure_stdio

    ensure_stdio()

    if not inp.is_file():
        result.status = JobStatus.ERROR
        result.message = "Nie znaleziono pliku wejściowego"
        return result

    result.old_bytes = inp.stat().st_size

    if out.exists() and not overwrite:
        result.status = JobStatus.SKIPPED
        result.message = "Plik istnieje — pominięto"
        result.new_bytes = out.stat().st_size
        return result

    in_place = inp == out
    staging = out.with_name(f".{out.name}.inyfinn.tmp") if in_place else out
    if staging.exists():
        staging.unlink(missing_ok=True)

    fmt = job.output_format.lower()

    try:
        try:
            staging.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OSError(f"Nie można utworzyć folderu wyjściowego: {staging.parent}") from exc

        src_bytes = result.old_bytes
        cmyk_tiff = _is_cmyk_tiff(inp)
        if is_video_file(inp):
            # Wideo ma własną ścieżkę: klatki z ffmpeg, scalanie zamrożeń, zapis animacji.
            if fmt != "gif":
                raise OSError("Film zapisujemy jako GIF — wybierz format GIF dla tego pliku.")
            result.message = convert_video(inp, staging, job.format_opts)
            if not staging.is_file() or staging.stat().st_size == 0:
                raise OSError("Nie udało się zapisać animacji")
            if in_place:
                os.replace(staging, out)
            result.new_bytes = out.stat().st_size
            result.status = JobStatus.OK
            return result

        use_vips = not cmyk_tiff and fmt not in ("bmp", "jp2") and _init_vips()
        animated = (
            fmt in _ANIMATED_OUTPUTS
            and not job.transforms.remove_background
            and _animated_frame_count(inp) > 1
        )
        if job.transforms.remove_background:
            _save_pillow_rgba(job, staging)
        elif fmt == "gif" and inp.suffix.lower() == ".gif" and not _has_pixel_changes(job):
            shutil.copy2(inp, staging)
        elif animated:
            _save_animated(job, staging)
        elif use_vips:
            try:
                image = _load_image(job)
                _save_vips(image, staging, fmt, job.format_opts, source_path=job.input_path)
            except Exception:
                _save_pillow_fallback(job, staging)
        else:
            _save_pillow_fallback(job, staging)

        if not staging.is_file() or staging.stat().st_size == 0:
            raise OSError("Zapis pliku wyjściowego nie powiódł się")

        # cwebp czyta tylko nieruchome obrazy — na animowanym WebP zostawiłby jedną klatkę.
        if not (animated and fmt == "webp"):
            try:
                _post_compress(staging, fmt, job.format_opts, source_bytes=src_bytes)
            except Exception:
                pass  # pngquant/gifsicle opcjonalne — plik już zapisany

        if (
            job.metadata.strip_all
            or not job.metadata.keep_exif
            or (fmt == "avif" and job.format_opts.rgb_bitmap_only)
        ):
            strip_metadata_file(staging, job.metadata)

        if in_place:
            os.replace(staging, out)
        result.new_bytes = out.stat().st_size
        result.status = JobStatus.OK
        result.message = "OK"
    except Exception as exc:
        result.status = JobStatus.ERROR
        result.message = _polish_error(exc)
        if job.transforms.remove_background:
            try:
                from inyfinn_resizer.utils.app_log import log_event

                log_event("Usuwanie tła", result.message, status="ERROR")
            except OSError:
                pass
        if staging.exists() and staging != out:
            staging.unlink(missing_ok=True)
        elif out.exists() and in_place and out.stat().st_size == 0:
            out.unlink(missing_ok=True)

    return result


def build_output_path(
    input_path: Path,
    output_dir: Path,
    output_format: str,
    base_root: Path | None = None,
    preserve_structure: bool = True,
    segregate_by_extension: bool = False,
) -> Path:
    ext = output_extension(output_format)
    root = output_dir
    if segregate_by_extension:
        sub = ext.lstrip(".").lower() or output_format.lower()
        root = output_dir / sub
    if preserve_structure and base_root is not None:
        try:
            if base_root in input_path.parents:
                rel = input_path.relative_to(base_root)
                return root / rel.parent / (input_path.stem + ext)
        except ValueError:
            pass
        parent_name = input_path.parent.name
        if parent_name:
            return root / parent_name / (input_path.stem + ext)
    return root / (input_path.stem + ext)


class ProcessingPipeline:
    """High-level batch API."""

    def process(self, job: JobSpec, overwrite: bool = True) -> JobResult:
        return process_job(job, overwrite=overwrite)

    def process_many(self, jobs: list[JobSpec], overwrite: bool = True) -> list[JobResult]:
        return [self.process(j, overwrite=overwrite) for j in jobs]
