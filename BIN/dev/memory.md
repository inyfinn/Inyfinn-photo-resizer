# memory.md — Inyfinn Photo Resizer

> Pamięć operacyjna agenta Monday. Przy awarii: ten plik + `README.md` + `process.md` (wszystko w `BIN/dev/`).

**Ostatnia aktualizacja:** 2026-10-06 · **Wersja aplikacji:** 2.6.6

---

## UWAGI.txt — zgłoszenia od zespołu (od 2026-09-18)

- Plik w korzeniu projektu (poza gitem). Ludzie dopisują na dole: Imię, Dział, Problem, Data.
- Po naprawie: usuń zgłoszenie z „Nowe uwagi”, w „Sprawdzono” dopisz 1–2 krótkie linie (data · wersja · kto: co było → jak działa teraz). Instrukcji na górze nie ruszaj.

## Wydanie / GitHub (2026-09-17) — CZYTAJ PRZED KAŻDYM RELEASE

- 2.4.3–2.4.7 **nigdy nie trafiły na GitHub** (tylko commity). Latest zostało na 2.4.2, której tag ma ucięty `results_dialog.py` → wszyscy pobierali zepsutą wersję, auto-update też kierował na 2.4.2.
- Release = commit + push + `gh release create` z `InyfinnPhotoResizer-{v}-setup.exe` **i** `InyfinnPhotoResizer-v{v}.zip` (auto-update szuka dokładnie tej nazwy ZIP).
- Po uploadzie: pobrać oba assety z GitHuba, porównać SHA256 z lokalnymi (`gh api .../releases/latest` pole `digest`), zainstalować z pobranego setupu.
- Pliki na `D:\Marketing` bywają ucinane / podmieniane przez sync (ucięty `package_release.ps1` w commicie 2.4.7, uszkodzone `BiRefNet-*.onnx` o poprawnym rozmiarze). Przed commitem: `compileall`, parsowanie `*.ps1`, `git diff --stat`.
- `sign_file.ps1` odrzuca `HashMismatch` / `NotSigned` (setup 2 GB miał nieważny podpis, a skrypt zgłaszał sukces).

## QThread — EXE ginie bez śladu (2026-09-18, naprawione w 2.4.10)

- Objaw: aplikacja znika w trakcie pobierania aktualizacji, zero komunikatu. Zrzut w `%LOCALAPPDATA%\CrashDumps`: `Qt6Core.dll`, kod `0xC0000409`, fast-fail **7** (FATAL_APP_EXIT = qFatal/abort), wątek główny.
- Przyczyna: `finished()` QThread leci ZANIM Qt oznaczy wątek jako zakończony. Zdjęcie ostatniej referencji w slocie `finished` → `~QThread` na działającym wątku → qFatal „QThread: Destroyed while thread is still running”.
- Zasada: przed `deleteLater()` zawsze `thread.wait()`; trzymaj referencję na liście (`UpdateManager._retire_thread`, `MainWindow._retire_worker_thread`). Nie podmieniaj `wait` w testach bez `monkeypatch.undo()`.
- Diagnostyka EXE: `INYFINN_STDERR_FILE=<plik>` zapisuje stderr + faulthandler. Bez tego windowed build gubi komunikaty.
- Awaria zależała od czasu — przy szybkim łączu nie występowała. Test „raz przeszło” nic nie dowodzi.

## Test auto-update (jak robić)

- Zainstaluj starszą wersję z setupu **pobranego z GitHuba** do `%LOCALAPPDATA%\Temp\inyf-*`, opublikuj nowszą, uruchom starszą.
- Klikanie z agenta: UI Automation na Qt potrafi wywrócić proces — nie używać. `SetCursorPos` + DPI-aware (`SetProcessDpiAwarenessContext(-4)`), bezpiecznik: klik tylko gdy okno pod kursorem należy do PID aplikacji. Obok pracują Teams/Photoshop użytkownika.
- `package_release.ps1` zabija **wszystkie** procesy InyfinnPhotoResizer — uprzedź użytkownika przed buildem.

