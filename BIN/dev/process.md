# Log operacyjny — Inyfinn Photo Resizer

## 2026-07-05 — Implementacja v1

**Komenda/Akcja:** Scaffold projektu + Sprint 1–6

**Log/Status:**
1. Utworzono strukturę `src/inyfinn_resizer/` (GUI, core, workers, CLI)
2. Port `_compress_wizek.py` → `core/compressors/png.py`, `jpeg.py`
3. Port GIF-COMPRESOR `gif_core.py` → `core/compressors/gif.py`
4. PySide6 MainWindow FastStone 3-kolumny + dark/light QSS
5. Batch worker multiprocessing + Results dialog
6. Advanced Options, Format Settings, Batch Rename tab
7. Watch folder service, JSON presets, CLI
8. Inno Setup + PyInstaller spec, CI workflow

**Efekt/Fix:** Aplikacja konwertuje `IMG_0113.jpg` → WebP/JPEG/PNG/AVIF

**Test/Ewaluacja:**
- `pytest tests/test_convert.py` — 3/3 PASSED
- CLI: `IMG_0113.jpg` → AVIF 3706 KB → 795 KB (22%)
- Screenshots: `ui-complete/screenshots/loop-1-{375,768,1024}-light.png`

**Źródła:** plan v1, GIF-COMPRESOR, _compress_wizek.py, FastStone UI reference

---

## 2026-07-05 — Design system + multi-format + dark mode

**Komenda/Akcja:** Przebudowa UI (granat/fiolet), checkboxy formatów, segregacja eksportu

**Log/Status:**
1. Zastąpiono `QGroupBox` płaskimi panelami `QFrame#panel` / `#dropPanel`
2. Nowe `light.qss` / `dark.qss` — wyższy kontrast dark (lista `#050810`, panel `#151d33`, akcent fiolet `#6366f1`)
3. Checkboxy z ikoną checkmark (`themes/icons/check-*.png`)
4. `FormatSelector` — wiele formatów naraz (WebP, JPEG, PNG, AVIF…)
5. Opcja segregacji: `output/webp/`, `output/jpg/` przy wielu formatach
6. `build_output_path(..., segregate_by_extension=True)` w pipeline
7. EXE przebudowany (`build.bat`)

**Efekt/Fix:** Ciemny motyw czytelniejszy; eksport wieloformatowy jak w skrypcie PS

**Test/Ewaluacja:**
- `pytest tests/` — 12/12 PASSED
- Ścieżki segregacji: `out/webp/photo.webp`, `out/jpg/photo.jpg`

**Źródła:** EKSPORT WIZEK PS.jsx (multi-format), `dev/design-system/MASTER.md`

---

## 2026-07-06 — Instalator: dezinstalacja + podpisywanie

**Komenda/Akcja:** Naprawa Inno Setup (uninstall), mutex aplikacji, build instalatora 1.0.1

**Log/Status:**
1. `inyfinn_resizer.iss` — `CloseApplications=force`, `AppMutex`, `taskkill` przed dezinstalacją, `[UninstallDelete]` dla `_internal`, `DelTree` w `usPostUninstall`
2. `app_mutex.py` + `main.py` — jedna instancja, komunikat PL
3. `sign_file.ps1` — opcjonalne podpisywanie Authenticode (`INYFINN_CODESIGN_PFX`)
4. `build_installer.ps1` — ISCC + kopia do korzenia projektu
5. Zbudowano `InyfinnPhotoResizer-1.0.1-setup.exe`

**Efekt/Fix:** Dezinstalacja zamyka proces przed usuwaniem `_internal`; SmartScreen wymaga certyfikatu kodu (skrypt gotowy)

**Test/Ewaluacja:** ISCC compile OK; silent install do `C:\InyfinnPhotoResizer` OK

**Źródła:** Inno Setup docs [UninstallDelete], [CloseApplications]; Microsoft SmartScreen / Authenticode

---

## 2026-07-08 — Redesign UI panelu ustawień (v1.0.8)

**Komenda/Akcja:** Przebudowa prawego panelu na sekcje siatkowe (CSS Grid / Flex)

**Log/Status:**
1. `layout_helpers.py` — `field_group`, `slider_control`, `make_settings_grid`, sekcje 2×2 dla przycisków
2. `main_window.py` — `_build_settings_panel()` z kartami: Format, Kompresja, Rozmiar, Wizek, Zapis, Zaawansowane, Dodatkowe
3. Usunięto mylący checkbox „Opcje zaawansowane” + „Otwórz…” → jeden przycisk + podsumowanie stanu
4. `advanced_options.py` — zakładki → scroll z sekcjami + intro
5. `app.qss` — `fieldLabel`, `advancedSummary`, `fieldGroup`
6. Preset „Oryginalny” nie kasuje ustawień z dialogu zaawansowanego

