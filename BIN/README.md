# Inyfinn Photo Resizer — struktura folderów

## Uruchamianie (użytkownik)

**Zawsze uruchamiaj ten plik:**

```
..\InyfinnPhotoResizer.exe          ← w KORZENIU projektu (launcher ~5 KB)
```

Launcher natychmiast startuje właściwą aplikację z tego folderu:

```
BIN\InyfinnPhotoResizer.exe       ← PyInstaller one-dir (~5 MB)
BIN\_internal\                    ← biblioteki Python, motywy, pngquant
BIN\_internal\tools\pngquant\     ← kompresja PNG
```

Dlaczego EXE jest też w `BIN/`? PyInstaller **one-dir** wymaga, żeby EXE leżał obok `_internal/`. Korzeniowy EXE to tylko lekki starter — nie duplikat do ręcznego uruchamiania.

## Kompresja (pipeline)

| Format | Narzędzie |
|--------|-----------|
| JPEG, WebP, AVIF, TIFF (bez libvips) | Pillow + pipeline |
| PNG | pngquant (+ oxipng) w `_internal/tools/` |
| GIF | gifsicle (jeśli spakowany w `dev/tools/gifsicle/`) |

Źródła: `BIN/dev/src/inyfinn_resizer/core/pipeline.py`, `core/compressors/`

## Deweloper

```powershell
cd BIN\dev
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
inyfinn-photo-resizer
```

Przebudowa:

```powershell
.\BIN\build.bat
# lub:
powershell -File BIN\dev\scripts\package_release.ps1
```

Wynik: korzeń `InyfinnPhotoResizer.exe` + zaktualizowany `BIN\`.

## Portable (opcjonalnie)

```powershell
powershell -File BIN\dev\scripts\package_release.ps1 -Portable
```

Wynik: `PORTABLE/InyfinnPhotoResizer/` — folder do skopiowania (EXE + `_internal`).
