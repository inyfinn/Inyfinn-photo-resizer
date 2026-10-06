"""Generuje obrazy pól wyboru (checkbox, radio) — po jednym pliku na stan i motyw.

Reguły G1 i S8 (DS 2.0): wnętrze jasne zawsze (także zaznaczone), obrys 1,5 px, znak (ptaszek / kropka) w kolorze
check_mark; zaznaczone ma obrys w kolorze znaku. QSS nie umie obrysu 1,5 px (rysuje 1 albo 2 px), więc cały wskaźnik jest obrazem 80×80 (4× rozmiaru
20 px): Qt zmniejsza go do 20 px (albo 25 px przy skali 125 %) wygładzonym skalowaniem, a w QSS zostaje
``border: none``. Obraz rysujemy w 16× i zmniejszamy (antyaliasing, PIL nie wygładza krawędzi sam).

Pliki: ``cb-<styl>-<tryb>-<stan>.png`` (kwadrat, promień 4 px) i ``rb-…`` (koło), stany z
``themes.CHECK_STATES``. Kolory z ról design systemu 1.6.0 (palettes.py): check_bg, check_border,
check_border_hover, check_mark, check_disabled_border, check_disabled_mark.

Uruchom: ``PYTHONPATH=src python -m inyfinn_resizer.app.themes.icons.generate_check_icons``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw

from inyfinn_resizer.app.themes import CHECK_SIZE_PX, CHECK_STATES
from inyfinn_resizer.app.themes.palettes import ROLES, SHAPE

OUT = Path(__file__).resolve().parent

LOGICAL = CHECK_SIZE_PX  # px wskaźnika w interfejsie (stała w themes/__init__.py)
FINAL = 80  # 4× — rozmiar pliku
SS = 4  # nadpróbkowanie przy rysowaniu (łącznie 16×)
BIG = FINAL * SS
U = BIG / LOGICAL  # px obrazu na 1 px interfejsu
BORDER_W = float(SHAPE["check_border_width"].removesuffix("px"))  # 1,5 px z DS
FOCUS_W = BORDER_W  # S15: fokus = ten sam cienki obrys, tylko w kolorze check_border_hover (bez grubszego pierścienia)
RADIUS = float(SHAPE["check_radius"].removesuffix("px"))
TICK = [(5.4, 10.4), (8.7, 13.6), (14.8, 6.6)]
TICK_W = 2.2
DOT_R = 4.2


def _mask_rrect(inset: float, radius: float, round_: bool) -> Image.Image:
    m = Image.new("L", (BIG, BIG), 0)
    d = ImageDraw.Draw(m)
    box = (inset * U, inset * U, BIG - inset * U - 1, BIG - inset * U - 1)
    if round_:
        d.ellipse(box, fill=255)
    else:
        d.rounded_rectangle(box, radius=max(radius * U, 0), fill=255)
    return m


def _tick_mask() -> Image.Image:
    m = Image.new("L", (BIG, BIG), 0)
    d = ImageDraw.Draw(m)
    pts = [(x * U, y * U) for x, y in TICK]
    w = TICK_W * U
    d.line(pts, fill=255, width=round(w), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):  # okrągłe końce
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return m


def _dot_mask() -> Image.Image:
    m = Image.new("L", (BIG, BIG), 0)
    c = BIG / 2
    r = DOT_R * U
    ImageDraw.Draw(m).ellipse((c - r, c - r, c + r, c + r), fill=255)
    return m


def _rgba(hex_color: str) -> tuple[int, int, int, int]:
    return ImageColor.getrgb(hex_color) + (255,)


def draw_state(spec: dict, *, radio: bool, hover: bool, focus: bool, checked: bool, disabled: bool) -> Image.Image:
    """Jeden obraz stanu (80×80 RGBA). ``spec`` = role design systemu danego motywu."""
    # S8: zaznaczony = obrys w kolorze znaku (zielony), niezaznaczony = check_border; najechanie / fokus = hover
    if disabled:
        border = spec["color_check_disabled_border"]
    elif hover or focus:
        border = spec["color_check_border_hover"]
    elif checked:
        border = spec["color_check_mark"]
    else:
        border = spec["color_check_border"]
    mark = spec["color_check_disabled_mark"] if disabled else spec["color_check_mark"]
    width = FOCUS_W if (focus and not disabled) else BORDER_W
    radius = RADIUS

    outer = _mask_rrect(0.0, radius, radio)
    inner = _mask_rrect(width, max(radius - width, 0.5), radio)
    ring = ImageChops.subtract(outer, inner)

    canvas = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    canvas.paste(Image.new("RGBA", (BIG, BIG), _rgba(spec["color_check_bg"])), (0, 0), inner)
    canvas.paste(Image.new("RGBA", (BIG, BIG), _rgba(border)), (0, 0), ring)
    if checked:
        canvas.paste(Image.new("RGBA", (BIG, BIG), _rgba(mark)), (0, 0), _dot_mask() if radio else _tick_mask())
    return canvas.resize((FINAL, FINAL), Image.LANCZOS)


def main() -> None:
    count = 0
    for key, spec in ROLES.items():
        for kind, radio in (("cb", False), ("rb", True)):
            for state, (hover, focus, checked, disabled) in CHECK_STATES.items():
                img = draw_state(spec, radio=radio, hover=hover, focus=focus, checked=checked, disabled=disabled)
                img.save(OUT / f"{kind}-{key}-{state}.png")
                count += 1
    print("OK", count, "files in", OUT)


if __name__ == "__main__":
    main()
