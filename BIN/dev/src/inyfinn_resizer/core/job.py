"""Job specification and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    OK = "OK"
    ERROR = "ERROR"
    SKIPPED = "skipped"


class ResizeMode(str, Enum):
    NONE = "none"
    PIXELS = "pixels"
    PERCENT = "percent"
    ONE_SIDE = "one_side"
    MAX_DIMENSION = "max_dimension"
    CROP_SMART = "crop_smart"
    FIT_BOX = "fit_box"


@dataclass
class ResizeOptions:
    mode: ResizeMode = ResizeMode.NONE
    width: int = 0
    height: int = 0
    percent: float = 100.0
    side: str = "width"  # width | height | longer | shorter
    dimension: int = 1800
    box_w: int = 0
    box_h: int = 0
    smart_margin: int = 90
    preserve_aspect: bool = True
    skip_if_smaller: bool = True
    filter_name: str = "lanczos3"
    scale_percent: float = 100.0
    min_longest_enabled: bool = True
    min_longest_px: int = 1080


@dataclass
class TransformOptions:
    rotate: int = 0
    flip_h: bool = False
    flip_v: bool = False
    auto_rotate_exif: bool = True
    trim_transparent: bool = False
    trim_margin: int = 0
    crop_x: int = 0
    crop_y: int = 0
    crop_w: int = 0
    crop_h: int = 0
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    grayscale: bool = False
    sepia: bool = False
    remove_background: bool = False
    bg_model: str = "birefnet-general"
    bg_alpha_matting: bool = True
    bg_post_process_mask: bool = True


@dataclass
class WatermarkOptions:
    enabled: bool = False
    text: str = ""
    image_path: str = ""
    opacity: float = 0.5
    position: str = "bottom-right"
    scale: float = 1.0


@dataclass
class MetadataPolicy:
    keep_exif: bool = True
    keep_iptc: bool = True
    keep_xmp: bool = True
    strip_all: bool = False
    icc_to_srgb: bool = False


DEFAULT_QUALITY = 50


@dataclass
class FormatOptions:
    quality: int = DEFAULT_QUALITY
    lossless: bool = False
    progressive: bool = True
    optimize: bool = True
    keep_metadata: bool = True
    subsampling: str = "medium"
    smoothing: int = 0
    target_kb: float | None = None
    target_tolerance: float = 0.2
    png_max_colors: int = 256
    png_colors_auto: bool = True
    png_mode: str = "auto"  # auto | png8 | png24
    jpeg_matte_mode: str = "white"  # white | black | custom | gradient
    jpeg_matte_color: str = "#ffffff"
    jpeg_matte_color2: str = "#000000"
    jpeg_gradient_type: str = "linear"  # linear | radial
    jpeg_gradient_reverse: bool = False
    jpeg_matte_noise: bool = False
    gif_dither: bool = True
    gif_lossy: int = 0
    gif_max_colors: int = 256
    gif_from_quality: bool = True
    gif_mode: str = "quality"  # quality | frames | ultra
    gif_level: int = 6
    gif_ultra_max_frames: int = 4
    gif_ultra_lossy: int = 70


@dataclass
class RenameRule:
    enabled: bool = False
    template: str = "{name}_{counter:04d}"
    search: str = ""
    replace: str = ""
    uppercase_ext: bool = False


@dataclass
class JobSpec:
    input_path: Path
    output_path: Path
    output_format: str = "webp"
    resize: ResizeOptions = field(default_factory=ResizeOptions)
    transforms: TransformOptions = field(default_factory=TransformOptions)
    watermark: WatermarkOptions = field(default_factory=WatermarkOptions)
    metadata: MetadataPolicy = field(default_factory=MetadataPolicy)
    format_opts: FormatOptions = field(default_factory=FormatOptions)
    rename: RenameRule = field(default_factory=RenameRule)
    preserve_folder_structure: bool = True
    ask_before_overwrite: bool = True


@dataclass
class JobResult:
    job: JobSpec
    status: JobStatus = JobStatus.PENDING
    message: str = ""
    old_bytes: int = 0
    new_bytes: int = 0

    @property
    def ratio_pct(self) -> float:
        if self.old_bytes <= 0:
            return 100.0
        return round(100.0 * self.new_bytes / self.old_bytes, 1)

    @property
    def saved_kb(self) -> float:
        return round((self.old_bytes - self.new_bytes) / 1024.0, 1)

    @property
    def old_kb(self) -> float:
        return round(self.old_bytes / 1024.0, 1)

    @property
    def new_kb(self) -> float:
        return round(self.new_bytes / 1024.0, 1)


@dataclass
class BatchSettings:
    output_dir: Path | None = None
    preserve_structure: bool = True
    ask_overwrite: bool = True
    keep_dates: bool = True
    parallel: bool = True
    max_workers: int = 0
    open_folder_after: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


CONVERTED_FOLDER_NAME = "Przekonwertowane"


def _enum_val(obj) -> str:
    return obj.value if hasattr(obj, "value") else str(obj)


def job_to_dict(job: JobSpec) -> dict[str, Any]:
    fo = job.format_opts
    ro = job.resize
    tr = job.transforms
    md = job.metadata
    return {
        "input_path": str(job.input_path),
        "output_path": str(job.output_path),
        "output_format": job.output_format,
        "format_opts": {
            "quality": fo.quality,
            "lossless": fo.lossless,
            "progressive": fo.progressive,
            "optimize": fo.optimize,
            "keep_metadata": fo.keep_metadata,
            "subsampling": fo.subsampling,
            "target_kb": fo.target_kb,
            "target_tolerance": fo.target_tolerance,
            "png_max_colors": fo.png_max_colors,
            "png_colors_auto": fo.png_colors_auto,
            "png_mode": fo.png_mode,
            "jpeg_matte_mode": fo.jpeg_matte_mode,
            "jpeg_matte_color": fo.jpeg_matte_color,
            "jpeg_matte_color2": fo.jpeg_matte_color2,
            "jpeg_gradient_type": fo.jpeg_gradient_type,
            "jpeg_gradient_reverse": fo.jpeg_gradient_reverse,
            "jpeg_matte_noise": fo.jpeg_matte_noise,
            "gif_dither": fo.gif_dither,
            "gif_lossy": fo.gif_lossy,
            "gif_max_colors": fo.gif_max_colors,
            "gif_from_quality": fo.gif_from_quality,
            "gif_mode": fo.gif_mode,
            "gif_level": fo.gif_level,
            "gif_ultra_max_frames": fo.gif_ultra_max_frames,
            "gif_ultra_lossy": fo.gif_ultra_lossy,
        },
        "resize": {
            "mode": _enum_val(ro.mode),
            "width": ro.width,
            "height": ro.height,
            "percent": ro.percent,
            "side": ro.side,
            "dimension": ro.dimension,
            "box_w": ro.box_w,
            "box_h": ro.box_h,
            "smart_margin": ro.smart_margin,
            "preserve_aspect": ro.preserve_aspect,
            "skip_if_smaller": ro.skip_if_smaller,
            "filter_name": ro.filter_name,
            "scale_percent": ro.scale_percent,
            "min_longest_enabled": ro.min_longest_enabled,
            "min_longest_px": ro.min_longest_px,
        },
        "transforms": {
            "rotate": tr.rotate,
            "flip_h": tr.flip_h,
            "flip_v": tr.flip_v,
            "auto_rotate_exif": tr.auto_rotate_exif,
            "trim_transparent": tr.trim_transparent,
            "trim_margin": tr.trim_margin,
            "crop_x": tr.crop_x,
            "crop_y": tr.crop_y,
            "crop_w": tr.crop_w,
            "crop_h": tr.crop_h,
            "grayscale": tr.grayscale,
            "sepia": tr.sepia,
            "remove_background": tr.remove_background,
            "bg_model": tr.bg_model,
            "bg_alpha_matting": tr.bg_alpha_matting,
            "bg_post_process_mask": tr.bg_post_process_mask,
        },
        "metadata": {
            "keep_exif": md.keep_exif,
            "keep_iptc": md.keep_iptc,
            "strip_all": md.strip_all,
        },
    }


def job_from_dict(data: dict[str, Any]) -> JobSpec:
    fo = data.get("format_opts", {})
    ro = data.get("resize", {})
    tr = data.get("transforms", {})
    md = data.get("metadata", {})
    mode = ro.get("mode", "none")
    try:
        resize_mode = ResizeMode(mode)
    except ValueError:
        resize_mode = ResizeMode.NONE
    return JobSpec(
        input_path=Path(data["input_path"]),
        output_path=Path(data["output_path"]),
        output_format=data.get("output_format", "webp"),
        format_opts=FormatOptions(
            quality=int(fo.get("quality", DEFAULT_QUALITY)),
            lossless=bool(fo.get("lossless", False)),
            progressive=bool(fo.get("progressive", True)),
            optimize=bool(fo.get("optimize", True)),
            keep_metadata=bool(fo.get("keep_metadata", True)),
            subsampling=str(fo.get("subsampling", "medium")),
            target_kb=fo.get("target_kb"),
            target_tolerance=float(fo.get("target_tolerance", 0.2)),
            png_max_colors=int(fo.get("png_max_colors", 256)),
            png_colors_auto=bool(fo.get("png_colors_auto", True)),
            png_mode=str(fo.get("png_mode", "auto")),
            jpeg_matte_mode=str(fo.get("jpeg_matte_mode", "white")),
            jpeg_matte_color=str(fo.get("jpeg_matte_color", "#ffffff")),
            jpeg_matte_color2=str(fo.get("jpeg_matte_color2", "#000000")),
            jpeg_gradient_type=str(fo.get("jpeg_gradient_type", "linear")),
            jpeg_gradient_reverse=bool(fo.get("jpeg_gradient_reverse", False)),
            jpeg_matte_noise=bool(fo.get("jpeg_matte_noise", False)),
            gif_dither=bool(fo.get("gif_dither", True)),
            gif_lossy=int(fo.get("gif_lossy", 0)),
            gif_max_colors=int(fo.get("gif_max_colors", 256)),
            gif_from_quality=bool(fo.get("gif_from_quality", True)),
            gif_mode=str(fo.get("gif_mode", "quality")),
            gif_level=int(fo.get("gif_level", 6)),
            gif_ultra_max_frames=int(fo.get("gif_ultra_max_frames", 4)),
            gif_ultra_lossy=int(fo.get("gif_ultra_lossy", 70)),
        ),
        resize=ResizeOptions(
            mode=resize_mode,
            width=int(ro.get("width", 0)),
            height=int(ro.get("height", 0)),
            percent=float(ro.get("percent", 100.0)),
            side=str(ro.get("side", "width")),
            dimension=int(ro.get("dimension", 1800)),
            box_w=int(ro.get("box_w", 0)),
            box_h=int(ro.get("box_h", 0)),
            smart_margin=int(ro.get("smart_margin", 90)),
            preserve_aspect=bool(ro.get("preserve_aspect", True)),
            skip_if_smaller=bool(ro.get("skip_if_smaller", True)),
            filter_name=str(ro.get("filter_name", "lanczos3")),
            scale_percent=float(ro.get("scale_percent", 100.0)),
            min_longest_enabled=bool(ro.get("min_longest_enabled", True)),
            min_longest_px=int(ro.get("min_longest_px", 1080)),
        ),
        transforms=TransformOptions(
            rotate=int(tr.get("rotate", 0)),
            flip_h=bool(tr.get("flip_h", False)),
            flip_v=bool(tr.get("flip_v", False)),
            auto_rotate_exif=bool(tr.get("auto_rotate_exif", True)),
            trim_transparent=bool(tr.get("trim_transparent", False)),
            trim_margin=int(tr.get("trim_margin", 0)),
            crop_x=int(tr.get("crop_x", 0)),
            crop_y=int(tr.get("crop_y", 0)),
            crop_w=int(tr.get("crop_w", 0)),
            crop_h=int(tr.get("crop_h", 0)),
            grayscale=bool(tr.get("grayscale", False)),
            sepia=bool(tr.get("sepia", False)),
            remove_background=bool(tr.get("remove_background", False)),
            bg_model=str(tr.get("bg_model", "birefnet-general")),
            bg_alpha_matting=bool(tr.get("bg_alpha_matting", True)),
            bg_post_process_mask=bool(tr.get("bg_post_process_mask", True)),
        ),
        metadata=MetadataPolicy(
            keep_exif=bool(md.get("keep_exif", True)),
            keep_iptc=bool(md.get("keep_iptc", True)),
            strip_all=bool(md.get("strip_all", False)),
        ),
    )
