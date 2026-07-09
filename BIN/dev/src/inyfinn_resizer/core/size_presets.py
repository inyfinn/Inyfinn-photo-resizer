"""Presety wymiarów obrazu (Format w UI)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from PySide6.QtCore import QSettings

from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions

PRESET_ORIGINAL = "original"
PRESET_LONG_1200 = "long_1200"
PRESET_SHORT_1200 = "short_1200"
PRESET_CROP_1200x848 = "crop_1200x848"
PRESET_BOX_1200 = "box_1200"
PRESET_SAVE_CUSTOM = "__save_custom__"
PRESET_CUSTOM_PREFIX = "custom:"

BUILTIN_PRESETS: list[tuple[str, str]] = [
    ("Oryginalny", PRESET_ORIGINAL),
    ("1200 px najdłuższej krawędzi", PRESET_LONG_1200),
    ("1200 px najkrótszej krawędzi", PRESET_SHORT_1200),
    ("1200×848 — inteligentny crop", PRESET_CROP_1200x848),
    ("1200×1200", PRESET_BOX_1200),
]

PRESET_TOOLTIPS: dict[str, str] = {
    PRESET_ORIGINAL: "Bez zmiany rozmiaru — zapis w oryginalnych wymiarach.",
    PRESET_LONG_1200: (
        "Najdłuższa krawędź (szerokość lub wysokość) = 1200 px. Proporcje zachowane.\n"
        "Przykład: 3000×2000 → 1200×800 (3000÷1,5=1200, 2000÷1,5=800)."
    ),
    PRESET_SHORT_1200: (
        "Najkrótsza krawędź = 1200 px. Proporcje zachowane.\n"
        "Przykład: 3000×2000 → 1800×1200 (1200×1,5=1800)."
    ),
    PRESET_CROP_1200x848: "Inteligentny przycięty kadr 1200×848 px (jak baner produktowy).",
    PRESET_BOX_1200: "Dopasowanie do kwadratu 1200×1200 px (cover, proporcje zachowane).",
}


def _settings() -> QSettings:
    return QSettings("Inyfinn", "PhotoResizer")


def load_custom_presets() -> list[tuple[str, str, dict[str, Any]]]:
    raw = _settings().value("size_presets/custom", "[]")
    if isinstance(raw, list):
        data = raw
    else:
        try:
            data = json.loads(str(raw))
        except (json.JSONDecodeError, TypeError):
            data = []
    out: list[tuple[str, str, dict[str, Any]]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id", ""))
        name = str(item.get("name", pid))
        if pid:
            out.append((name, f"{PRESET_CUSTOM_PREFIX}{pid}", item))
    return out


def is_custom_preset(preset_id: str) -> bool:
    return preset_id.startswith(PRESET_CUSTOM_PREFIX)


def delete_custom_preset(preset_id: str) -> bool:
    if not is_custom_preset(preset_id):
        return False
    raw_id = preset_id[len(PRESET_CUSTOM_PREFIX) :]
    raw = _settings().value("size_presets/custom", "[]")
    try:
        customs = json.loads(str(raw)) if not isinstance(raw, list) else list(raw)
    except (json.JSONDecodeError, TypeError):
        return False
    new_list = [item for item in customs if str(item.get("id", "")) != raw_id]
    if len(new_list) == len(customs):
        return False
    _settings().setValue("size_presets/custom", json.dumps(new_list, ensure_ascii=False))
    return True


def save_custom_preset(name: str, resize: ResizeOptions, transforms: TransformOptions) -> str:
    import uuid

    pid = uuid.uuid4().hex[:8]
    entry = {
        "id": pid,
        "name": name.strip() or f"Własny {pid}",
        "resize": {**asdict(resize), "mode": resize.mode.value},
        "transforms": asdict(transforms),
    }
    customs = []
    raw = _settings().value("size_presets/custom", "[]")
    try:
        customs = json.loads(str(raw)) if not isinstance(raw, list) else list(raw)
    except (json.JSONDecodeError, TypeError):
        customs = []
    customs.append(entry)
    _settings().setValue("size_presets/custom", json.dumps(customs, ensure_ascii=False))
    return f"{PRESET_CUSTOM_PREFIX}{pid}"


def _resize_from_dict(data: dict[str, Any]) -> ResizeOptions:
    mode = data.get("mode", ResizeMode.NONE.value)
    if hasattr(mode, "value"):
        mode = mode.value
    payload = {k: v for k, v in data.items() if k != "mode"}
    return ResizeOptions(mode=ResizeMode(mode), **payload)


def apply_size_preset(
    preset_id: str,
    *,
    custom_payload: dict[str, Any] | None = None,
) -> tuple[ResizeOptions, TransformOptions]:
    if preset_id == PRESET_ORIGINAL:
        return ResizeOptions(), TransformOptions()

    if preset_id == PRESET_LONG_1200:
        return (
            ResizeOptions(mode=ResizeMode.ONE_SIDE, side="longer", dimension=1200),
            TransformOptions(),
        )

    if preset_id == PRESET_SHORT_1200:
        return (
            ResizeOptions(mode=ResizeMode.ONE_SIDE, side="shorter", dimension=1200),
            TransformOptions(),
        )

    if preset_id == PRESET_CROP_1200x848:
        return (
            ResizeOptions(
                mode=ResizeMode.CROP_SMART,
                box_w=1200,
                box_h=848,
                smart_margin=90,
            ),
            TransformOptions(),
        )

    if preset_id == PRESET_BOX_1200:
        return (
            ResizeOptions(mode=ResizeMode.FIT_BOX, box_w=1200, box_h=1200),
            TransformOptions(),
        )

    if preset_id.startswith(PRESET_CUSTOM_PREFIX) and custom_payload:
        resize = _resize_from_dict(custom_payload.get("resize", {}))
        tr = custom_payload.get("transforms", {})
        return resize, TransformOptions(**tr) if tr else TransformOptions()

    return ResizeOptions(), TransformOptions()


def preset_summary(resize: ResizeOptions) -> str:
    if resize.mode == ResizeMode.NONE:
        return "oryginał"
    if resize.mode == ResizeMode.ONE_SIDE and resize.side == "longer":
        return f"{resize.dimension}px najdł. bok"
    if resize.mode == ResizeMode.ONE_SIDE and resize.side == "shorter":
        return f"{resize.dimension}px najkr. bok"
    if resize.mode == ResizeMode.CROP_SMART:
        return f"crop {resize.box_w}×{resize.box_h}"
    if resize.mode == ResizeMode.FIT_BOX:
        return f"{resize.box_w}×{resize.box_h}"
    if resize.mode == ResizeMode.ONE_SIDE:
        side = {"width": "szer.", "height": "wys.", "longer": "dł.", "shorter": "kr."}.get(
            resize.side, resize.side
        )
        return f"{resize.dimension}px ({side})"
    if resize.mode == ResizeMode.MAX_DIMENSION:
        return f"maks. {resize.dimension}px"
    if resize.mode == ResizeMode.PERCENT:
        return f"{int(resize.percent)}%"
    return "własny"
