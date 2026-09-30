"""Generuje strzałki rozwijanej listy dla QComboBox — po jednej na motyw Dobra Kaloria.

Kolor = color_text_muted (palettes.py). Plik: combo-down-<styl>-<tryb>.png.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from inyfinn_resizer.app.themes.palettes import ROLES

OUT = Path(__file__).resolve().parent


def _draw_chevron(path: Path, color: tuple[int, int, int, int]) -> None:
    img = Image.new("RGBA", (14, 14), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(3, 5), (11, 5), (7, 10)], fill=color)
    img.save(path)


def main() -> None:
    for name, roles in ROLES.items():
        _draw_chevron(OUT / f"combo-down-{name}.png", ImageColor.getrgb(roles["color_text_muted"]) + (255,))
    print("OK", OUT)


if __name__ == "__main__":
    main()
