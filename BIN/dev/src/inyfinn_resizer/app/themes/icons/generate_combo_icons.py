"""Generuje strzałki rozwijane listy dla QComboBox."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent


def _draw_chevron(path: Path, color: tuple[int, int, int, int]) -> None:
    img = Image.new("RGBA", (14, 14), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(3, 5), (11, 5), (7, 10)], fill=color)
    img.save(path)


def main() -> None:
    _draw_chevron(OUT / "combo-down-light.png", (2, 132, 199, 255))
    _draw_chevron(OUT / "combo-down-dark.png", (125, 211, 252, 255))
    print("OK", OUT)


if __name__ == "__main__":
    main()
