"""Presety sieci handlowych — format, wymiary, tło (na podstawie wytycznych dostawców)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions
from inyfinn_resizer.core.size_presets import (
    PRESET_BOX_1200,
    PRESET_BOX_1920,
    PRESET_BOX_2000,
    PRESET_BOX_2500,
    PRESET_BOX_3000,
    PRESET_LONG_1200,
    PRESET_LONG_2400,
    PRESET_ORIGINAL,
    apply_size_preset,
)

RETAIL_NONE = "retail:none"


def canonical_output_format(fmt: str) -> str:
    """Klucz formatu zgodny z FormatMultiCombo (jpeg, nie jpg)."""
    key = fmt.lower().strip()
    if key in ("jpg", "jpeg"):
        return "jpeg"
    return key


def infer_output_format(*, remove_background: bool, explicit: str | None = None) -> str:
    """Gdy specyfikacja nie podaje rozszerzenia: tło → JPEG, bez tła → PNG + usuń tło."""
    if explicit:
        return canonical_output_format(explicit)
    return "png" if remove_background else "jpeg"


@dataclass(frozen=True)
class RetailPreset:
    id: str
    label: str
    tooltip: str
    source: str
    output_format: str
    quality: int
    size_preset: str
    remove_background: bool
    bg_model: str = "birefnet-general"
    min_longest_enabled: bool = False
    min_longest_px: int = 1200
    scale_percent: float = 100.0
    png_colors_auto: bool = True
    png_max_colors: int = 256
    jpeg_matte_mode: str = "white"
    segregate: bool = False
    wiz_sequence: bool = False
    output_enabled: bool = False
    preserve_structure: bool = True
    keep_dates: bool = True
    overwrite_prompt: bool = True
    parallel: bool = True


RETAIL_PRESETS: list[RetailPreset] = [
    RetailPreset(
        id="aldi_cms",
        label="ALDI — sklep online",
        tooltip=(
            "PNG 1920×1920 px, produkt bez tła, max ~2 MB. "
            "Źródło: ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf (format CMS online)."
        ),
        source="ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf",
        output_format="png",
        quality=82,
        size_preset=PRESET_BOX_1920,
        remove_background=True,
    ),
    RetailPreset(
        id="aldi_print",
        label="ALDI — druk",
        tooltip=(
            "JPEG najwyższa jakość, min. 20 cm przy 300 dpi (~2400 px najdłuższej krawędzi). "
            "Źródło: ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf (format do druku)."
        ),
        source="ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf",
        output_format="jpeg",
        quality=95,
        size_preset=PRESET_LONG_2400,
        remove_background=False,
        jpeg_matte_mode="white",
    ),
    RetailPreset(
        id="dm",
        label="dm.pl",
        tooltip=(
            "PNG lub JPEG ze ścieżką — tu: PNG 2000×2000 px, tło przezroczyste, max 5 MB, 300 dpi. "
            "Źródło: dm-pl-Wytyczne dla plików multimedialnych lipiec 2024.pdf."
        ),
        source="dm-pl-Wytyczne dla plików multimedialnych lipiec 2024.pdf",
        output_format="png",
        quality=88,
        size_preset=PRESET_BOX_2000,
        remove_background=True,
    ),
    RetailPreset(
        id="rossmann",
        label="Rossmann",
        tooltip=(
            "PNG lub WebP, produkt bez tła, min. 1200 px, max 2500 px, max 5 MB. "
            "Źródło: Rossmann_Zdjęcia - nowa specyfikacja dla dostawców.pdf."
        ),
        source="Rossmann_Zdjęcia - nowa specyfikacja dla dostawców.pdf",
        output_format="webp",
        quality=84,
        size_preset=PRESET_BOX_2500,
        remove_background=True,
        min_longest_enabled=True,
        min_longest_px=1200,
    ),
    RetailPreset(
        id="lidl",
        label="Lidl — białe tło",
        tooltip=(
            "Zdjęcie na białym tle, dobra jakość, bez usuwania tła. "
            "Źródło: Lidl_INSTRUKCJA ROBIENIA ZDJĘĆ ARTYKUŁÓW_akceptacja kartonów.pdf."
        ),
        source="Lidl_INSTRUKCJA ROBIENIA ZDJĘĆ ARTYKUŁÓW_akceptacja kartonów.pdf",
        output_format="jpeg",
        quality=92,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,
        jpeg_matte_mode="white",
    ),
    RetailPreset(
        id="amazon_allegro",
        label="Amazon / Allegro",
        tooltip=(
            "PNG bez tła, 1200×1200 px (fallback gdy brak renderów 10000 px). "
            "Źródło: MOKATE_amazon-allegro.docx."
        ),
        source="MOKATE_amazon-allegro.docx",
        output_format="png",
        quality=90,
        size_preset=PRESET_BOX_1200,
        remove_background=True,
    ),
    RetailPreset(
        id="amazon_main",
        label="Amazon — zdjęcie główne",
        tooltip=(
            "JPEG min. 3000×3000 px, tło białe RGB 255,255,255. "
            "Źródło: eCommerce Listing Guidelines Best Practices - Nutripharm - March24.pptx."
        ),
        source="eCommerce Listing Guidelines Best Practices - Nutripharm - March24.pptx",
        output_format="jpeg",
        quality=92,
        size_preset=PRESET_BOX_3000,
        remove_background=False,
        jpeg_matte_mode="white",
    ),
    RetailPreset(
        id="auchan",
        label="Auchan — ogólny",
        tooltip=(
            "JPEG 1200 px najdłuższej krawędzi, białe tło — preset ogólny "
            "(brak szczegółowych wymiarów w Auchan_zakładka instrukcja.xlsx)."
        ),
        source="Auchan_zakładka instrukcja.xlsx",
        output_format="jpeg",
        quality=90,
        size_preset=PRESET_LONG_1200,
        remove_background=False,
        jpeg_matte_mode="white",
    ),
]


def retail_preset_by_id(preset_id: str) -> RetailPreset | None:
    for preset in RETAIL_PRESETS:
        if preset.id == preset_id:
            return preset
    return None


def retail_snapshot_from_preset(preset: RetailPreset) -> dict:
    """Pełny, niezmienny stan UI dla presetu sieci."""
    fmt = infer_output_format(
        remove_background=preset.remove_background,
        explicit=preset.output_format,
    )
    resize, transforms = apply_size_preset(preset.size_preset)
    resize = replace_resize_from_preset(resize, preset)
    transforms = replace_transforms_from_preset(transforms, preset)
    format_opts = FormatOptions(
        quality=preset.quality,
        png_colors_auto=preset.png_colors_auto,
        png_max_colors=preset.png_max_colors,
        jpeg_matte_mode=preset.jpeg_matte_mode,
    )
    return {
        "retail_id": preset.id,
        "output_format": fmt,
        "formats": [fmt],
        "quality": preset.quality,
        "size_preset": preset.size_preset,
        "remove_background": preset.remove_background,
        "bg_model": preset.bg_model,
        "min_longest_enabled": preset.min_longest_enabled,
        "min_longest_px": preset.min_longest_px,
        "scale_percent": preset.scale_percent,
        "png_colors_auto": preset.png_colors_auto,
        "png_max_colors": preset.png_max_colors,
        "jpeg_matte_mode": preset.jpeg_matte_mode,
        "segregate": preset.segregate,
        "wiz_sequence": preset.wiz_sequence,
        "output_enabled": preset.output_enabled,
        "preserve_structure": preset.preserve_structure,
        "keep_dates": preset.keep_dates,
        "overwrite_prompt": preset.overwrite_prompt,
        "parallel": preset.parallel,
        "format_opts": format_opts,
        "resize": resize,
        "transforms": transforms,
    }


def replace_resize_from_preset(resize: ResizeOptions, preset: RetailPreset) -> ResizeOptions:
    return replace(
        resize,
        scale_percent=preset.scale_percent,
        min_longest_enabled=preset.min_longest_enabled,
        min_longest_px=preset.min_longest_px,
    )


def replace_transforms_from_preset(transforms: TransformOptions, preset: RetailPreset) -> TransformOptions:
    return replace(
        transforms,
        remove_background=preset.remove_background,
        bg_model=preset.bg_model,
    )


def default_format_opts_for_retail(preset: RetailPreset) -> FormatOptions:
    return FormatOptions(
        quality=preset.quality,
        png_colors_auto=preset.png_colors_auto,
        png_max_colors=preset.png_max_colors,
        jpeg_matte_mode=preset.jpeg_matte_mode,
    )
