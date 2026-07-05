# Inyfinn Photo Resizer

Native Windows desktop batch image converter and compressor — an enhanced alternative to [FastStone Photo Resizer](https://www.faststone.org/FSResizerDetail.htm) with WebP, AVIF, HEIC, GIF compression, and modern formats.

**No Electron. No Chromium.** Built with Python + PySide6 (Qt6) + libvips/pyvips.

## Features

- **Batch Convert** — drag & drop, multi-threaded processing, FastStone-style 3-column UI
- **Formats** — read JPEG, PNG, GIF, BMP, TIFF, WebP, AVIF, HEIC, JPEG2000, RAW (bonus); write WebP, AVIF, HEIC, JXL, PDF and more
- **Compression** — pngquant (PNG), quality slider, target file size (KB), gifsicle (GIF)
- **Advanced** — resize, rotate, crop, adjustments, watermark (panel), metadata
- **Batch Rename** — templates `{name}_{counter:04d}`, search & replace preview
- **CLI** — headless scripting for WooCommerce/PrestaShop workflows
- **Dark / Light** theme
- **Presets** — JSON export/import

## Quick start

```powershell
cd "D:\--- INYFINN - PROJEKTY\--- OSOBISTE\PHOTO RESIZER"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# GUI
inyfinn-photo-resizer

# CLI
python -m inyfinn_resizer.cli convert -i tests/fixtures/IMG_0113.jpg -o tests/output -f webp -q 85 --overwrite

# Tests
pytest tests/ -v
```

## Optional tools (bundled in `tools/`)

| Tool | Purpose |
|------|---------|
| libvips | Fast decode/encode WebP, AVIF, HEIC |
| pngquant | PNG palette compression |
| gifsicle | GIF optimization |
| cwebp | WebP encoder |
| avifenc | AVIF encoder |
| oxipng | PNG lossless optimize |

Copy `pngquant.exe` to `tools/pngquant/` or set `PNGQUANT` env var.

## Build & release

Dwuklik **`build.bat`** (lub `scripts\package_release.ps1`) tworzy gotowy folder:

```
release/
  InyfinnPhotoResizer.exe    ← uruchom ten plik
  InyfinnPhotoResizer.ico    ← ikona skrótu Windows
  _internal/                 ← biblioteki, pngquant, motywy (nie ruszaj)
```

Artefakty buildu trafiają do `build/` (poza `release/`).

Instalator Inno Setup (opcjonalnie):

```powershell
# Po build.bat — skompiluj installer\inyfinn_resizer.iss w Inno Setup
```

## Related projects

- [GIF-COMPRESOR](https://github.com/inyfinn/GIF-COMPRESOR) — GIF compression (gifsicle pipeline ported here)
- Photoshop export scripts — `_compress_wizek.py` pngquant calibration ported to `core/compressors/`

## License

MIT
