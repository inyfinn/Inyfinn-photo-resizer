# Inyfinn Photo Resizer

Natywna aplikacja Windows do wsadowej konwersji i kompresji zdjęć. Inspiracja: [FastStone Photo Resizer](https://www.faststone.org/FSResizerDetail.htm), z obsługą WebP, AVIF, HEIC i nowoczesnych formatów.

**Bez Electrona. Bez Chromium.** Python 3.14 + PySide6 (Qt6) + libvips/pyvips.

## Funkcje

- **Konwersja wsadowa** - przeciągnij i upuść, wielowątkowość, układ lista + ustawienia
- **Wiele formatów naraz** - rozwijana lista wielokrotnego wyboru (jak FastStone), opcjonalna segregacja do `webp/`, `jpg/`, `png/`…
- **Formaty** - odczyt JPEG, PNG, GIF, BMP, TIFF, WebP, AVIF, HEIC, JPEG2000; zapis WebP, AVIF, HEIC, JXL, PDF i inne
- **Kompresja** - pngquant (PNG), suwak jakości, gifsicle (GIF)
- **Opcje zaawansowane** - zmiana rozmiaru, obrót, korekcje (EXIF, proporcje)
- **Zmiana nazw** - szablony `{name}_{counter:04d}`, podgląd
- **CLI** - skrypty bez GUI (sklepy, automatyzacja)
- **Motyw jasny / ciemny** - spójny w całej aplikacji (okna dialogowe w tym samym motywie)
- **Presety** - eksport / import JSON
- **Interfejs po polsku**

## Szybki start (użytkownik)

1. Pobierz instalator z [Releases](https://github.com/inyfinn/Inyfinn-photo-resizer/releases) (`InyfinnPhotoResizer-1.0.0-setup.exe`)
2. Uruchom instalator i postępuj według kreatora
3. Uruchom **Inyfinn Photo Resizer** z menu Start lub skrótu na pulpicie

Alternatywnie: rozpakuj paczkę portable i uruchom `InyfinnPhotoResizer.exe` (folder `_internal` musi leżeć obok EXE).

## Szybki start (deweloper)

```powershell
cd dev
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# GUI
inyfinn-photo-resizer

# CLI
python -m inyfinn_resizer.cli convert -i tests/fixtures/IMG_0113.jpg -o tests/output -f webp -q 85 --overwrite

# Testy
pytest tests/ -v
```

## Budowanie EXE

Z katalogu głównego projektu:

```powershell
.\build.bat
```

lub:

```powershell
powershell -File dev\scripts\package_release.ps1
```

Wynik:

```
InyfinnPhotoResizer.exe
InyfinnPhotoResizer.ico
_internal/
```

## Instalator (Inno Setup)

Po zbudowaniu EXE:

```powershell
# Wymaga Inno Setup 6 (ISCC.exe w PATH)
iscc dev\installer\inyfinn_resizer.iss
```

Plik setup trafia do `installer-output/InyfinnPhotoResizer-1.0.0-setup.exe`.

## Opcjonalne narzędzia (`dev/tools/`)

| Narzędzie | Rola |
|-----------|------|
| libvips | Szybkie dekodowanie / kodowanie WebP, AVIF, HEIC |
| pngquant | Kompresja paletowa PNG |
| gifsicle | Optymalizacja GIF |
| oxipng | Bezstratna optymalizacja PNG |

Skopiuj `pngquant.exe` do `dev/tools/pngquant/` lub ustaw zmienną `PNGQUANT`.

## Struktura repozytorium

```
dev/src/inyfinn_resizer/   # kod źródłowy
dev/tests/                 # testy pytest
dev/installer/             # Inno Setup
dev/scripts/               # build, zrzuty UI
build.bat                  # skrót do release
```

## Powiązane projekty

- [GIF-COMPRESOR](https://github.com/inyfinn/GIF-COMPRESOR) - kompresja GIF (pipeline gifsicle)

## Dokumentacja

Szczegóły użytkownika: [docs/DOKUMENTACJA.md](docs/DOKUMENTACJA.md)

## Licencja

MIT
