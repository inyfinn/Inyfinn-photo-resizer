# memory.md — Inyfinn Photo Resizer

> Pamięć operacyjna agenta Monday. Przy awarii: ten plik + `README.md` + `process.md` (wszystko w `BIN/dev/`).

**Ostatnia aktualizacja:** 2026-07-09 · **Wersja aplikacji:** 1.0.33

---

## Zasada nadrzędna (użytkownik)

- **W korzeniu projektu jest tylko `InyfinnPhotoResizer.exe`** (launcher) — żadnych README/memory w korzeniu.
- **Agent sam przebudowuje EXE** — nigdy nie prosi użytkownika o `build.bat` / rebuild.

---

## Cel projektu

Natywna aplikacja Windows (Python 3.12 + PySide6) do wsadowej konwersji i kompresji obrazów.

**Korzeń:** tylko `InyfinnPhotoResizer.exe`  
**Runtime:** `BIN/InyfinnPhotoResizer.exe` + `BIN/_internal/`  
**Kod:** `BIN/dev/src/inyfinn_resizer/`

---

## Build (agent wykonuje sam)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "BIN\dev\scripts\package_release.ps1"
```

Efekt: launcher w korzeniu + pełna aplikacja w `BIN/`.

---

## Co działa

1. Konwersja wsadowa TIFF → PNG/WebP (CMYK + LZW).
2. Kolory CMYK — ICC PERCEPTUAL z `InterColorProfile`.
3. Portable bundle — libvips, pngquant, gifsicle, pełny imagecodecs.
4. UI v1.0.33 — separatory, PRZEGLĄDAJ, zakładka Zaawansowane, multi-select formatów, splash, GIF↔jakość.

---

## Recovery przy awarii

1. Sprawdź `BIN\_internal\` — libvips-42.dll, pngquant, gifsicle, imagecodecs/*.pyd.
2. **Agent** uruchamia `package_release.ps1` (nie użytkownik).
3. Błędy kolorów TIFF → `image_loader.py`, nie goły CMYK.convert.
4. Log: `BIN/dev/process.md`.

---

## UI — zasady (v1.0.33)

- Separatory: token `@SEP@` w `app/themes`.
- Formaty: nazwa = jeden; Ctrl/Shift/checkbox = wiele.
- Zaawansowane: ostatnia zakładka w ustawieniach formatu.
- Dokumentacja: **tylko** `BIN/dev/` — nigdy w korzeniu projektu.
