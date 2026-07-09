"""Kalibracja zachowania zielonych akcentów przy kompresji PNG."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image

from inyfinn_resizer.core.compressors.png import find_tool
from inyfinn_resizer.utils.subprocess_win import run_hidden

SRC = Path(r"C:\Users\krzysztof.wieczorek\OneDrive - Kubara Sp. z o.o\Pulpit\1.png")
WORK = Path(__file__).resolve().parent.parent / "tests" / "output" / "calibrate_spaghetti"


def green_stats(path: Path) -> int:
    img = Image.open(path).convert("RGB")
    data = list(img.get_flattened_data())
    return sum(1 for r, g, b in data if g > r + 12 and g > b + 12 and g > 80)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    pngquant = find_tool("pngquant")
    if not pngquant:
        print("brak pngquant")
        return

    orig = green_stats(SRC)
    print(f"orig green={orig} size={SRC.stat().st_size // 1024}KB")

    for nofs in (False, True):
        for q in ("80-95", "85-98", "90-100"):
            tag = f"nofs{nofs}_q{q.replace('-', '_')}"
            dst = WORK / f"{tag}.png"
            src_copy = WORK / f"{tag}.src.png"
            shutil.copy2(SRC, src_copy)
            cmd = [
                str(pngquant),
                "--force",
                "--quality",
                q,
                "--speed",
                "1",
                "256",
                "--output",
                str(dst),
                "--",
                str(src_copy),
            ]
            if nofs:
                cmd.insert(2, "--nofs")
            run_hidden(cmd, timeout=120)
            if dst.exists():
                g = green_stats(dst)
                print(
                    f"nofs={nofs} q={q} {dst.stat().st_size // 1024}KB "
                    f"green={g} loss={orig - g}"
                )
            src_copy.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