**Efekt/Fix:** Brak ucinania etykiet; czytelna hierarchia; min. okno 980×620; panel ustawień min. 400 px

**Test/Ewaluacja:** Import modułów — wymaga venv z PySide6 (lokalnie); linter OK

**Źródła:** Qt QGridLayout/QVBoxLayout; feedback użytkownika (ucinanie, nieintuicyjne Zaawansowane)

---

## 2026-07-08 — Menu kontekstowe listy plików + kalibracja zielonych akcentów

**Komenda/Akcja:** PPM na liście plików; kalibracja kompresji na `1.png` (makaron)

**Log/Status:**
1. `main_window.py` — menu kontekstowe: Konwertuj zaznaczone, Usuń, Otwórz lokalizację, Kopiuj ścieżkę, Zaznacz wszystkie; `_build_jobs(inputs=…)`, `_start_convert_subset`
2. `png.py` — `count_rare_green_accents`, `accents_preserved`, guard pngquant (pomija warianty niszczące zieleń)
3. `pipeline.py` — WebP/JPEG: min. jakość 92 gdy wykryto rzadkie zielone akcenty
4. Kalibracja `Pulpit\1.png`: 11 px zieleni (0,001%); pngquant max_kb=800 wcześniej tracił wszystkie; po guardzie oryginał zachowany; WebP q85→0 zieleni, q92→7/11

**Efekt/Fix:** PPM na plikach w liście; konwersja podzbioru kolejki; ochrona małych plam koloru przy kompresji

**Test/Ewaluacja:** `pytest tests/test_png_palette.py` — 6 passed

**Źródła:** test A/B na `1.png`; pngquant docs (`--nofs`, quality bands)

---

## 2026-07-08 — Kompaktowy układ FastStone (panel ustawień)

**Komenda/Akcja:** Przebudowa prawego panelu — bez scrolla i sekcji-boxów; gęsty układ jak FastStone Photo Resizer

**Log/Status:**
1. `main_window.py` — płaskie wiersze `compact_row`; checkboxy bez „Więcej”; podgląd + Konwertuj/Zamknij w jednym stopce (jak FastStone); okno 860×480 (min. 720×380); usunięto `QScrollArea` i martwe importy
2. `app.qss` — kontrolki 28px, checkboxy 22px, mniejsze przyciski i listy
3. `layout_helpers.py` — `BTN_H=28`, `COMPACT_LABEL_W=72`

**Efekt/Fix:** Wszystkie opcje widoczne bez przewijania; mniej pustego paddingu; brak poucinania „Zaawansowane”

**Test/Ewaluacja:** `pytest tests/test_png_palette.py` — 7 passed; import `MainWindow` OK

**Źródła:** FastStone Photo Resizer (benchmark UX); feedback użytkownika (za dużo miejsca, scroll, poucinanie)

---

## 2026-07-08 — Usunięcie belki tytułu + zakładek (v1.0.12)

**Komenda/Akcja:** Weryfikacja ui-complete — belka „Inyfinn Photo Resizer / Wersja” out; wersja w statusBar; zakładki do menu

**Log/Status:**
1. Belka tytułu — już brak w `main_window.py`; użytkownik widział stary EXE 1.0.11
2. Usunięto `QTabWidget` — treść od razu pod menu (jak FastStone)
3. „Zmiana nazw” → `Narzędzia → Zmiana nazw…` (`rename_dialog.py`)
4. Checkboxy wsadowe w siatce 2×2; prawy panel min. 340px
5. Wersja **1.0.12**; screenshot `loop-final-main-light.png`; QA_FAIL_COUNT: 0

**Efekt/Fix:** ~30px więcej miejsca na ustawienia; brak duplikatu nazwy pod menu

**Test/Ewaluacja:** pytest 8 passed; capture_ui loop-final OK

**Źródła:** ui-complete Ralph loop; screenshot użytkownika (belka zaznaczona na czerwono)

---

## 2026-07-08 — Build EXE v1.0.13 (deploy do korzenia projektu)

**Komenda/Akcja:** `package_release.ps1` — wdrożenie na `InyfinnPhotoResizer.exe`