## JPEG kolor (2.4.12)

- „Wyblakła czerwień” PNG → JPG = podpróbkowanie chromy 4:2:0 (barwa wspólna dla bloku 2×2), NIE profil ICC (oba pliki bez ICC, średnie kolory identyczne). Widać na krawędziach i drobnym tekście.
- Pomiar na BANOFEE PREV: nasycenie krawędzi PNG 0,817 → 4:2:0 0,782 → 4:4:4 0,814. Plik ~2×.
- Reguła: 4:4:4 od jakości 70 (`FULL_CHROMA_MIN_QUALITY`), opcja `FormatOptions.subsampling` auto/full/reduced.
- `_post_compress` NIE koduje JPG ponownie bez `target_kb` (było 6–7 przebiegów + strata generacji). Wizki nadal wołają `compress_jpeg_file` celowo.
- Podbicie jakości do 92 przy zielonych akcentach tylko od q ≥ 70 — inaczej suwak 35/50/75 dawał ten sam plik.
- Użytkownik mówi „nie zmniejszaj grafik” — tłumacz, że 4:2:0 to parametr kodowania, wymiary zostają.

## Tryb prosty — folder zapisu (2.4.12)

- Tryb prosty ma własny `_simple_output_dir` (pusty na starcie sesji). Wcześniej dzielił pole z trybem zaawansowanym, przywracane z sesji → pliki lądowały po cichu w starym folderze.
- Okno wyników: „Zapisano w: …” + „Pokaż w folderze” (`utils/reveal.py`, Popen z DEVNULL).

## Tryb prosty — wysokości kontrolek (2.4.11)

- `CONTROL_H = 32` (pole ścieżki, Wybierz folder, Dodaj/Wyczyść), `ACTION_H = 36` (Konwertuj, PNG/JPG/AVIF). Helper `mark_large()` + QSS `[large="true"]`.
- QSS `min-height` liczy się BEZ obramowania: chip z border 2px ma w QSS 32 px, żeby wyszło 36.
- `setFixedHeight` w kodzie i `min/max-height` w QSS muszą się zgadzać — wcześniej Konwertuj miał 32 w kodzie i 36 w QSS.

## Modele usuwania tła (od 2.4.8)

- **Nie są w instalatorze** (~200 MB zamiast 2 GB; limit Inno i assetu GitHub = 2 GiB).
- `core/transforms/rmbg_models.py`: pobieranie przy pierwszym „Usuń tło” z `github.com/danielgatis/rembg/releases/download/v0.0.0`, SHA256 przypięte, wznawianie `.part`, katalog `%LOCALAPPDATA%\Inyfinn\PhotoResizer\rmbg`.
- rembg szuka `U2NET_HOME/<model>.onnx`; `MODEL_CHECKSUM_DISABLED=1`, bo inaczej przy innym MD5 po cichu pobiera 1 GB.
- `BIN/dev/tools/rmbg/BiRefNet-*.onnx` są USZKODZONE (zły SHA256) — nie używać. Dobre pliki: `birefnet-general.onnx`, `birefnet-general-lite.onnx` (`setup_rmbg_models.ps1` je weryfikuje).

## Konwersja (2026-09-17)

- Animowany GIF/WebP → GIF/WebP: `_save_animated` klatka po klatce; cwebp nie dla animacji (zostawia 1 klatkę).
- `.jp2` przez Pillow/OpenJPEG — `jpegsave` z libvips zapisywał zwykły JPEG.
- Presety sieci z FIT_BOX działają jak „cover” — ucinają 25% (3:4, 4:3) i 43,75% (16:9). Decyzja „contain” czeka na użytkownika.

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

