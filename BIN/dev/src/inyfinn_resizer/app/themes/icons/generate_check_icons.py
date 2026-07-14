"""Generuje ikony checkmark dla QSS checkboxów (global + sekcje kroków)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent

SECTION_ACCENTS = {
    "check-section1": (99, 102, 241),
    "check-section2": (13, 148, 136),
    "check-section3": (234, 88, 12),
}


def _draw_check(path: Path, bg: tuple[int, int, int], fg: tuple[int, int, int]) -> None:
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((1, 1, 18, 18), radius=5, fill=bg)
    draw.line((5, 10, 8, 14), fill=fg, width=2)
    draw.line((8, 14, 15, 6), fill=fg, width=2)
    img.save(path)


def main() -> None:
    _draw_check(OUT / "check-light.png", (14, 165, 233), (255, 255, 255))
    _draw_check(OUT / "check-dark.png", (129, 140, 248), (15, 23, 42))
    for name, rgb in SECTION_ACCENTS.items():
        _draw_check(OUT / f"{name}.png", rgb, (255, 255, 255))
    print("OK", OUT)


if __name__ == "__main__":
    main()