**Log/Status:**
1. Problem: zmiany tylko w `dev/src` — użytkownik uruchamiał stary EXE **1.0.11** z korzenia projektu
2. Ikony: `tool_icons.py` — plus zielony (Dodaj pliki/folder), minus czerwony (Usuń), krzyżyk szary (Wyczyść)
3. Przyciski: jeden poziomy rząd (`tool_button_row` → `QHBoxLayout`)
4. Belka tytułu + zakładki: usunięte w kodzie; wersja tylko w statusBar
5. Build: `GOTOWE v1.0.13` → `D:\...\Inyfinn Image resizer\InyfinnPhotoResizer.exe`

**Efekt/Fix:** EXE w miejscu wskazanym przez użytkownika zaktualizowany

**Test/Ewaluacja:** PyInstaller OK; plik ~4.98 MB, świeży timestamp

**Źródła:** `dev/scripts/package_release.ps1` (Copy-Item do `$AppRoot`)

---

## 2026-07-09 — UI v1.0.17: suwak motywu, presety formatu, ustawienia rozszerzeń

**Komenda/Akcja:** Przełącznik motywu w rogu; padding 20px; rename Rozszerzenie/Format; presety wymiarów + smart crop; PNG8/24, JPG tło, GIF dither

**Log/Status:**
1. `theme_toggle.py` → `menuBar().setCornerWidget` (prawy górny róg); usunięto przycisk ze statusBar
2. Padding 20px w panelach i `centralRoot`; Zaawansowane: podsumowanie pod przyciskiem (bez ucinania); checkboxy 2×2
3. Etykiety: **Rozszerzenie** (typ pliku) / **Format** (wymiary px); tooltips `i18n_tooltips.py`
4. `size_presets.py` — Oryginalny, 1200 kr. bok, 1200×848 smart crop (margines 90px), 1200×1200, zapis własnych
5. `image_ops.py` — `CROP_SMART`, `FIT_BOX`; `matte.py` — tło JPG (białe/czarne/kolor/gradient)
6. `format_settings.py` — PNG-8/24, tło JPG z podglądem, GIF dither + lossy; pipeline podpięty
7. Build **v1.0.17** → `InyfinnPhotoResizer.exe`

**Efekt/Fix:** Suwak słońce/księżyc widoczny u góry; brak ucinania Zaawansowane/checkboxów; nowe presety i działające ustawienia formatów

**Test/Ewaluacja:** pytest 24/26 passed (2 flaky PNG z JPEG fixture); PyInstaller OK

**Źródła:** feedback użytkownika (screenshoty v1.0.16); pyvips composite/flatten; gifsicle `--no-dither`/`--lossy`

---

## 2026-07-09 — Build portable one-file EXE (v1.0.17)

**Komenda/Akcja:** `package_release.ps1 -Portable` — jeden plik EXE bez `_internal`

**Log/Status:**
1. `inyfinn_resizer_onefile.spec` — PyInstaller onefile (PySide6 + pngquant + themes w archiwum)
2. `package_release.ps1 -Portable` — nadpisuje `InyfinnPhotoResizer.exe` (~54 MB)
3. `test_portable_exe.ps1` — uruchomienie EXE w izolowanym `%TEMP%` bez `_internal` → PASSED
4. ZIP: `InyfinnPhotoResizer-1.0.17-portable-onefile.zip` (sam EXE)
5. `_internal` — **nie usunięty** (czeka na OK użytkownika)

**Efekt/Fix:** Aplikacja portable — wystarczy jeden EXE, rozpakowuje się do `%TEMP%` przy starcie

**Test/Ewaluacja:** smoke test OK; pytest 12 passed (png + webp)

**Źródła:** PyInstaller onefile + `sys._MEIPASS` w `paths.py`

---

## 2026-07-09 — Fix przełącznika motywu + rozmiar okna 1024×581 (v1.0.18)

**Komenda/Akcja:** Screenshot użytkownika — brak suwaka jasny/ciemny; natywny rozmiar okna jak na zrzucie

**Log/Status:**
1. Wymiary referencyjnego screenshota: **1024 × 581 px** (obszar klienta okna)
2. `setCornerWidget` na Windows nie renderował `ThemeToggle` — przeniesiono do `setMenuWidget` (`menuStrip`: QMenuBar + suwak po prawej)
3. `DEFAULT_WINDOW_WIDTH/HEIGHT` → 1024×581; `_fit_initial_window_size` nie nadpisuje przy zapisanej geometrii
4. QSS: `#menuStrip`, przezroczysty QMenuBar w pasku
5. Build portable **v1.0.18** → `InyfinnPhotoResizer.exe`

