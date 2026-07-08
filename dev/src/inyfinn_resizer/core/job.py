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


@dataclass
class ResizeOptions:
    mode: ResizeMode = ResizeMode.NONE
    width: int = 0
    height: int = 0
    percent: float = 100.0
    side: str = "width"  # width | height | longer | shorter
    dimension: int = 1800
    preserve_aspect: bool = True
    skip_if_smaller: bool = True
    filter_name: str = "lanczos3"


@dataclass
class TransformOptions:
    rotate: int = 0
    flip_h: bool = False
    flip_v: bool = False
    auto_rotate_exif: bool = True
    crop_x: int = 0
    crop_y: int = 0
    crop_w: int = 0
    crop_h: int = 0
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    grayscale: bool = False
    sepia: bool = False


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


@dataclass
class FormatOptions:
    quality: int = 85
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
