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
  `btnBrowse`, `btnUpdatePath`, `formatChip`, `saveChoiceOutline`) i link (`footerClose`, `btnLink` = Anuluj/Zamknij w oknach,
  `updateToastLater`). Napisy w Lato, nie wersalikami („Przeglądaj”). Ikony przycisków rysowane w kolorze tekstu przycisku
  (`tool_icons.py`, `section_icons.py`), po zmianie motywu odświeża je `layout_helpers.refresh_themed_icons`.
- **Ikona programu (od 2.6.2)** z design systemu Dobra Kaloria (wariant A, zielony kafelek „RE”): `dev/assets/icon.ico`
  (poprzednia: `icon-old.ico`). `generate_icon.py` nie nadpisuje istniejącej ikony.
- Aktywny motyw i czcionki trafiają do `logs/activity.log` przy każdym starcie („Motyw”).
- Kolory: `app/themes/palettes.py` (kopia ról z `tokens_qt.py` design systemu). Znaczniki:
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
