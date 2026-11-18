"""Presety sieci handlowych — format, wymiary, tło (na podstawie wytycznych dostawców)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions
from inyfinn_resizer.core.size_presets import (
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
    # Eksport wg specyfikacji (core/retail_export.py); 0 = bez limitu.
    trim_to_content: bool = False
    alpha_floor: int = 8  # alfa poniżej progu = tło (mgiełka widoczna w trybie ciemnym sklepu)
    min_shortest_px: int = 0
    max_longest_px: int = 0
    max_file_mb: float = 0.0
    canvas_px: int = 0  # kwadrat N×N px: cały produkt wyśrodkowany, dopełnienie przezroczyste (PNG) / białe (JPG)
    dpi: int = 0
    naming: str = ""  # "ean_role" = <EAN>_<rola>.png (core/ean.py)


RETAIL_PRESETS: list[RetailPreset] = [
    RetailPreset(
        id="aldi_cms",
        label="ALDI — sklep online",
        tooltip=(
            "PNG 1920×1920 px, cały produkt na środku, tło przezroczyste, max ~2 MB. "
            "Źródło: ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf (format CMS online)."
        ),
        source="ALDI_Wymagania dotyczące zdjęć 2025.08.18.pdf",
        output_format="png",
        quality=82,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,  # tło usuwa retail_export tylko, gdy plik nie ma przezroczystości
        # cały produkt w kadrze: kadr do treści, potem wyśrodkowany na kwadracie (nigdy obcięty)
        trim_to_content=True,
        canvas_px=1920,
        max_file_mb=2.0,
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
            "PNG 2000×2000 px, cały produkt na środku, tło przezroczyste, max 5 MB, 300 dpi. "
            "Źródło: dm-pl-Wytyczne dla plików multimedialnych lipiec 2024.pdf."
        ),
        source="dm-pl-Wytyczne dla plików multimedialnych lipiec 2024.pdf",
        output_format="png",
        quality=88,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,
        # cały produkt w kadrze: kadr do treści, potem wyśrodkowany na kwadracie (nigdy obcięty)
        trim_to_content=True,
        canvas_px=2000,
        max_file_mb=5.0,
        dpi=300,
    ),
    RetailPreset(
        id="rossmann",
        label="Rossmann",
        tooltip=(
            "PNG bez tła, kadr do krawędzi produktu, krótszy bok min. 1200 px, dłuższy max 3800 px, "
            "max 5 MB, nazwy EAN_g / EAN_t. "
            "Źródło: Rossmann specyfikacja techniczna zdjęcia (2026)."
        ),
        source="Rossmann specyfikacja techniczna zdjęcia (2026).pdf",
        output_format="png",
        quality=90,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,  # tło usuwa retail_export tylko, gdy plik nie ma przezroczystości
        trim_to_content=True,
        min_shortest_px=1200,
        max_longest_px=3800,
        max_file_mb=5.0,
        dpi=72,
        naming="ean_role",
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
            "PNG bez tła, 1200×1200 px, cały produkt na środku (fallback gdy brak renderów 10000 px). "
            "Źródło: MOKATE_amazon-allegro.docx."
        ),
        source="MOKATE_amazon-allegro.docx",
        output_format="png",
        quality=90,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,
        # cały produkt w kadrze: kadr do treści, potem wyśrodkowany na kwadracie (nigdy obcięty)
        trim_to_content=True,
        canvas_px=1200,
    ),
    RetailPreset(
        id="amazon_main",
        label="Amazon — zdjęcie główne",
        tooltip=(
            "JPEG 3000×3000 px, cały produkt na środku, tło białe RGB 255,255,255. "
            "Źródło: eCommerce Listing Guidelines Best Practices - Nutripharm - March24.pptx."
        ),
        source="eCommerce Listing Guidelines Best Practices - Nutripharm - March24.pptx",
        output_format="jpeg",
        quality=92,
        size_preset=PRESET_ORIGINAL,
        remove_background=False,
        jpeg_matte_mode="white",
        # cały produkt w kadrze: kadr do treści, potem wyśrodkowany na kwadracie (nigdy obcięty)
        trim_to_content=True,
        canvas_px=3000,
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

SCHEMA_VERSION = 1


def presets_json() -> dict:
    """Jedno źródło presetów dla innych programów (skrypty JSX Photoshopa): presety, role zdjęć, wzorzec nazwy."""
    from dataclasses import asdict

    from inyfinn_resizer import __version__
    from inyfinn_resizer.core.ean import NAME_PATTERNS, ROLE_LABELS, ROLE_WORDS

    presets = []
    for p in RETAIL_PRESETS:
        resize, _ = apply_size_preset(p.size_preset)
        presets.append({
            **asdict(p),
            "resize": {k: getattr(v, "value", v) for k, v in asdict(resize).items()},
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "app_version": __version__,
        "generated_from": "inyfinn_resizer/core/retail_presets.py",
        "naming": NAME_PATTERNS,
        "roles": [
            {"role": role, "label": ROLE_LABELS[role], "words": list(words)} for words, role in ROLE_WORDS
        ],
        "role_labels": ROLE_LABELS,
        "presets": presets,
    }


def write_presets_json(path) -> None:
    import json
    from pathlib import Path

    Path(path).write_text(json.dumps(presets_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3 or sys.argv[1] != "--json":
        raise SystemExit("Użycie: python -m inyfinn_resizer.core.retail_presets --json <plik.json>")
    write_presets_json(sys.argv[2])
    print(f"Zapisano {sys.argv[2]}")
