# Brief — Inyfinn Photo Resizer v1

## Cel
Natywna aplikacja desktop Windows do batch konwersji i kompresji obrazów — ulepszona alternatywa FastStone Photo Resizer z WebP, AVIF, HEIC, GIF i docelowym rozmiarem pliku.

## Deliverable
- Aplikacja `.exe` + instalator Inno Setup
- GUI PySide6 (FastStone 3-kolumny)
- CLI headless
- Dark/Light theme

## Grupa docelowa
Twórca treści, e-commerce (wizki produktowe), marketing — workflow podobny do skryptów Photoshop EKSPORT WIZEK PS.

## Stack
Python 3.10+, PySide6, pyvips, pngquant, gifsicle, Pillow.

## Hard constraints
- **Brak Electron/Chromium/CEF**
- Prostota: 3 kontrolki górne (Format, Rozmiar, Quality)
- Domyślnie WebP q=85, zachowaj EXIF

## Out of scope v1.1
- macOS/Linux installer (kod cross-platform, installer później)

## Źródła reuse
- GitHub [GIF-COMPRESOR](https://github.com/inyfinn/GIF-COMPRESOR)
- `_compress_wizek.py` — pngquant target KB
