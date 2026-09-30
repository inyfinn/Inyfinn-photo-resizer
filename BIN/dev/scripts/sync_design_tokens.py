"""Kopiuje kolory design systemu Dobra Kaloria (tokens_qt.py) do app/themes/palettes.py.

    python scripts/sync_design_tokens.py [ścieżka do tokens_qt.py]

Domyślnie: ~/.claude/skills/ds-dobra-kaloria/tokens/tokens_qt.py. Plik design systemu jest tylko czytany.
palettes.py jest nadpisywany w całości — nie edytuj go ręcznie, zmień tokens.json design systemu.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "inyfinn_resizer" / "app" / "themes" / "palettes.py"
DEFAULT_SRC = Path.home() / ".claude" / "skills" / "ds-dobra-kaloria" / "tokens" / "tokens_qt.py"

# motyw Resizera → wariant design systemu (tokens_qt.VARIANTS)
THEME_VARIANTS = {
    "zielen-jasny": "zielen-jasny",
    "zielen-ciemny": "zielen-ciemny",
    "krem-jasny": "krem-jasny",
    "krem-ciemny": "krem-ciemny",
}
ROLE_KEYS = (
    "color_text", "color_text_muted", "color_label", "color_bg", "color_surface", "color_surface_hover",
    "color_border", "color_border_strong", "color_field_border", "color_brand", "color_brand_hover",
    "color_brand_soft", "color_brand_soft_strong", "color_on_brand", "color_cta", "color_cta_hover",
    "color_on_cta", "color_disabled_bg", "color_switch_off", "color_danger", "color_danger_soft",
    "color_warning_text", "color_warning_border", "color_warning_bg", "color_inverse_bg",
    "color_on_inverse", "color_focus",
)
LEVELS = 5
TAGS = 8


def _load(src: Path):
    spec = importlib.util.spec_from_file_location("dk_tokens_qt", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _version(src: Path) -> str:
    first = src.read_text(encoding="utf-8").splitlines()[:3]
    for line in first:
        if "Tokeny Dobra Kaloria" in line:
            return line.split("Tokeny Dobra Kaloria", 1)[1].split()[0]
    return "?"


def render(src: Path) -> str:
    mod = _load(src)
    version = _version(src)
    variants = mod.VARIANTS
    lines = [
        "# -*- coding: utf-8 -*-",
        f'"""Kolory design systemu Dobra Kaloria {version} (skill ds-dobra-kaloria, tokens/tokens_qt.py).',
        "",
        "PLIK GENEROWANY: python scripts/sync_design_tokens.py — nie edytuj ręcznie. Zmiana koloru = zmiana",
        "w tokens.json design systemu, build_tokens.py, potem ponowne uruchomienie skryptu.",
        "Kontrast par tekst/tło i tagów sprawdza generator design systemu.",
        "",
        "ROLES  — role kolorów (tekst, akcent, CTA, ramki…).",
        "LADDER — drabina powierzchni L0…L4: surface_<n> (tło poziomu), border_subtle_<n> (ramka poziomu).",
        "         Jasny: głębiej = ciemniej. Ciemny: głębiej = jaśniej.",
        "TAGS   — 8 tagów (tło, ramka, tekst): odcień stylu z przesunięciem barwy (hue) o ±12°, ±24°…",
        '"""',
        "",
        "ROLES: dict[str, dict[str, str]] = {",
    ]
    for theme, variant in THEME_VARIANTS.items():
        t = variants[variant]
        lines.append(f'    "{theme}": {{  # {variant}')
        for key in ROLE_KEYS:
            lines.append(f'        "{key}": "{t[key].upper()}",')
        lines.append("    },")
    lines += ["}", "", "LADDER: dict[str, dict[str, str]] = {"]
    for theme, variant in THEME_VARIANTS.items():
        t = variants[variant]
        lines.append(f'    "{theme}": {{')
        for n in range(LEVELS):
            lines.append(f'        "surface_{n}": "{t[f"color_surface_{n}"].upper()}",')
        for n in range(LEVELS):
            lines.append(f'        "border_subtle_{n}": "{t[f"color_border_subtle_{n}"].upper()}",')
        lines.append("    },")
    lines += ["}", "", "# (tło, ramka, tekst) tagów 1..8", "TAGS: dict[str, list[tuple[str, str, str]]] = {"]
    for theme, variant in THEME_VARIANTS.items():
        t = variants[variant]
        lines.append(f'    "{theme}": [')
        for n in range(1, TAGS + 1):
            bg, border, fg = (t[f"color_tag_{n}_{part}"].upper() for part in ("bg", "border", "fg"))
            lines.append(f'        ("{bg}", "{border}", "{fg}"),')
        lines.append("    ],")
    lines += ["}", ""]
    return "\n".join(lines)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.is_file():
        print(f"Brak pliku tokenów: {src}", file=sys.stderr)
        return 1
    text = render(src)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Zapisano {OUT} ({len(text)} znaków) z {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
