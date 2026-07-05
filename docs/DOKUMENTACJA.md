# Inyfinn Photo Resizer — dokumentacja użytkownika

## Co robi program

Inyfinn Photo Resizer to natywna aplikacja Windows do **wsadowej konwersji i kompresji zdjęć**. Obsługuje m.in. WebP, AVIF, HEIC, PNG (pngquant), JPEG i GIF.

Interfejs jest **w całości po polsku**.

## Instalacja

1. Pobierz `InyfinnPhotoResizer-1.0.0-setup.exe` z [GitHub Releases](https://github.com/inyfinn/Inyfinn-photo-resizer/releases).
2. Uruchom kreator instalacji.
3. Program pojawi się w menu Start (opcjonalnie skrót na pulpicie).

Wersja portable: folder z `InyfinnPhotoResizer.exe` i podfolderem `_internal` (nie rozdzielaj ich).

## Szybki start

1. Uruchom program.
2. Przeciągnij zdjęcia na listę po lewej lub użyj **Dodaj pliki** / **Dodaj folder**.
3. Wybierz **format(y)** z rozwijanej listy (wielokrotny wybór jak w FastStone).
4. Ustaw **rozmiar**, **jakość** i folder **Wyjście**.
5. Kliknij **Konwertuj**.

Opcje wsadowe i podgląd są w zwiniętej sekcji **Więcej opcji**.

## Format wyjściowy

- Lista rozwijana z checkboxami — możesz zaznaczyć kilka formatów naraz.
- Przy wielu formatach włącz **Segreguj do podfolderów** (`webp/`, `jpg/` itd.).
- **Ustawienia…** otwiera opcje JPEG/PNG/WebP/AVIF/GIF (EXIF, progressive, bezstratny).

## Kompresja

| Format | Silnik | Uwagi |
|--------|--------|-------|
| JPEG | libvips | Jakość suwakiem 0–100 |
| PNG | pngquant + oxipng | Silna redukcja rozmiaru |
| WebP | libvips | Domyślny format |
| AVIF / HEIC | libvips | Wymaga bibliotek w buildzie |
| GIF | gifsicle (opcjonalnie) | |

### Wyniki testów kompresji (fixture IMG_0113.jpg, ~3,7 MB)

| Format | Jakość | Wynik | Stosunek do źródła |
|--------|--------|-------|---------------------|
| WebP | 85 | ~804 KB | ~22% |
| JPEG | 75/50/35 | mniejszy od źródła | tak |
| PNG | 50 | wyraźnie mniejszy (pngquant) | < 40% |

Wszystkie 12 testów automatycznych (`pytest tests/test_convert.py`) przechodzą.

## Motywy

- **Jasny** — domyślny, wysoki kontrast.
- **Ciemny** — granat + fiolet, ten sam motyw w oknach dialogowych.
- Przełącznik: przycisk w nagłówku lub menu **Motyw**.

## CLI (bez GUI)

```powershell
cd dev
python -m inyfinn_resizer.cli convert -i ścieżka\zdjęcie.jpg -o folder\wyjściowy -f webp -q 85 --overwrite
```

## Budowanie ze źródeł

```powershell
.\build.bat
```

Instalator (Inno Setup):

```powershell
iscc dev\installer\inyfinn_resizer.iss
```

## Wsparcie

Repozytorium: https://github.com/inyfinn/Inyfinn-photo-resizer
