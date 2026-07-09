"""JSON preset load/save."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QStandardPaths

from inyfinn_resizer.core.job import (
    BatchSettings,
    FormatOptions,
    MetadataPolicy,
    RenameRule,
    ResizeMode,
    ResizeOptions,
    TransformOptions,
)


def _enum_val(v):
    return v.value if hasattr(v, "value") else v


def settings_to_dict(
    output_format: str,
    format_opts: FormatOptions,
    resize: ResizeOptions,
    transforms: TransformOptions,
    metadata: MetadataPolicy,
    rename: RenameRule,
    batch: BatchSettings | None = None,
) -> dict[str, Any]:
    return {
        "version": 1,
        "output_format": output_format,
        "format_opts": asdict(format_opts),
        "resize": {**asdict(resize), "mode": _enum_val(resize.mode)},
        "transforms": asdict(transforms),
        "metadata": asdict(metadata),
        "rename": asdict(rename),
        "batch": asdict(batch) if batch else {},
    }


def load_preset(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_preset(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


MAX_AUTO_PROFILES = 10


def auto_profiles_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base) / "profiles"


def auto_save_profile_rotating(data: dict[str, Any], *, max_files: int = MAX_AUTO_PROFILES) -> Path:
    """Zapisuje profil JSON i usuwa najstarsze, gdy jest ich więcej niż max_files."""
    folder = auto_profiles_dir()
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = folder / f"auto-{stamp}.json"
    save_preset(path, data)
    files = sorted(folder.glob("auto-*.json"), key=lambda p: p.stat().st_mtime)
    while len(files) > max_files:
        files[0].unlink(missing_ok=True)
        files = files[1:]
    return path


def apply_preset(data: dict[str, Any]) -> dict[str, Any]:
    resize = data.get("resize", {})
    if "mode" in resize:
        resize["mode"] = ResizeMode(resize["mode"])
    return {
        "output_format": data.get("output_format", "webp"),
        "format_opts": FormatOptions(**data.get("format_opts", {})),
        "resize": ResizeOptions(**resize) if resize else ResizeOptions(),
        "transforms": TransformOptions(**data.get("transforms", {})),
        "metadata": MetadataPolicy(**data.get("metadata", {})),
        "rename": RenameRule(**data.get("rename", {})),
    }
