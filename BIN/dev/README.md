# Inyfinn Photo Resizer — dokumentacja deweloperska

Natywna aplikacja Windows (Python 3.12 · PySide6 · libvips · pngquant · gifsicle).  
**Wersja:** 2.6.8 · **Korzeń projektu:** wyłącznie `InyfinnPhotoResizer.exe` (launcher).

Dokumentacja i logi są **tylko tutaj** (`BIN/dev/`), nie w korzeniu.

---

## Uruchomienie

| Tryb | Jak |
|------|-----|
| Produkcja | Dwuklik `InyfinnPhotoResizer.exe` w korzeniu → startuje `BIN\` |
| Dev | `pip install -e ".[dev]"` → `inyfinn-photo-resizer` |

---

## Lista rozszerzeń (`FormatMultiCombo`) — poprawka 20.10.2026, do wydania po 2.6.6

Zgłoszenie: „wybieranie rozszerzeń z listy rozwijanej jest trudne, bo zwija się od razu”.

- **Przyczyna:** zwykły klik w format wybierał TYLKO ten format i zamykał listę; kilka formatów dało się zaznaczyć wyłącznie z Ctrl albo trafiając w sam kwadrat pola wyboru.
- **Teraz:** każdy klik zaznacza albo odznacza format, lista zostaje otwarta; Shift zaznacza zakres; listę zamyka klik obok albo Esc. Ostatniego formatu nie da się odznaczyć.
- **Puszczenie przycisku**, które przychodzi do listy bez wciśnięcia w niej (klik, który ją otworzył), jest pomijane — nie zamyka listy i nie zmienia wyboru.
- Kod: `src/inyfinn_resizer/app/widgets/format_multi_combo.py` (filtr zdarzeń na `view().viewport()`, flagi `_press_in_popup`, `_swallow_release`). Test: `tests/test_format_combo_popup.py` (prawdziwe okno Qt, nie `offscreen` — na `offscreen` lista się nie otwiera).
- Od 2.6.7 rozszerzenia w trybie zaawansowanym to pigułki (poniżej); `FormatMultiCombo` zostaje w kodzie razem z poprawką i testem, ale okno główne go już nie używa.

## Zapis jawnie, białe pole na pliki, GIF bez wyszarzonych pól — 2.6.8

Słowa usera z 20.10.2026 po 2.6.7 (panel „toporny”, liczenie klatek niezrozumiałe, w GIF-ach „nie da się kliknąć”, za mało oddechu, jedna wielka beżowa ramka na pliki, program nie mówi, czy nadpisze, w opisach jakiś „CNOV”). Reguły design systemu: S79–S83 (`ZALECENIA-USERA.md`).

- **Białe pole na pliki (S79).** Tryb prosty: kafelek plików to zwykły panel L1 (`variant="panel"`; nagłówek, przyciski, licznik), a miejsce na pliki to `QFrame#dropField` (L2, przerywana ramka `DROP_BORDER`, promień `RADIUS_DROP`) z pustym stanem albo listą. Wiersze listy: białe, linia 1 px `LIST_ROW_LINE` (te same tokeny co lista trybu zaawansowanego), bez odstępów. Kwadrat ikony pustego stanu ma `BG_PANEL`, żeby było go widać na bieli. Upuszczanie obsługuje nadal okno (`dropEvent`). Wariant `drop` kafelka zostaje w QSS i w `make_tile`, ale nic go już nie używa.
- **Oddech (S80).** Odstęp między wierszami formularzy trybu prostego 12 → 20 px (`main_window.SIMPLE_ROW_GAP` = 20 / 16 / 12 wg gęstości okna, więc niski ekran nadal się zagęszcza); opis kafelka 6 px pod tytułem (`TILE_TITLE_HINT_GAP`). `Density.section_gap` (70) bez zmian. Wysokość trybu prostego liczy się przy szerokości, jaką okno naprawdę dostanie (`_measure_w`), bo zdania pod polami zawijają się w wąskim oknie.
- **Zapis jawnie (S82, S83).** `app/save_conflicts.py` (czysta logika): zdania pod polem „Folder” (tryb prosty: `saveInfo`, odświeżane przy zmianie folderu i kolejki; tryb zaawansowany: karta „Zapis plików”, odświeżane przełącznikami „Zapisz do folderu wyjściowego” i „Pytaj przed nadpisaniem”), wykrywanie zajętych celów (istnieją na dysku albo powtarzają się w partii), nazwy z dopiskiem przez `core.pipeline.unique_conv_path` (nazwy unikalne także w partii). `dialogs/simple_save_dialog.SaveConflictDialog` / `ask_save_conflict` zwraca `"suffix"`, `"overwrite"` albo `None`; „Zapisz obok z dopiskiem” jest domyślne (Enter).
  - Tryb prosty: bez bezwarunkowego pytania. Cel = wybrany folder albo obok oryginału z rozszerzeniem formatu wyjściowego; pytanie tylko przy zajętych nazwach (np. „Jak oryginał” bez folderu, folder = folder zdjęć).
  - Tryb zaawansowany: jedno pytanie o całą partię zamiast `ask_overwrite_inplace` na każdy plik i okna Tak/Nie; bez folderu wyjściowego pytamy zawsze, z folderem tylko przy „Pytaj przed nadpisaniem” (bez niego nadpisanie po cichu jak dotąd). Sekwencja wizek bez zmian.
  - W opisach programu nie ma już `_conv` („z dopiskiem w nazwie”); w rdzeniu plik nadal dostaje `_conv`.
