"""Processing pipeline — load, transform, encode, post-compress."""

from __future__ import annotations

import os
import shutil
import sys
import threading
from contextlib import nullcontext
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
)
from inyfinn_resizer.core.formats.registry import output_extension
from inyfinn_resizer.core.job import JobResult, JobSpec, JobStatus
from inyfinn_resizer.core.metadata.exif import strip_metadata_file
from inyfinn_resizer.core.transforms.image_ops import apply_resize, apply_scale_postprocess, apply_transforms
from inyfinn_resizer.core.transforms.matte import apply_jpeg_matte
from inyfinn_resizer.core.image_loader import ensure_export_rgb, open_image
from inyfinn_resizer.core.transforms.pillow_ops import apply_resize_pil, apply_scale_postprocess_pil, apply_transforms_pil
from inyfinn_resizer.core.compressors.png import resolve_png_max_colors, count_rare_green_accents
from inyfinn_resizer.utils.paths import bootstrap_runtime_paths, bundled_libvips, ensure_vips_lib

_VIPS_READY = False
_VIPS_LOCK = threading.Lock()
_PROCESS_LOCK = threading.Lock()


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
    """Podbija jakość, gdy źródło ma rzadkie zielone akcenty."""
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
        )
    elif fmt == "png":
        compression = 9 if opts.optimize else 6
        image.pngsave(str(path), compression=compression, strip=not opts.keep_metadata)
    elif fmt == "webp":
        image.webpsave(str(path), Q=q, lossless=opts.lossless, strip=not opts.keep_metadata)
    elif fmt == "avif":
        image.heifsave(str(path), Q=q, lossless=opts.lossless, strip=not opts.keep_metadata)
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
        image.jpegsave(str(path), Q=q)
    elif fmt == "pdf":
        image.pdfsave(str(path))
    else:
        image.write_to_file(str(path))


def _save_pillow_fallback(job: JobSpec, out_path: Path) -> None:
    im = open_image(job.input_path)
    try:
        im = apply_transforms_pil(im, job.transforms)
        im = apply_resize_pil(im, job.resize)
        im = apply_scale_postprocess_pil(im, job.resize)
        im = ensure_export_rgb(im)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = job.output_format.upper()
        quality = job.format_opts.quality
        if not job.format_opts.lossless and fmt in ("WEBP", "JPEG", "JPG"):
            quality = _effective_lossy_quality(job.input_path, quality)
        if fmt in ("JPEG", "JPG"):
            fmt = "JPEG"
            im.save(out_path, format=fmt, quality=quality, optimize=True)
        elif fmt == "WEBP":
            im.save(out_path, format="WEBP", quality=quality)
        elif fmt == "PNG":
            im.save(out_path, format="PNG", optimize=True)
        elif fmt == "TIFF":
            im.save(out_path, format="TIFF", compression="tiff_lzw")
        elif fmt == "HEIC":
            _save_heic_pillow(im, out_path, quality)
        elif fmt == "JP2":
            _save_jp2_pillow(im, out_path, quality)
        else:
            im.save(out_path)
    finally:
        im.close()


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
        im.save(out_path, format="JPEG2000", quality_mode="rates", quality_layers=[quality / 100.0])
    except Exception as exc:
        raise OSError(f"JPEG2000: {exc}") from exc


def _post_compress(path: Path, fmt: str, opts, *, source_bytes: int = 0) -> str:
    detail = ""
    if fmt == "png" and not opts.lossless:
        if opts.png_mode == "png24":
            optimize_png_oxipng(path)
            return detail
        target_kb = opts.target_kb
        force_colors = resolve_png_max_colors(opts)
        if opts.png_mode == "png8":
            force_colors = min(force_colors, 256)
        ok, detail = apply_pngquant(
            path,
            target_kb=target_kb,
            target_tolerance=opts.target_tolerance,
            quality_pct=opts.quality,
            max_colors=force_colors,
        )
        if not ok:
            optimize_png_oxipng(path)
    elif fmt == "jpeg":
        compress_jpeg_file(
            path,
            quality=opts.quality,
            target_kb=opts.target_kb,
            target_tolerance=opts.target_tolerance,
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
        tmp = path.with_suffix(".avif.tmp.avif")
        ok, msg = compress_avif_avifenc(path, tmp, opts.quality, opts.lossless)
        if ok and tmp.exists():
            shutil.move(str(tmp), str(path))
            detail = msg
        else:
            tmp.unlink(missing_ok=True)
    elif fmt == "gif":
        tmp = path.with_suffix(".gif.tmp.gif")
        ok, msg = compress_gif(
            path, tmp,
            quality=opts.quality,
            dither=opts.gif_dither,
            lossy=opts.gif_lossy,
            colors=opts.gif_max_colors if opts.gif_from_quality else None,
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

    lock = _PROCESS_LOCK if getattr(sys, "frozen", False) else nullcontext()
    fmt = job.output_format.lower()

    try:
        with lock:
            try:
                staging.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise OSError(f"Nie można utworzyć folderu wyjściowego: {staging.parent}") from exc

            src_bytes = result.old_bytes
            cmyk_tiff = _is_cmyk_tiff(inp)
            use_vips = not cmyk_tiff and fmt not in ("bmp",) and _init_vips()
            if fmt == "gif" and inp.suffix.lower() == ".gif" and job.resize.mode.value == "none":
                shutil.copy2(inp, staging)
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

            try:
                _post_compress(staging, fmt, job.format_opts, source_bytes=src_bytes)
            except Exception:
                pass  # pngquant/gifsicle opcjonalne — plik już zapisany

            if job.metadata.strip_all or not job.metadata.keep_exif:
                strip_metadata_file(staging, job.metadata)

            if in_place:
                os.replace(staging, out)
            result.new_bytes = out.stat().st_size
            result.status = JobStatus.OK
            result.message = "OK"
    except Exception as exc:
        result.status = JobStatus.ERROR
        result.message = _polish_error(exc)
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
    if preserve_structure and base_root and base_root in input_path.parents:
        rel = input_path.relative_to(base_root)
        return root / rel.parent / (input_path.stem + ext)
    return root / (input_path.stem + ext)


class ProcessingPipeline:
    """High-level batch API."""

    def process(self, job: JobSpec, overwrite: bool = True) -> JobResult:
        return process_job(job, overwrite=overwrite)

    def process_many(self, jobs: list[JobSpec], overwrite: bool = True) -> list[JobResult]:
        return [self.process(j, overwrite=overwrite) for j in jobs]
