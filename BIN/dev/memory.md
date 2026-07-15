# memory.md — Inyfinn Photo Resizer

> Pamięć operacyjna agenta Monday. Przy awarii: ten plik + `README.md` + `process.md` (wszystko w `BIN/dev/`).

**Ostatnia aktualizacja:** 2026-07-15 · **Wersja aplikacji:** 1.0.61

---

## Zasada nadrzędna (użytkownik)

- **Użytkownik NIGDY nie robi buildu, commita, release ani konfiguracji.** Agent wykonuje wszystko sam.
- **W korzeniu projektu jest tylko `InyfinnPhotoResizer.exe`** (launcher) — żadnych README/memory w korzeniu.
- **Agent sam przebudowuje EXE** — nigdy nie prosi użytkownika o `build.bat` / rebuild.

---

## Cel projektu

Natywna aplikacja Windows (Python 3.12 + PySide6) do wsadowej konwersji i kompresji obrazów.

**Korzeń:** tylko `InyfinnPhotoResizer.exe`  
**Runtime:** `BIN/InyfinnPhotoResizer.exe` + `BIN/_internal/`  
**Kod:** `BIN/dev/src/inyfinn_resizer/`  
**Repo GitHub:** `inyfinn/Inyfinn-photo-resizer`

---

## Auto-update (od v1.0.60)

### Zachowanie aplikacji u użytkownika

1. Przy starcie (co 6 h): sprawdzenie GitHub Releases w tle.
2. Nowa wersja → pobieranie ZIP w tle → toast w lewym dolnym rogu.
3. **Pomoc → Sprawdź aktualizacje…** → dialog z **„Pobierz i zainstaluj”**.
4. Instalacja: zamknięcie app → PowerShell rozpakowuje → podmienia pliki → **uruchamia ponownie**.
5. **Po restarcie — jednorazowy komunikat:** „Udało się zaktualizować do wersji X.Y.Z” (marker `pending_success.json`).
6. Cache aktualizacji: max **2 pakiety** w `%LOCALAPPDATA%\Inyfinn\PhotoResizer\updates\`.

### Obowiązki agenta przy każdej nowej wersji

Agent **sam** wykonuje (użytkownik nie):

1. Podbić `__version__` w `src/inyfinn_resizer/__init__.py`.
2. Build: `powershell -File BIN\dev\scripts\package_release.ps1 -Release`
3. Commit + push na `main`.
4. Tag + GitHub Release z ZIP: `InyfinnPhotoResizer-v{version}.zip`
5. Ustawić release jako **Latest**.

**Sam push na git NIE aktualizuje użytkowników** — wymagany jest GitHub Release z ZIP.

---

## Build (agent wykonuje sam)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "BIN\dev\scripts\package_release.ps1"
```

Release ZIP:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "BIN\dev\scripts\package_release.ps1" -Release
```

Efekt: launcher w korzeniu + pełna aplikacja w `BIN/` + opcjonalnie `release/InyfinnPhotoResizer-vX.Y.Z.zip`.

---

## Recovery przy awarii

1. Sprawdź `BIN\_internal\` — libvips-42.dll, pngquant, gifsicle, imagecodecs/*.pyd.
2. **Agent** uruchamia `package_release.ps1` (nie użytkownik).
3. Błędy kolorów TIFF → `image_loader.py`, nie goły CMYK.convert.
4. Log: `BIN/dev/process.md`.

---

## UI — zasady

- Separatory: token `@SEP@` w `app/themes`.
- Dark/light: tokeny QSS, bez hardcoded kolorów light w dark mode.
- Dokumentacja operacyjna: **tylko** `BIN/dev/` — nigdy w korzeniu projektu.
