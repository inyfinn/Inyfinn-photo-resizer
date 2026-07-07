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