- **GIF (S81).** Okno „Ustawienia…”: sposób wybierany pigułkami „Jakość / Mniej klatek / ULTRA” (`PillGroup`), pod nimi jedno zdanie o skutku; widoczne są tylko pola wybranego sposobu (`FormGrid.set_row_visible`), nic nie jest wyszarzone. Jakość: „Lossy i kolory z suwaka Jakość” + linia „Teraz: …” (ręczny lossy 0–200 dopiero po odznaczeniu); Mniej klatek: lista „Zostaw klatek” (`FRAME_PRESETS` 10 → 1, wartość = `gif_level`); ULTRA: „Najwyżej klatek” 2–8 i „Lossy” 0–200. Film → GIF: pigułki „Płynnie / ULTRA”; Płynnie = „Klatki na sekundę” + „Najwięcej klatek” (bezpiecznik), ULTRA = „Liczba zatrzymań”. W trybie prostym rząd Film → GIF to te same dwie pigułki i JEDNO pole liczbowe z jawną etykietą („Klatki na sekundę” / „Liczba zatrzymań”).
- **Poprawka rdzenia.** `compress_gif`, sposób „Jakość”: własne kolory i lossy działają zawsze, gdy podano kolory (lossy 0 = bez lossy); dawniej `lossy == 0` po cichu wracało do presetu poziomu (256 kolorów, lossy 80).
- **Testy:** `tests/test_save_flow_268.py` (zdania o zapisie, zajęte nazwy, przepływy trybu prostego i zaawansowanego, `dropField`, oddech, GIF, `compress_gif`), przepisane `tests/test_simple_save_dialog.py`, poprawione `test_simple_video.py`, `test_window_fit.py`, `test_look_267.py`. **Zrzuty:** `scripts\capture_ui.py <iteracja> <folder> <motywy> v268`.

## Nowy wygląd czterech części — 2.6.7

Wybór usera z rundy `/design` 20.10.2026 (strona wyboru wariantów z opisami; wybrane: 1D, 2B+C, 3D, 4B). Design system Dobra Kaloria 2.0.10 (`scripts\sync_design_tokens.py`, potem oba generatory ikon); przepisy: `components.md` rozdz. 26, reguły S20, S30, S37, S48, S59, S60.

**1. Tryb prosty (wariant D).** Pliki (strefa upuszczania z przyciskami w nagłówku) → Folder (`pole + zwykły przycisk „Wybierz folder…”` w jednym rzędzie, także w wąskim oknie) → Format (pigułki jeden wybór: Jak oryginał / PNG / JPG / AVIF / WebP) i Jakość (własny rząd: etykieta, suwak, liczba) → jeden żółty „Konwertuj”. Między częściami ok. 70 px (`Density.section_gap` 70 → 48 → 28 px przy niskim ekranie, S60). Format wybierasz PRZED „Konwertuj”: pigułka niczego nie uruchamia (dawne kafle konwertowały od razu). Mechanika bez zmian: lista plików, Film → GIF, folder zapisu, pytanie nadpisać / `_conv`. Kod: `main_window._build_simple_view`, `_simple_target_format`.

