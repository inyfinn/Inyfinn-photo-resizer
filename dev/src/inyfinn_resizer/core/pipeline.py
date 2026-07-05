"""Processing pipeline — load, transform, encode, post-compress."""

from __future__ import annotations

import shutil
from pathlib import Path

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
from inyfinn_resizer.core.transforms.image_ops import apply_resize, apply_transforms
from inyfinn_resizer.utils.paths import ensure_vips_lib

_VIPS_READY = False


def _init_vips() -> bool:
    global _VIPS_READY
    if _VIPS_READY:
        return True
    ensure_vips_lib()
    try:
        import pyvips  # noqa: F401
        _VIPS_READY = True
        return True
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
    image = apply_transforms(image, job.transforms)
    image = apply_resize(image, job.resize)
    return image


def _save_vips(image, path: Path, fmt: str, opts) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    q = max(0, min(100, opts.quality))

    if fmt == "jpeg":
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
    elif fmt == "jxl":
        image.jxlsave(str(path), Q=q, lossless=opts.lossless)
    elif fmt == "jp2":
        image.jpegsave(str(path), Q=q)
    elif fmt == "pdf":
        image.pdfsave(str(path))
    else:
        image.write_to_file(str(path))


def _save_pillow_fallback(job: JobSpec, out_path: Path) -> None:
    from PIL import Image

    im = Image.open(job.input_path)
    im.load()
    if job.transforms.auto_rotate_exif:
        try:
            from PIL import ImageOps
            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = job.output_format.upper()
    if fmt in ("JPEG", "JPG"):
        fmt = "JPEG"
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(out_path, format=fmt, quality=job.format_opts.quality, optimize=True)
    elif fmt == "WEBP":
        im.save(out_path, format="WEBP", quality=job.format_opts.quality)
    elif fmt == "PNG":
        im.save(out_path, format="PNG", optimize=True)
    else:
        im.save(out_path)


def _post_compress(path: Path, fmt: str, opts, *, source_bytes: int = 0) -> str:
    detail = ""
    if fmt == "png" and not opts.lossless:
        ok, detail = apply_pngquant(
            path,
            target_kb=opts.target_kb,
            target_tolerance=opts.target_tolerance,
            quality_pct=opts.quality,
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
        ok, msg = compress_gif(path, tmp, quality=opts.quality)
        if ok and tmp.exists():
            shutil.move(str(tmp), str(path))
            detail = msg
    return detail


def process_job(job: JobSpec, *, overwrite: bool = True) -> JobResult:
    result = JobResult(job=job)
    inp = job.input_path
    out = job.output_path

    if not inp.is_file():
        result.status = JobStatus.ERROR
        result.message = "Input file not found"
        return result

    result.old_bytes = inp.stat().st_size

    if out.exists() and not overwrite:
        result.status = JobStatus.SKIPPED
        result.message = "Exists — skipped"
        result.new_bytes = out.stat().st_size
        return result

    out.parent.mkdir(parents=True, exist_ok=True)
    fmt = job.output_format.lower()

    try:
        src_bytes = result.old_bytes
        if fmt == "gif" and inp.suffix.lower() == ".gif" and job.resize.mode.value == "none":
            shutil.copy2(inp, out)
            _post_compress(out, fmt, job.format_opts, source_bytes=src_bytes)
        elif _init_vips():
            image = _load_image(job)
            _save_vips(image, out, fmt, job.format_opts)
            _post_compress(out, fmt, job.format_opts, source_bytes=src_bytes)
        else:
            _save_pillow_fallback(job, out)
            _post_compress(out, fmt, job.format_opts, source_bytes=src_bytes)

        if job.metadata.strip_all or not job.metadata.keep_exif:
            strip_metadata_file(out, job.metadata)

        result.new_bytes = out.stat().st_size if out.exists() else 0
        result.status = JobStatus.OK
        result.message = "OK"
    except Exception as exc:
        result.status = JobStatus.ERROR
        result.message = str(exc)
        if out.exists() and out.stat().st_size == 0:
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
