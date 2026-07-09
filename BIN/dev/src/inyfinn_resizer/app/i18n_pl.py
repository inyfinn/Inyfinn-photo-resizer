"""Polskie etykiety interfejsu."""

from __future__ import annotations

from inyfinn_resizer.core.formats.registry import OUTPUT_FORMATS

FORMAT_LABEL_PL: dict[str, str] = {
    "jpeg": "JPEG (*.jpg)",
    "png": "PNG (*.png)",
    "gif": "GIF (*.gif)",
    "bmp": "BMP (*.bmp)",
    "tiff": "TIFF (*.tif)",
    "webp": "WebP (*.webp)",
    "avif": "AVIF (*.avif)",
    "heic": "HEIC (*.heic)",
    "jp2": "JPEG2000 (*.jp2)",
    "pdf": "PDF (*.pdf)",
}


def format_labels_pl() -> list[str]:
    return [FORMAT_LABEL_PL.get(k, meta["label"]) for k, meta in OUTPUT_FORMATS.items()]


def format_to_label_pl(fmt: str) -> str:
    return FORMAT_LABEL_PL.get(fmt.lower(), FORMAT_LABEL_PL["webp"])


def label_to_format_pl(label: str) -> str:
    for key, pl_label in FORMAT_LABEL_PL.items():
        if pl_label == label:
            return key
    for key, meta in OUTPUT_FORMATS.items():
        if meta["label"] == label:
            return key
    return "webp"
