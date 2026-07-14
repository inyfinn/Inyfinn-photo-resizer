# Historia eksperymentu portable

## v1.0.17 — pierwszy onefile

- `inyfinn_resizer_onefile.spec` dodany
- `-Portable` nadpisywał `InyfinnPhotoResizer.exe` w korzeniu (~54 MB)
- Smoke test OK przy starcie

## v1.0.18 — cleanup + portable domyślny (błąd)

- Usunięto `_internal` z korzenia na prośbę użytkownika
- `build.bat` ustawiony na `-Portable`
- Użytkownik bez `_internal` — niestabilne

## v1.0.19 — powrót one-dir

- Błąd: `PIL_avif.pyd decompression return code -3`
- Fix: `upx=False`, exclude AVIF pyd
- Domyślny build: **EXE + _internal** w korzeniu
- Portable tylko w `dev/installer-output/`

## v1.0.20 — fix kompresji (wprowadzony błąd)

- ThreadPoolExecutor w frozen EXE — dobry kierunek
- **Błąd:** `process_job(j, overwrite)` pozycyjnie — crash przy „Wiele plików jednocześnie”
- Folder `Przekonwertowane`, dialog wielu folderów — OK w kodzie

## v1.0.21 — stabilna one-dir (obecna)

- Fix `overwrite=self.overwrite` w batch_worker
- Motyw: `setNativeMenuBar(False)`, min. wysokość menuStrip
- Portable zarchiwizowany w folderze `PORTABLE/`
- Build domyślny: one-dir, bez `-Portable`