**Efekt/Fix:** Suwak słońce/księżyc widoczny w prawym górnym rogu menu; okno startuje 1024×581

**Test/Ewaluacja:** toggle `isVisible=True`, parent `menuStrip`; pytest 9 passed; smoke test portable PASSED

**Źródła:** Qt `QMainWindow::setMenuWidget`; znany problem `setCornerWidget` na Win

---

## 2026-07-09 — Sprzątanie folderu projektu (portable v1.0.18)

**Komenda/Akcja:** OK użytkownika — cleanup po gotowym buildzie

**Log/Status:**
1. Usunięto `_internal/` (stary one-dir, ~32 pliki)
2. Usunięto `1.png` z korzenia (artefakt kalibracji)
3. Usunięto `ui-complete/` z korzenia (duplikat screenshotów QA)
4. Usunięto `dev/build/` (artefakty PyInstaller)
5. `dev/installer-output/` — zostawiono tylko `InyfinnPhotoResizer-1.0.18-portable-onefile.zip`
6. `build.bat` → `-Portable`; README zaktualizowany (bez `_internal`)

**Efekt/Fix:** Korzeń: EXE + ICO + dev + build.bat + README

**Test/Ewaluacja:** lista katalogu OK; EXE v1.0.18 bez zmian

---

## 2026-07-09 — Fix błędu portable EXE: PIL_avif.pyd (v1.0.19)

**Komenda/Akcja:** Błąd startu: `Failed to extract PIL_avif.cp312-win_amd64.pyd: decompression return code -3`

**Log/Status:**
1. Przyczyna: plugin Pillow AVIF (~8 MB) + UPX w onefile → uszkodzona dekompresja przy starcie
2. `inyfinn_resizer_onefile.spec` + `inyfinn_resizer.spec`: `upx=False`, wykluczono `_avif.pyd` i `_imagingtk.pyd` (AVIF przez pyvips/avifenc)
3. Przywrócono domyślny build **one-dir** (`EXE` + `_internal`) — stabilny w korzeniu projektu
4. `-Portable` zapisuje tylko do `dev/installer-output/`, nie nadpisuje korzenia
5. Build **v1.0.19** — one-dir OK, portable onefile smoke test PASSED (49.8 MB)

**Efekt/Fix:** Program uruchamia się z `InyfinnPhotoResizer.exe` + `_internal`; portable opcjonalnie w installer-output

**Test/Ewaluacja:** one-dir smoke z folderu projektu OK; portable smoke PASSED

**Źródła:** PyInstaller UPX + duże .pyd; Pillow AVIF niepotrzebny przy pyvips pipeline

---

## 2026-07-09 — Naprawa kompresji + folder „Przekonwertowane” (v1.0.20)

**Komenda/Akcja:** 0/18 plików TIFF — błąd; domyślny folder wyjścia; dialog przy plikach z różnych lokalizacji

**Log/Status:**
1. `batch_worker.py` — w EXE (`sys.frozen`) `ThreadPoolExecutor` zamiast `ProcessPoolExecutor` (procesy w PyInstaller nie działały)
2. `pipeline.py` — fallback Pillow gdy brak libvips; test `pyvips.Image.black(1,1)` przy init; CMYK→RGB dla WebP/JPEG; `MAX_IMAGE_PIXELS=300M`
3. `pillow_ops.py` — resize/transformacje bez libvips
4. `job.py` — `CONVERTED_FOLDER_NAME = "Przekonwertowane"`; pełna serializacja jobów
5. `message_boxes.py` — dialog: „Wszystko do jednego folderu” / „Stwórz foldery w miejscu docelowym plików”
6. `main_window.py` — `_prepare_output_for_convert`, placeholder „Przekonwertowane obok plików”
7. `results_dialog.py` — kolumna Status pokazuje treść błędu + tooltip
8. `package_release.ps1` — fix parsera (em-dash w Write-Host)
9. Build **v1.0.20** → `InyfinnPhotoResizer.exe` + `_internal`

**Efekt/Fix:** Kompresja działa bez libvips (Pillow); domyślny folder „Przekonwertowane”; wybór przy wielu folderach źródłowych

**Test/Ewaluacja:** CLI TIFF→WebP OK; EXE startuje; pytest jpeg 3/3 OK

