# Inyfinn Photo Resizer — dokumentacja deweloperska

Natywna aplikacja Windows (Python 3.12 · PySide6 · libvips · pngquant · gifsicle).  
**Wersja:** 1.0.38 · **Korzeń projektu:** wyłącznie `InyfinnPhotoResizer.exe` (launcher).

Dokumentacja i logi są **tylko tutaj** (`BIN/dev/`), nie w korzeniu.

---

## Uruchomienie

| Tryb | Jak |
|------|-----|
| Produkcja | Dwuklik `InyfinnPhotoResizer.exe` w korzeniu → startuje `BIN\` |
| Dev | `pip install -e ".[dev]"` → `inyfinn-photo-resizer` |

---

## UI v1.0.38 — Wyjście, presety, skala

- **Checkbox „Zapisz do folderu wyjściowego”** — bez zaznaczenia: nadpisanie w miejscu źródła (pytanie: Tak / Tak dla wszystkich / Nie / Nie dla wszystkich).
- **PRZEGLĄDAJ** automatycznie zaznacza checkbox wyjścia.
- **Minus przy Formacie** — usuwanie własnych presetów wymiarów (z potwierdzeniem).
- **Skala** — suwak na pełnej szerokości; min. krawędź wpisywana ręcznie (bez strzałek).

## UI v1.0.37 — Skala i minimum wymiaru

Pod suwakiem **Jakość** znajduje się **Skala** (1–100%):

- Procentowe zmniejszenie obu wymiarów po presecie **Format**.
- Przykład: 50% na obrazie 3000×2000 → 1500×1000 px.

Obok skali:

- **Min. najdłuższa krawędź** (checkbox, domyślnie włączony).
- Pole wartości w px — **domyślnie 1080** (docelowy rozmiar do internetu).
- Gdy obraz po skali byłby mniejszy, program powiększa go proporcjonalnie do minimum.

Kolejność w pipeline: preset Format → **Skala** → **Min. najdłuższa krawędź** → kompresja jakości.

---

## Jak doszliśmy do rozwiązania

### CMYK TIFF
Pillow bez ICC → złe kolory. Fix: `image_loader.py` + ImageCms PERCEPTUAL.

### Portable 18/18 błędów
Brak pełnego imagecodecs i libvips w bundle. Fix: spec PyInstaller + `setup_libvips.ps1` + routing pyvips.

### pngquant
Boost palety na nasyconych produktach. Fix: `png.py` — kalibracja jak EKSPORT WIZEK PS.

### UI v1.0.36
Dropdown formatów (Explorer-style), logi operacji (`BIN/logs/activity.log`), preset 1200 px najdłuższej krawędzi, dialog własnego presetu.

---

## Recovery

1. Sprawdź `BIN\_internal\` (libvips, pngquant, imagecodecs).
2. Przebudowa: `scripts\package_release.ps1 -Release` (wykonuje agent).
3. Szczegóły: `memory.md`, `process.md`.

### Test referencyjny
`CYNAMON_1.tif` → PNG q=50% vs `Test\CYNAMON_1_2.png` (Photoshop).

---

## Struktura

```
(korzeń) InyfinnPhotoResizer.exe    ← tylko launcher
BIN/
  InyfinnPhotoResizer.exe
  _internal/
  dev/          ← ten folder (kod, docs, build)
release/        ← ZIP vX.Y.Z (cały projekt bez PORTABLE/)
```

---

## Build (agent / CI)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\package_release.ps1" -Release
```

Release ZIP zawiera cały folder projektu **bez** `PORTABLE/`.

---

## Licencja

MIT