- **Od 2.6.1: styl kolorów × tryb.** Style `zielen` („Dobra Kaloria 1 · zieleń”) i `krem` („Dobra Kaloria 2 · krem”), tryby `jasny`/`ciemny`; id `dobra-kaloria-<styl>-<tryb>`. Menu Narzędzia → Styl kolorów / Tryb, suwak = tylko tryb. Ustawienia `ui/theme_style` + `ui/theme_mode`; migracja `ui/theme_migrated_dk3` (dark → zieleń ciemna, `dobra-kaloria` → krem jasny, reszta → zieleń jasna; usuwa `ui/theme` i flagi 2.6.0). Motywy indygo usunięte. `resolve_theme()` mapuje stare nazwy.
- Kolory = `palettes.py` (kopia ról z design systemu 1.3.0, generowana skryptem z `tokens_qt.py`). `_tokens()` w `themes/__init__.py` robi z ról znaczniki QSS. Każdy motyw ma każdy znacznik (test). Tekst na akcencie = `@ON_ACCENT@` (w ciemnych ciemny, nie biały).
- **Styl DK w QSS:** przyciski domyślnie drugorzędne (ramka 2 px akcent), CTA żółte tylko: footerConvert/footerPrimary/primaryBtn/saveChoicePrimary; footerClose = link. Pola ramka 2 px `@FIELD_BORDER@`, fokus 3 px z paddingiem −1, żeby tekst się nie przesuwał. Qt rysuje 1.5 px jak 2 px. Wysokości: QSS min/max-height NIE liczy ramki ani paddingu — przy każdej zmianie ramki przelicz (np. przycisk 28 = 24 + 2×2). `ACTION_H = 44`.
- **Wersaliki / odstęp liter** — QSS ich nie zna: filtr zdarzeń `typography.py` (Polish) na etykietach z `DISPLAY_OBJECTS` / `EYEBROW_OBJECTS`. Tekst etykiet się nie zmienia. Nowy nagłówek = dodaj objectName do zbioru.
- Ikony z pliku: `check-<styl>-<tryb>.png`, `combo-down-<styl>-<tryb>.png` (generatory czytają palettes). Pliki `-light`/`-dark` (indygo) są nieużywane.
- Pytest tworzy MainWindow na prawdziwym rejestrze → uruchamia migrację motywu na tej stacji.
- Czcionki w `app/themes/fonts/`: Lato (OFL) i Mindset (licencja komercyjna firmy — user potwierdził 30.09). Spec zbiera cały katalog `themes`.
- Kolory rysowane w kodzie (QPainter: `section_icons.py`, `theme_toggle.py`, ✕ w `removable_items.py`, czcionka okna konwersji) biorą wartości z motywu (`theme_token`).
- **Ekran startowy 2.6.2** (`startup_splash.py`): rysowany ręcznie (bez QSS), wzór `WORK\src\launcher\launcher.cs` klasa Splash. Ciężki import okna + `QFontDatabase.families()` w wątku w tle (`main._boot_application`) — na stacji z ~3700 czcionkami samo wczytanie listy to ~1 s. Budowa okna (~4–5 s na tej stacji, tak samo z pustym QSS) musi być w wątku GUI → `pulse()` robi `repaint()` planszy między etapami (bez `processEvents`). Kąt kółka i pasek liczone z zegara. Zostaje jedna przerwa ~2 s w animacji. `finish()`: 100% przez 250 ms, potem plansza znika i okno się pokazuje (nigdy nad oknem). Czas startu → `startup/last_seconds` + wpis „Start programu” w activity.log.
- Zrzuty ekranu dla dowodu: tylko z okna aplikacji (`widget.grab()` / PrintWindow), NIGDY zrzut całego ekranu — obok są okna usera (edytor z prywatną rozmową trafił raz do zrzutu, plik usunięty).
- Separatory: token `@SEP@` w `app/themes`.
- **2.6.3 drabina L0–L4 + tagi (DS 1.4.0):** `palettes.py` GENEROWANY (`scripts/sync_design_tokens.py` czyta `tokens_qt.py` DS: ROLES, LADDER surface_0..4 + border_subtle_0..4, TAGS 8×(bg,border,fg)); krem-jasny = wariant `krem-jasny` DS (nie `program`). Mapowanie: okno L0, karta/pasek/dialog L1, pola+listy+tabela+zakładka L2 (`@BG_INPUT@`=`@BG_PANEL_ALT@`), co drugi wiersz / pole na zakładce L3, menu/popup/tooltip/najechanie w drzewie L4. Najechanie w rubryce L2 musi być L3/L4 — `@BG_HOVER@` (= surface-hover = L2) zlałby się z tłem. Chipy formatu i `fileProgressExt` = tagi (`setProperty("tag", format_tag(fmt))`), chip ma ramkę w kolorze tekstu tagu (ramka tagu DS za słaba na przycisk). QSS `::branch:alternate` w QTreeView NIE działa (pasek wcięcia co drugi wiersz zostaje jaśniejszy/ciemniejszy — stan z 2.6.2).
- **Kafelek Kolory (2.6.3):** sam Kolory (bez Kadru) stoi pod Tło i warianty w lewej kolumnie, Wymiary w prawej (`_relayout_bento`); treść kafelków Kolory/Wymiary do góry (addStretch). Kolory + Kadr i sam Kadr jak w 2.6.2.
- **2.6.5 wygląd „sklep” (DS 2.0.5), wzorzec = program „Stwórz prezentację” (user: „wygląda obłędnie dobrze, tak mają wyglądać Resizer i DAM”):** okno BIAŁE; szary panel L1 to JEDEN blok na ekranie (zaawansowany: „Lista plików” z podglądem w środku; prosty: strefa upuszczania = krok 1), reszta leży na bieli pod zielonymi nadtytułami (`QLabel#sectionTitle`, Lato 700, wersaliki, odstęp 0,09 em) i liniami 1 px (`QFrame#groupSep`). Kafel ma właściwość `variant` = `panel` / `plain` / `drop` (`make_tile(..., variant=)`, QSS `QFrame#bentoTile[variant=…]`). L2 (białe pola) jest JAŚNIEJSZE od L1 — mapuj rolą, nie arytmetyką; menu/listy rozwijane/podpowiedzi = rola `overlay`, nie L4. Drabina L3/L4 w QSS nie występuje.
- **Przyciski 2.6.5 (S6, S13):** żółty tylko `footerConvert` („Konwertuj”, bez wersalików); zielony główny w oknach dialogowych (`primaryBtn`, `footerPrimary`, `saveChoicePrimary`, `updateDialogAction`, `updateToastInstall`); obrysowany drugorzędny najwyżej JEDEN w grupie; reszta „cicha”: `toolBtn`, `btnUpdatePath` i `setProperty("quiet", True)` — bez ramki, tło `icon_bg` na bieli / białe na panelu (reguły zależne od przodka generuje `themes._quiet_rules`). Przycisk z samą ikoną = `iconBtn` (kwadrat z kodu). Napisy przycisków wersalikami ustawia filtr `typography.py` (wyjątki `BUTTON_NO_UPPERCASE`).
- **Pułapka: ponowne nałożenie arkusza (zmiana motywu w działającym programie).** (1) Qt przywraca widżetom czcionkę sprzed naszego `setFont` i NIE wysyła Polish ani Show — filtr typografii musi reagować też na `FontChange`, inaczej część przycisków i nadtytułów gubi wersaliki. (2) QSS wpisuje w widżet własne min/max (`#iconBtn`: min 0) i kasuje `setFixedSize` z kodu — po `apply_theme` wołaj `_square_icon_buttons()`. Zrzuty ze skryptu (`apply_theme` + `_repolish`) tego NIE pokazują; sprawdzaj klikając prawdziwy przełącznik (`QTest.mouseClick(win._theme_toggle)`), test `test_theme_toggle_keeps_uppercase_labels_and_icon_button_sizes`.
- **Pułapka: `_flush_layouts` tylko dla bieżącego widoku.** Aktywowanie układów ukrytych, pustych widżetów (nakładka konwersji) sprawia, że `QScrollArea.sizeHint()` zapamiętuje (0, 0) — lista kart zostawała na 54 px z paskiem przewijania.
- **Okno 2.6.5 (`app/window_fit.py`):** przy starcie i zmianie trybu rozmiar = potrzeba bieżącego widoku, przycięta do dostępnego obszaru ekranu (z ramką 8/31/8/8); nie mieści się → gęstość 1, 2 (odstępy 16 → 12 → 8), potem przewijanie prawego panelu ze stopką na wierzchu. Rozmiar ustawiony ręcznie: `ui/window_size_<tryb>`, honorowany tylko gdy się mieści. Zapisany podział kolumn nie wyłącza dopasowania (błąd do 2.6.4). Dowody i tabela 16 ekranów: `BIN\dev\logs\v2.6.5\B3\okno-tabela.md`.
- **Pola wyboru 2.6.5:** cały wskaźnik to obraz stanu (`icons/cb-<styl>-<tryb>-<stan>.png`, radio `rb-…`, 80×80, generator `generate_check_icons.py` z ról `check_*`), bo QSS nie narysuje obrysu 1,5 px. Po każdym `sync_design_tokens.py` uruchom oba generatory ikon. Stare `check-<styl>-<tryb>.png` i `check-light/dark.png` są nieużywane.
- **Kolory tylko przez sync:** `python scripts/sync_design_tokens.py` → `palettes.py` (ROLES, LADDER, TAGS, SHAPE). W QSS, widżetach i generatorach nie ma wartości na sztywno (wyjątki: zasłona modalna ciemnych stylów `_SCRIM`, zaznaczony wiersz w ciemnych = L4 — DS nie ma roli „zaznaczony wiersz”).
- **2.6.6 (DS 2.0.7):** wielkość liter przycisków wg S18 — WERSALIKI tylko zielony główny i jeden obrysowany; ciche, żółty „Konwertuj”, linki, ikony zwykłą wielkością. Reguła w jednym miejscu: `typography.wants_uppercase(btn)` (nazwa obiektu + właściwość `quiet` w chwili zdarzenia; filtr słucha też `DynamicPropertyChange`, przycisk, który przestał się kwalifikować, traci wersaliki). Lista plików w jasnych stylach: białe wiersze z linią 1 px zamiast pasów (`@LIST_ALT_BG@`, `@LIST_ROW_LINE@` w `_theme_tokens`). Odstęp między kolumnami: `Density.col_gap` ≥ 12 px (pion osobno). Tytuł programu w pasku trybu zaawansowanego NIE mieści się przy szerokości 1077 px — decyzja kierownika głównego: nie dodawać.
- **Testy tylko na izolowanych ustawieniach:** `tests/conftest.py` daje każdemu testowi własny plik INI (od 2.6.5). Wcześniej testy pisały do prawdziwego rejestru usera (`ui/window_size_advanced = 1280×920` z testu sprawiło, że zbudowany program otworzył się w rozmiarze z testu). Skrypty zrzutów: `capture_ui._isolate_settings()`. Stary „znany” błąd `test_segregate_checkbox` zniknął razem z izolacją.
- **Dowód po prawdziwej akcji:** zrzuty ze skryptu (`apply_theme` + repolish) ukryły usterkę zmiany motywu w 2.6.5. Stan, do którego user dochodzi kliknięciem (motyw, tryb), sprawdzaj zdarzeniem na widżecie (`QTest.mouseClick`), nie wywołaniem funkcji wewnętrznej.
- Dark/light: tokeny QSS, bez hardcoded kolorów light w dark mode.
- Dokumentacja operacyjna: **tylko** `BIN/dev/` — nigdy w korzeniu projektu.