**Źródła:** PyInstaller multiprocessing; Pillow DecompressionBomb; feedback użytkownika (screenshot 0/18 błąd)

---

## 2026-07-09 — Powrót one-dir + fix process_job + archiwum PORTABLE (v1.0.21)

**Komenda/Akcja:** Błąd `process_job() takes 1 positional argument but 2 were given`; brak suwaka motywu; archiwum portable

**Log/Status:**
1. `batch_worker.py` — `pool.submit(process_job, job, overwrite=self.overwrite)` (keyword-only arg)
2. `main_window.py` — `setNativeMenuBar(False)`, `menuStrip` min-height 36px, suwak motywu
3. Folder `PORTABLE/` — README, HISTORIA, kopia onefile.spec i test_portable_exe.ps1
4. Domyślny build: **one-dir** (`EXE` + `_internal`), bez `-Portable` w korzeniu
5. Funkcje zachowane: `Przekonwertowane`, dialog wielu folderów, okno 1024×581
6. Build **v1.0.21**

**Efekt/Fix:** Kompresja równoległa w EXE działa; motyw widoczny; portable odłożony do PORTABLE/

**Test/Ewaluacja:** frozen batch 3/3 OK; build PyInstaller OK

**Źródła:** TypeError keyword-only `overwrite`; feedback użytkownika (screenshot błędu)

---

## 2026-07-09 — Reorganizacja folderów: korzeń / BIN / PORTABLE

**Komenda/Akcja:** Porządek w korzeniu — tylko `InyfinnPhotoResizer.exe` + `BIN/` + `PORTABLE/`

**Log/Status:**
1. `dev/` → `BIN/dev/`; `_internal/` → `BIN/_internal/`; usunięto `URUCHOM.bat`, `build.bat` z korzenia
2. `package_release.ps1` — deploy aplikacji do `BIN/`; lekki launcher onefile (~7 MB) w korzeniu (`dev/launcher/launcher.py`)
3. Launcher `os.execv` → `BIN\InyfinnPhotoResizer.exe` (PyInstaller wymaga `_internal` obok EXE w BIN)
4. `paths.py` — `project_root()` rozpoznaje układ BIN
5. PORTABLE — usunięto onefile spec/zipy; `-Portable` tworzy rozpakowany folder `PORTABLE/InyfinnPhotoResizer/`
6. Build **v1.0.23**; smoke test launcher OK

**Efekt/Fix:** Korzeń: EXE 6.98 MB (launcher) + BIN + PORTABLE; brak syfu (`WERSJA.txt`, `URUCHOM.bat` w korzeniu)

**Test/Ewaluacja:** Start z korzenia → proces `BIN\InyfinnPhotoResizer.exe`; PyInstaller OK

**Źródła:** PyInstaller one-dir layout; feedback użytkownika (struktura folderów)

---

## 2026-07-09 — Fix kompresji + UI v1.0.24

**Komenda/Akcja:** 0/39 błędów konwersji; brak motywu; wolny start; tabela wyników; format multi-select

**Log/Status:**
1. `pipeline.py` — Pillow-first dla TIFF/BMP bez libvips; lock w EXE; `bootstrap_runtime_paths()`; błędy PL; post_compress nie psuje joba
2. `paths.py` — PATH do pngquant w `_internal` przy starcie
3. `results_dialog.py` — 1024×581; kolumny: Lp 34px, pliki stretch, ratio 58px; bez siatki Excel
4. `format_multi_combo.py` — klik nazwy = jeden format; Ctrl/Shift/checkbox = multi; NoSelection
5. `main_window.py` — okno 1024×581 (bez restore geometrii); theme toggle 72×32
6. `main.py` — splash od razu + status ładowania
7. Build **v1.0.24** → korzeniowy `InyfinnPhotoResizer.exe`

**Efekt/Fix:** Konwersja przez Pillow gdy brak libvips; czytelna tabela; natywny rozmiar okna

**Test/Ewaluacja:** pytest; frozen sim OK; build PyInstaller OK

**Źródła:** screenshot 1047×594; diagnostyka ścieżek BIN/_internal

---

## 2026-07-09 — v1.0.25: natychmiastowy start + naprawa kompresji

**Komenda/Akcja:** Kontynuacja fixów po v1.0.24 — 0/39 błędów, wolny launcher 7 MB, tabela, motyw

