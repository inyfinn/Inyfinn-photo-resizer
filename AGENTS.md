# AGENTS.md

## Cursor Cloud specific instructions

This repository is **Inyfinn Photo Resizer** — a native **Windows** batch image
converter/resizer/compressor GUI app (Python + PySide6/Qt6 + libvips + pngquant).
The cloud VM is **Linux**, so the app runs here through its cross-platform code
paths (it gracefully falls back from bundled libvips to Pillow, and the external
encoders come from the system `PATH` instead of the bundled Windows `.exe`s).

### Where the code lives
- The real project root is **`BIN/dev/`** (source, `pyproject.toml`, `tests/`, docs).
  The top-level `dev/` folder is a stale partial stub — ignore it.
- Package source: `BIN/dev/src/inyfinn_resizer/`. Entry point: `inyfinn_resizer.main:main`
  (console script `inyfinn-resizer`, GUI script `inyfinn-photo-resizer`).

### Environment (already set up by the startup update script)
- A Python venv lives at **`BIN/dev/.venv`**. Activate with
  `source BIN/dev/.venv/bin/activate` before running anything.
- **Non-obvious dependency caveat:** `pyproject.toml` pins `onnxruntime-directml`,
  which is **Windows-only and cannot install on Linux**. The update script therefore
  installs the Linux-compatible dependency subset explicitly and then runs
  `pip install -e BIN/dev --no-deps`. Do **not** run a plain `pip install -e ".[dev]"`
  on this VM — it will fail on `onnxruntime-directml`.
- Consequence: the **AI background-removal** feature (`rembg` + ONNX) and its test
  `tests/test_background_removal.py` are **not available** on Linux (optional feature).
- System packages `libvips42`, `pngquant`, `webp` (`cwebp`), `gifsicle`, `xvfb`, and the
  Qt xcb libraries (incl. `libxcb-cursor0`) are preinstalled in the VM snapshot.

### Run / lint / test (from `BIN/dev/`, venv activated)
- **Lint:** `ruff check src tests` — the tool works, but the repo currently has
  pre-existing lint findings; a clean exit is not expected. This is codebase state,
  not an environment problem.
- **Tests (CI target):** `pytest tests/test_convert.py -v`. On Linux 11/12 pass;
  `test_png_pngquant_real_compression[75]` fails because it asserts a palette-PNG of a
  detailed photo is smaller than the heavily-compressed source JPEG — a size threshold
  that is encoder/backend sensitive (Linux uses the Pillow save path, not bundled
  libvips). Not an environment issue.
- **Run the GUI:** it needs a display. A VNC X server is available on `DISPLAY=:1`.
  Launch with `DISPLAY=:1 QT_QPA_PLATFORM=xcb inyfinn-photo-resizer`.
  For headless screenshots without a display, use `xvfb-run -a python tests/screenshot_app.py`.
- **Single-instance mutex:** the app enforces one running instance; if a launch exits
  immediately, an instance is likely already running — reuse it or terminate it by PID.

### Windows-only tooling (not runnable here)
The `*.ps1` / `*.bat` scripts under `BIN/` and `BIN/dev/scripts/`, the PyInstaller specs,
and Inno Setup installer are for producing the Windows `.exe`/installer and cannot run on
this Linux VM.
