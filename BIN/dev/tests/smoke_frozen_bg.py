"""Smoke test zbudowanego EXE — usuwanie tla + metadane pymatting."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIN = ROOT / "BIN"
INTERNAL = BIN / "_internal"
EXE = ROOT / "InyfinnPhotoResizer.exe"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "IMG_0113.jpg"
OUT = Path(__file__).resolve().parent / "output" / "frozen_bg_smoke.png"

SCRIPT = r"""
import os
import sys
from pathlib import Path

internal = Path(r"{internal}")
sys.path.insert(0, str(internal))
os.chdir(r"{bin}")
os.environ["U2NET_HOME"] = str(internal / "tools" / "rmbg")
sys.frozen = True

from importlib import metadata as importlib_metadata
print("pymatting_version", importlib_metadata.version("pymatting"))

from inyfinn_resizer.core.transforms.background_removal import alpha_matting_available
print("alpha_matting_available", alpha_matting_available())

from inyfinn_resizer.core.job import FormatOptions, JobSpec, TransformOptions
from inyfinn_resizer.core.pipeline import process_job

job = JobSpec(
    input_path=Path(r"{fixture}"),
    output_path=Path(r"{out}"),
    output_format="png",
    format_opts=FormatOptions(quality=50, png_mode="png8"),
    transforms=TransformOptions(
        remove_background=True,
        bg_model="birefnet-general-lite",
        bg_alpha_matting=True,
        bg_post_process_mask=True,
    ),
)
result = process_job(job, overwrite=True)
print("status", result.status.value, result.message)
if result.status.value != "OK":
    raise SystemExit(2)

from PIL import Image
import numpy as np
with Image.open(r"{out}") as im:
    alpha = np.array(im.split()[-1])
    ratio = float((alpha < 10).sum()) / alpha.size
print("transparent_pct", round(ratio * 100, 1))
if ratio < 0.10:
    raise SystemExit(3)
"""


def main() -> int:
    assert EXE.is_file(), f"Brak EXE: {EXE}"
    assert FIXTURE.is_file(), f"Brak fixture: {FIXTURE}"
    assert (INTERNAL / "tools" / "rmbg").is_dir(), "Brak modeli w BIN/_internal/tools/rmbg"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.unlink(missing_ok=True)

    code = SCRIPT.format(
        internal=str(INTERNAL).replace("\\", "\\\\"),
        bin=str(BIN).replace("\\", "\\\\"),
        fixture=str(FIXTURE).replace("\\", "\\\\"),
        out=str(OUT).replace("\\", "\\\\"),
    )
    py = ROOT / "BIN" / "dev" / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.run([str(py), "-c", code], capture_output=True, text=True, cwd=str(BIN))
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