**2. Tryb zaawansowany (B + C).** Prawa kolumna = szary panel (`QFrame#cardPanel`) z białymi kartami sekcji (`widgets/section_card.py`): Format i jakość („Ustawienia…” w nagłówku) | Tło i warianty | Wymiary | Zapis plików. Wiersze `etykieta | pole` w `widgets/form_grid.FormGrid` (przy wąskiej szerokości etykieta nad polem). „Liczba kolorów” (PNG / GIF) i „Kadr” to wiersze kart, widoczne tylko gdy mają sens (`_sync_conditional_rows`). Przyciski listy plików w siatce 2×2, „Zamknij” (obrys) i „Konwertuj” w jednym rzędzie, ta sama wysokość.
- **Zwijanie:** klik w nagłówek karty (albo strzałkę) zwija ją do tytułu i jednej linii podsumowania (`SectionCard.set_summary`, odświeżane przy każdej zmianie kontrolek). Stan w ustawieniach użytkownika: `ui/collapsed_sections` (lista kluczy `format`, `background`, `dimensions`, `save`), zapisywany od razu; domyślnie wszystko rozwinięte.
- **Rozszerzenia:** `widgets/pills.FormatPills` — pigułki wielokrotnego wyboru z tym samym interfejsem co `FormatMultiCombo` (`selected_formats`, `set_selected`, `apply_format_state`, `set_alpha_only_mode`, `first_selected`, `selectionChanged`), więc sesja, presety i usuwanie tła (tryb „tylko z przezroczystością”: pigułki bez alfa wyłączone) działają jak dotąd. Pierwszy rząd: PNG, JPG, WebP, AVIF, GIF i „Inne”; drugi rząd (TIFF, HEIC, BMP, JPEG 2000, PDF) pod „Inne” — zaznaczony rzadki format sam go rozwija i nie da się go ukryć. Co najmniej jeden format zostaje zawsze zaznaczony.

**3. Okno „Ustawienia…” (wariant D).** Jedna przewijana strona z sekcjami JPEG / PNG / WebP / AVIF / GIF / Zaawansowane (szary panel, tytuł Mindset, opis formatu u góry, siatka etykieta | pole) i rzędem kotwic u góry (klik przewija do sekcji, przewijanie przełącza aktywną kotwicę). Okno otwiera się na sekcji formatu wybranego w głównym oknie. Dół: „Resetuj” | „Anuluj”, „OK”. Mechanika opcji (`get_options`, `get_resize`, `get_transforms`, reset) bez zmian — zmienił się tylko układ.

**4. Okno „Opcje zaawansowane” (wariant B).** `AdvancedSettingsPanel` (wspólny dla okna „Opcje zaawansowane”, sekcji Zaawansowane i okna zapisu własnego presetu): białe karty na szarym tle. „Włącz…” to przełącznik DS w nagłówku karty (`widgets/switch.SwitchBox`, nadal `QCheckBox`: `resize_enable`, `crop_enable`); wyłączona treść jest przygaszona i nieaktywna. W karcie Kadrowanie przełącznik dotyczy prostokąta (X, Y, szerokość, wysokość); „Kadruj do przezroczystych pikseli”, margines i „Zachowaj proporcje” działają niezależnie, jak dotąd.

**5. Obrysy przycisków (S59).** Obrys przycisku drugorzędnego to token `btn2-border` (grey-500 `#868E96` w stylach jasnych, DS 2.0.10), nie `#222222`; tekst zostaje ciemny. Nic na sztywno w QSS.

**6. Responsywność.** Minimum okna wynika z treści (ok. 900–910 px zamiast dawnych 1180); siatki przestawiają się przy wąskiej szerokości (`FormGrid`, `SplitRow`, `ActionRow`: próg = minimum układu szerokiego, więc dzieci nigdy nie są ściskane). Etykieta „Presety” w pasku u góry ustępuje pierwsza, gdy brakuje miejsca. `window_fit.py` nadal dopasowuje okno do ekranu (poziomy gęstości 0–2). Układ w jednej kolumnie kart jest wyższy od dawnego dwukolumnowego: pełny (wszystkie karty rozwinięte) potrzebuje ok. 1170 px (AVIF) / 1210 px (PNG z wierszem „Liczba kolorów”) na poziomie 0, 1067 / 1105 na poziomie 1 i 993 / 1029 na poziomie 2; na niższym ekranie prawy panel przewija się ze stopką na wierzchu, a zwinięcie kart skraca go. Przy wąskim oknie (etykiety nad polami) panel jest jeszcze wyższy i też się przewija.

**Skutek uboczny tokenów 2.0.10.** Zebra ciemnych stylów = L2 (tło listy), więc pasów w ciemnych nie ma; lista plików ma w obu trybach białe wiersze rozdzielone linią 1 px (`LIST_ALT_BG`, `LIST_ROW_LINE`).

**Testy:** `tests/test_look_267.py` (pigułki, 70 px, przycisk folderu, rząd jakości, zwijanie i zapamiętanie, przełączniki, okno Ustawienia, 960 px), `tests/test_bento_colors_tile.py` (wiersze warunkowe). **Zrzuty:** `scripts\capture_ui.py <iteracja> <folder> <motywy> v267`.

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
