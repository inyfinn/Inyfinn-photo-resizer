"""Input/output format registry."""

from __future__ import annotations

INPUT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".pcx", ".tga",
    ".wmf", ".emf", ".ico", ".cur", ".ppm", ".heic", ".heif", ".webp", ".avif",
    ".jp2", ".j2k", ".jxl", ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2",
}

OUTPUT_FORMATS = {
    "jpeg": {"ext": ".jpg", "label": "JPEG Format (*.jpg)", "lossy": True},
    "png": {"ext": ".png", "label": "PNG Format (*.png)", "lossy": False},
    "gif": {"ext": ".gif", "label": "GIF Format (*.gif)", "lossy": True},
    "bmp": {"ext": ".bmp", "label": "BMP Format (*.bmp)", "lossy": False},
    "tiff": {"ext": ".tif", "label": "TIFF Format (*.tif)", "lossy": False},
    "webp": {"ext": ".webp", "label": "WebP Format (*.webp)", "lossy": True},
    "avif": {"ext": ".avif", "label": "AVIF Format (*.avif)", "lossy": True},
    "heic": {"ext": ".heic", "label": "HEIC Format (*.heic)", "lossy": True},
    "jp2": {"ext": ".jp2", "label": "JPEG2000 (*.jp2)", "lossy": True},
    "pdf": {"ext": ".pdf", "label": "PDF (*.pdf)", "lossy": False},
}

IMAGE_FILTER = "Images (*.jpg *.jpeg *.png *.gif *.bmp *.tif *.tiff *.webp *.avif *.heic);;All (*.*)"


def is_image_file(path) -> bool:
    from pathlib import Path
    p = Path(path)
    return p.suffix.lower() in INPUT_EXTENSIONS or p.suffix.lower() in {v["ext"] for v in OUTPUT_FORMATS.values()}


def output_extension(fmt: str) -> str:
    return OUTPUT_FORMATS.get(fmt.lower(), OUTPUT_FORMATS["webp"])["ext"]


def format_labels() -> list[str]:
    return [v["label"] for v in OUTPUT_FORMATS.values()]


def label_to_format(label: str) -> str:
    for key, meta in OUTPUT_FORMATS.items():
        if meta["label"] == label:
            return key
    return "webp"


def format_to_label(fmt: str) -> str:
    return OUTPUT_FORMATS.get(fmt.lower(), OUTPUT_FORMATS["webp"])["label"]


def output_format_for_input(path) -> str:
    """Format wyjściowy dopasowany do rozszerzenia pliku wejściowego."""
    from pathlib import Path

    ext = Path(path).suffix.lower()
    mapping = {
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
        ".png": "png",
        ".gif": "gif",
        ".webp": "webp",
        ".avif": "avif",
        ".tif": "tiff",
        ".tiff": "tiff",
        ".bmp": "bmp",
        ".heic": "heic",
        ".heif": "heic",
        ".jp2": "jp2",
    }
    return mapping.get(ext, "jpeg")
