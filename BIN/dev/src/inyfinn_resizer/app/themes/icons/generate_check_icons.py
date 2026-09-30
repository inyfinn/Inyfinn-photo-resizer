"""Generuje ikony checkmark dla QSS checkboxów — po jednej na motyw Dobra Kaloria.

Tło = color_brand, znak = color_on_brand (palettes.py). Plik: check-<styl>-<tryb>.png.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from inyfinn_resizer.app.themes.palettes import ROLES

OUT = Path(__file__).resolve().parent


def _draw_check(path: Path, bg: tuple[int, int, int], fg: tuple[int, int, int]) -> None:
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((1, 1, 18, 18), radius=4, fill=bg)
    draw.line((5, 10, 8, 14), fill=fg, width=2)
    draw.line((8, 14, 15, 6), fill=fg, width=2)
    img.save(path)


def main() -> None:
    for name, roles in ROLES.items():
        _draw_check(
            OUT / f"check-{name}.png",
            ImageColor.getrgb(roles["color_brand"]),
            ImageColor.getrgb(roles["color_on_brand"]),
        )
    print("OK", OUT)


if __name__ == "__main__":
    main()
