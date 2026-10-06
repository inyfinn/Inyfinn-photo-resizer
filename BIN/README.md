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

## Wygląd (od 2.6.0): design Dobra Kaloria

Zmieniamy design na ten, który ma program do tworzenia prezentacji „Stwórz prezentację”
(design system Dobra Kaloria). Od 2.6.1 cały program ma ten styl, nie tylko kolory:

- **Nagłówki** kafelków i okien: czcionka **Mindset** wielkimi literami (licencja komercyjna firmy,
  potwierdzona przez właściciela projektu 30.09.2026). **Tekst:** Lato (OFL). Małe etykiety sekcji:
  Lato Bold wersalikami z odstępem liter. Obie czcionki są w paczce (`app/themes/fonts/`).
- **Przyciski:** główna akcja żółta (#FFD42A, brązowy tekst, 44 px, jedna na ekran), drugorzędne
  z zieloną ramką i zielonym tekstem (hover = miękkie wypełnienie), „Zamknij” jako podkreślony link.
- **Pola** z ramką w kolorze `field-border`, fokus 3 px w kolorze akcentu (tekst się nie przesuwa),
  zaokrąglenia 4 / 8 / 12 px, karty z cienką ramką.
- **Dwa niezależne wybory:** styl kolorów (menu **Narzędzia → Styl kolorów**: „Dobra Kaloria 1 · zieleń”,
  „Dobra Kaloria 2 · krem”) i tryb (suwak słońce/księżyc, też **Narzędzia → Tryb**). Cztery motywy
  `dobra-kaloria-<zielen|krem>-<jasny|ciemny>` = `themes-list` z design systemu 1.3.0.
  Ustawienia: `ui/theme_style`, `ui/theme_mode`.
- **Migracja** (raz, flaga `ui/theme_migrated_dk3`) zachowuje to, co user widzi: `dark` /
  `dobra-kaloria-ciemny` → zieleń ciemna, `dobra-kaloria` (kremowy z 2.6.0) → krem jasny, brak / `light` /
  inne → zieleń jasna. Stare klucze (`ui/theme` i flagi 2.6.0) są usuwane. Motywy indygo usunięte.
- **Ekran startowy (od 2.6.2)** taki sam jak w programie „Stwórz prezentację” 1.1.2: 560×330, zieleń
  #0F763E, białe logo, „INYFINN PHOTO RESIZER” czcionką Mindset, kółko ładowania, „Uruchamiam program…”,
  „zostało ok. N s” i żółty pasek (92% w przewidywanym czasie, potem powoli). Czas = poprzedni start
  (`startup/last_seconds`), pierwszy raz 6 s / 15 s z dysku sieciowego. Kod: `app/widgets/startup_splash.py`.
- **Przyciski (od 2.6.2)** trzy rodziny w całym programie: główny żółty (`footerConvert`, `primaryBtn`, `saveChoicePrimary`,
  `updateDialogAction`, `updateToastInstall`, `updateStatusInstall`), drugorzędny z ramką w kolorze akcentu (`btnSecondary`, `toolBtn`,
  `btnBrowse`, `btnUpdatePath`, `saveChoiceOutline`; `formatChip` od 2.6.3 = tag) i link (`footerClose`, `btnLink` = Anuluj/Zamknij w oknach,
  `updateToastLater`). Napisy w Lato, nie wersalikami („Przeglądaj”). Ikony przycisków rysowane w kolorze tekstu przycisku
  (`tool_icons.py`, `section_icons.py`), po zmianie motywu odświeża je `layout_helpers.refresh_themed_icons`.
- **Ikona programu (od 2.6.2)** z design systemu Dobra Kaloria (wariant A, zielony kafelek „RE”): `dev/assets/icon.ico`
  (poprzednia: `icon-old.ico`). `generate_icon.py` nie nadpisuje istniejącej ikony.
- Aktywny motyw i czcionki trafiają do `logs/activity.log` przy każdym starcie („Motyw”).
- **Drabina powierzchni (od 2.6.3, design system 1.4.0):** L0 tło okna → L1 karta, pasek menu, okno dialogu →
  L2 rubryka (pola, lista plików, strefa upuszczania, tabela wyników, podgląd, zakładka okna Ustawienia, karta pliku
  w oknie konwersji) → L3 element w rubryce (co drugi wiersz, pole na zakładce, najechanie w liście) → L4 nakładka
  (menu, rozwinięta lista, podpowiedź, najechanie w drzewie plików). Jasny: głębiej = ciemniej, ciemny: głębiej =
  jaśniej, bez czystej bieli. Znaczniki `@BG_WINDOW@`, `@BG_PANEL@`, `@BG_INPUT@`/`@BG_PANEL_ALT@`, `@BG_L3@`, `@BG_L4@`.
- **Skala tekstu i odstępy programu (od 2.6.4, design system 1.5.0, tokeny `qt.*`):** jasne style = biała kartka L0
  `#FFFFFF` i kremowe karty L1 `#FDF8ED` jak w programie „Stwórz prezentację”; ramka karty 1 px w roli `border`
  (`@CARD_BORDER@`, nie `border-strong`). Tekst 15 px (`themes._FONT_PIXEL_SIZE`), etykiety/podpowiedzi 14 px,
  nagłówki kart Mindset 22 px; pola 40 px z ramką 1 px (fokus 2 px), przyciski 40 px, „Konwertuj” i chipy 48 px.
  Stałe w `widgets/layout_helpers.py` (CONTROL_H 40, ACTION_H 48, SECTION_GAP 12, TILE_PADDING 20). Okno min.
  1180×700; tryb prosty w `QScrollArea#simpleScroll` (na 1366×768 przewija się zamiast ściskać listę).
- **Tagi (od 2.6.3):** chipy formatu PNG/JPG/AVIF w trybie prostym i znaczniki rozszerzenia w oknie konwersji mają
  kolory tagów design systemu (`@TAG<n>_BG@/_BORDER@/_FG@`, odcień stylu ±12°/±24°…); numer tagu formatu:
  `themes.format_tag()` (PNG 1, JPG 2, AVIF 3, WebP 4, GIF 5, TIFF 6).
- **Okno „Nie wybrano folderu zapisu” (od 2.6.3):** „Zapisz jako nowe (_conv)” = `saveChoicePrimary` i Enter
  (od 2.6.5 zielony, nie żółty), „Nadpisz oryginały” = `saveChoiceOutline`.
- **Wygląd „sklep” (od 2.6.5, design system 2.0.5; zastępuje opisy drabiny i skali z 2.6.3–2.6.4 powyżej tam, gdzie
  się różnią):** wzorzec to sklep dobrakaloria.pl i program „Stwórz prezentację”. Okno białe (L0), tekst `#222222`,
  ciemna zieleń `#00642E` w tytule programu i nadtytułach. Szary panel L1 `#F8F7F5` (krem: ecru `#FDF8EC`) to jeden
  blok na ekranie: „Lista plików” (tryb zaawansowany, z podglądem w środku) albo strefa upuszczania (tryb prosty,
  ramka przerywana 1 px). Pozostałe grupy leżą na bieli pod nadtytułami `QLabel#sectionTitle`, rozdzielone liniami
  `QFrame#groupSep`. Kafel: `make_tile(..., variant="panel" | "plain" | "drop")` → QSS `QFrame#bentoTile[variant=…]`.
  Pola białe z ramką 1 px `#868E96`, promień 4; panel/karta promień 8. L2 jest jaśniejsze od L1; menu, listy
  rozwijane i podpowiedzi = rola `overlay`. Poziomy L3/L4 nie są używane.
- **Przyciski (od 2.6.5):** żółty tylko „Konwertuj” (`footerConvert`); zielony główny w oknach dialogowych; obrysowany
  drugorzędny najwyżej jeden w grupie; pozostałe „ciche” (bez ramki): `toolBtn`, `btnUpdatePath`, właściwość
  `quiet=true`; przycisk z samą ikoną `iconBtn`. Wielkość liter ustawia `themes/typography.py`: od 2.6.6 (DS 2.0.6,
  S18) WERSALIKI tylko na zielonym głównym i na jednym obrysowanym; ciche, żółty „Konwertuj”, linki i przyciski-ikony
  zwykłą wielkością liter — jedna reguła `typography.wants_uppercase(btn)`, liczona z bieżącego stanu przycisku.
- **Od 2.6.6:** lista plików w jasnych stylach bez pasów — białe wiersze z linią 1 px (`@LIST_ALT_BG@`,
  `@LIST_ROW_LINE@`; ciemne style zostają przy pasach, tabela wyników też); sekcje przewodnika bez ramek, rozdzielone
  `groupSep`; odstęp między kolumnami `Density.col_gap` ≥ 12 px na każdym poziomie gęstości (pion bez zmian);
  kolumna „Lp.” w wynikach 44 px; ścieżka w podglądzie łamie się po separatorze (`layout_helpers.breakable_path`);
  tagi ciemnych stylów z DS 2.0.7.
- **Tagi (od 2.6.5):** osiem różnych barw, samo wypełnienie bez ramki; `themes.format_tag()`: PNG 1, JPG 4, AVIF 8,
  WebP 3, GIF 5, TIFF 6, JP2/HEIC 7, inne 2.
- **Pola wyboru (od 2.6.5):** obrazy stanów `themes/icons/cb-*.png`, `rb-*.png` (jasne wnętrze, obrys 1,5 px, ptaszek);
  po `scripts/sync_design_tokens.py` uruchom `generate_check_icons.py` i `generate_combo_icons.py`.
- **Okno a ekran (od 2.6.5):** `app/window_fit.py` — przy starcie i zmianie trybu okno ma rozmiar potrzebny bieżącemu
  widokowi, nigdy większy niż dostępny obszar ekranu; gdy treść się nie mieści: odstępy 16 → 12 → 8, potem przewijanie
  prawego panelu (stopka z „Konwertuj” zostaje). Rozmiar ustawiony ręcznie pamiętany osobno dla trybu
  (`ui/window_size_simple`, `ui/window_size_advanced`). Odstęp między kartami: `CARD_GAP = 16`.
- Kolory: `app/themes/palettes.py` — PLIK GENEROWANY z `tokens_qt.py` design systemu:
  `python scripts/sync_design_tokens.py` (role, drabina L0–L4, tagi). Znaczniki:
  `app/themes/__init__.py`, arkusz: `app/themes/app.qss`, wersaliki: `app/themes/typography.py`.
  Zmiana dotyczy tylko wyglądu, nie funkcji.

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
