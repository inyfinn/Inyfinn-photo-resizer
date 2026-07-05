"""Generate Inyfinn Photo Resizer .ico for Windows EXE and shortcut."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "icon.ico"


def _frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(2, size // 16)
    draw.rounded_rectangle(
        (pad, pad, size - pad - 1, size - pad - 1),
        radius=max(4, size // 8),
        fill=(15, 23, 42, 255),
        outline=(56, 189, 248, 255),
        width=max(1, size // 32),
    )
    inner = size // 5
    draw.rounded_rectangle(
        (inner, inner, size - inner - 1, size - inner - 1),
        radius=max(3, size // 12),
        fill=(30, 41, 59, 255),
    )
    cx, cy = size // 2, size // 2
    r = size // 6
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(56, 189, 248, 255))
    arrow = size // 4
    draw.polygon(
        [
            (size - inner - arrow, size - inner - arrow // 2),
            (size - inner - 2, size - inner - 2),
            (size - inner - arrow // 2, size - inner - arrow),
        ],
        fill=(34, 197, 94, 255),
    )
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [_frame(s) for s in sizes]
    frames[-1].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