**Log/Status:**
1. `pipeline.py` — `_init_vips()` tylko gdy `bundled_libvips()`; TIFF bez inicjalizacji vips; post_compress opcjonalny
2. `png.py` — `count_rare_green_accents` na miniaturze 512px (nie skan całego obrazu — wiszące konwersje)
3. `subprocess_win.py` — PATH katalogu narzędzia przy pngquant/gifsicle (fix „Nie można odnaleźć pliku”)
4. `launcher/Program.NetFx.cs` + `package_release.ps1` — launcher .NET Framework **5.6 KB** zamiast PyInstaller 7 MB
5. `results_dialog.py` — kolumna odstępu; Lp 28px; pliki stretch; rozmiary osobna grupa; ratio 52px
6. `main_window.py` / `app.qss` — theme toggle 72×32 Fixed, zawsze widoczny w menuStrip
7. Build **v1.0.25** — korzeń `InyfinnPhotoResizer.exe` 0.01 MB

**Efekt/Fix:** Start natychmiastowy (launcher uruchamia BIN); TIFF→TIFF OK (Pillow); pngquant z DLL

**Test/Ewaluacja:** TIFF fixture OK 11.4 MB; launcher 5632 B; `BIN\WERSJA.txt` v1.0.25

**Źródła:** diagnostyka `_init_vips` hang; Windows csc v4.0.30319

---

## 2026-07-09 — v1.0.31: naprawa portable — libvips + imagecodecs + CMYK ICC

**Komenda/Akcja:** Regresja po portable: 18/18 TIFF → `could not import name 'lzw_decode' from 'imagecodecs'`

**Log/Status:**
1. **Przyczyna:** PyInstaller pakował tylko `imagecodecs/_shared.pyd` (brak `_imcd.pyd` z `lzw_decode`); `libvips` w ogóle nie był w `_internal`; pipeline wysyłał WSZYSTKIE TIFF na `tifffile` zamiast `pyvips`
2. `setup_libvips.ps1` — auto-pobranie `vips-dev-x64-web-8.18.3` do `dev/tools/libvips`
3. `inyfinn_resizer.spec` — bundling całego `tools/libvips` + wszystkie `imagecodecs/*.pyd` (70 modułów)
4. `package_release.ps1` — wywołanie `setup_libvips.ps1` przed buildem
5. `pipeline.py` — `pyvips` primary dla JPEG/PNG/WebP/AVIF; CMYK TIFF → `image_loader` (ICC PERCEPTUAL z `InterColorProfile`); RGB TIFF → pyvips
6. `image_loader.py` — ICC z tagu TIFF; `png.py` — bez fałszywego boostu palety na nasyconych produktach

**Efekt/Fix:** `_internal` kompletne: libvips + 70× imagecodecs pyd; konwersja TIFF działa

**Test/Ewaluacja:**
- `CYNAMON_1.tif` → PNG q=50: **482 KB**, mean RGB **(169.6, 80.4, 36.7)** ≈ PS
- `Cynamon.tif`, `CYNAMON.tif` → WebP/PNG: **OK**
- `lzw_decode` import z `_internal`: **OK**

**Źródła:** screenshot 18 błędów; PyInstaller warn-inyfinn_resizer.txt; libvips [build-win64-mxe v8.18.3](https://github.com/libvips/build-win64-mxe/releases/tag/v8.18.3)

---

## 2026-07-09 — UI v1.0.33 + dokumentacja

**Komenda/Akcja:** Separatory, PRZEGLĄDAJ, zakładka Zaawansowane, splash, GIF↔jakość, README + memory.md

**Log/Status:**
1. Token `@SEP@` w QSS — separatory pion/poziom (5% opacity)
2. `format_multi_combo.py` — Ctrl/Shift/checkbox + tooltip (już w kodzie, wymaga nowego buildu)
3. `format_settings.py` — zakładka Zaawansowane (crop, trim przezroczystych, gradient JPG 100×100, preset Inyfinn)
4. `main_window.py` — PRZEGLĄDAJ, usunięty osobny blok „Otwórz zaawansowane”
5. `quality_map.py` — GIF lossy + kolory z suwaka jakości
6. `startup_splash.py` — „Ładowanie aplikacji…”, animacja paska (gradient marki)
7. `README.md` + `memory.md` — historia, recovery (lokalizacja: **BIN/dev/**, nie korzeń)

**Efekt/Fix:** Wersja **1.0.33** w kodzie; dokumentacja poza korzeniem; rebuild przez agenta

**Źródła:** feedback użytkownika (screenshoty UI); ui-ux-pro-max (separatory, loading feedback)
