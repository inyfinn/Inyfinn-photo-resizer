# memory.md — Inyfinn Photo Resizer

> Pamięć operacyjna agenta Monday. Przy awarii: ten plik + `README.md` + `process.md` (wszystko w `BIN/dev/`).

**Ostatnia aktualizacja:** 2026-09-15 · **Wersja aplikacji:** 2.4.7

---

## Instalator / SmartScreen (2026-09-15)

- Setup bez Authenticode = „Nieznany wydawca” i SmartScreen (user odpalał `2.4.2-setup.exe`).
- `sign_file.ps1` **nie wolno** kończyć `exit 0` przy braku PFX — podpisuje lokalnym certem `CN=Inyfinn Photo Resizer` + TrustedPublisher.
- OV/EV (`INYFINN_CODESIGN_PFX`) gdy będzie — wtedy reputacja też poza tą stacją.
- `build_installer.ps1` kasuje stare `*-setup.exe` po udanym buildzie.

## GitHub / protected branch (2026-09-15)

- Global rule: `~/.cursor/rules/github-protected-branch.mdc` (ruleset `inyfinn-protect-default`).
- `main` tego repo: **publiczne** — GitHub blokuje force-push i usunięcie. Zwykły `git push` zostaje.
- **NIGDY** `--force` na `main`. Prywatne repo Inyfinn bez Pro nie przyjmą rulesetu — agent i tak nie force-pushuje.

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

## Usuwanie tła + kompresja (2026-09-15)

- rembg **przed** resize na pełnym zdjęciu + alpha matting + model General = partia 51 plików „nie działa” (nigdy nie kończy).
- Sieć max 2560 px / wymiar wyjścia. Matting tylko ≤1600 px.
- EXE: nie trzymać `_PROCESS_LOCK` na całym `process_job` — tylko `_INFER_LOCK` wokół `rembg.remove`.
- pngquant `speed=1` przy q≥50 i oxipng `-o 2` + Pillow `optimize=True` = kompresja stoi. Teraz speed ≥4, oxipng `-o 1 --fast`, zlib 6.

## Anulowanie batcha (2026-09-14)

- Nie submitować całej listy do executora. `with ThreadPoolExecutor` przy cancel czeka na wszystkie futures.
- `shutdown(wait=False, cancel_futures=True)` + overlay zamykać w `_on_overlay_abort`, nie dopiero w `_on_finished`.

## Overlay konwersji (2026-09-14)

- Na Windows `font-size` / `font-weight` w QSS na `QLabel` podwójnie maluje glify (zlewające się „Konwersja plików”).
- Font overlaya tylko przez `QFont` w kodzie; QSS zostawia kolor i tło.
- Chip formatu ma własną szerokość z `QFontMetrics` — nie wolno `setFixedSize(36,36)` na „PNG”.
- Tor paska: `@BORDER@`, nie `@BG_INPUT@` (to ten sam kolor co kafelek).

## Start / splash (2026-09-14)

- Splash „Ładowanie aplikacji…” bez dalszego statusu = wyjątek przy imporcie okna. EXE windowed gubi stderr.
- v2.4.2: `results_dialog.py` ucięty na `def _on_done(sel` (tak w gicie). `main_window.py` miał trailing NUL (sync na `D:\Marketing`).
- Przy awarii: `python -m py_compile` na `BIN/dev/src`, potem `activity.log`. Nie zgaduj „wisi hydracja”.

## Recovery przy awarii

1. Sprawdź `BIN\_internal\` — libvips-42.dll, pngquant, gifsicle, imagecodecs/*.pyd.
2. **Agent** uruchamia `package_release.ps1` (nie użytkownik).
3. Błędy kolorów TIFF → `image_loader.py`, nie goły CMYK.convert.
4. Log: `BIN/dev/process.md`.

---

## AVIF / bitmapa RGB (2026-09-10, v2.4.1)

Z DAM bierzemy **kanały**, nie limit wagi:

- AVIF = płaska bitmapa RGB. Spłaszcz warstwy, CMYK→RGB, wyrzuć Pantone/spot, bez ICC/EXIF w pliku.
- **Bez domyślnego capu 70 KB** — to tylko pamięć podręczna DAM. Opcjonalny limit wagi jest wyłączony, chyba że user włączy go w Ustawieniach albo poda `--target-kb`.
- CLI: `--format avif` startuje od jakości 30.

---

## UI — zasady

- Separatory: token `@SEP@` w `app/themes`.
- Dark/light: tokeny QSS, bez hardcoded kolorów light w dark mode.
- Dokumentacja operacyjna: **tylko** `BIN/dev/` — nigdy w korzeniu projektu.
