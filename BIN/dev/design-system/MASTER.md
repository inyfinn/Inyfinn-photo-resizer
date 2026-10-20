# Design System — Inyfinn Photo Resizer (Qt / QSS)

> **Stan 2.6.7.** Kolory i kształty pochodzą z design systemu Dobra Kaloria 2.0.10 (`scripts/sync_design_tokens.py` → `palettes.py`;
> przepisy: skill `ds-dobra-kaloria`, `components.md` rozdz. 26). Tabele Light / Dark niżej to historia (motyw indygo, usunięty w 2.6.1).

## Układ okna (2.6.7)
- Okno białe (L0). Szary panel (L1) tylko tam, gdzie jest jeden blok: lista plików (tryb zaawansowany, lewa kolumna), strefa upuszczania (tryb prosty) i panel kart (prawa kolumna trybu zaawansowanego, okna Opcje zaawansowane i Ustawienia). W panelu leżą białe karty / pola (L2) — krem nigdy na szarym (S20), bez ramki w ramce (S30).
- **Tryb prosty:** strefa plików → Folder (`pole | zwykły przycisk drugorzędny`) → Format (pigułki, jeden wybór) i Jakość (własny rząd) → jeden żółty „Konwertuj”. Między częściami ~70 px (`Density.section_gap`: 70 / 48 / 28), S60.
- **Tryb zaawansowany:** karty sekcji (`SectionCard`): tytuł Mindset, akcja karty i strzałka w nagłówku, treść w siatce `etykieta | pole` (`FormGrid`, etykiety 150 px; przy wąskiej szerokości etykieta nad polem). Karta zwija się do tytułu i linii podsumowania; stan w `ui/collapsed_sections`. Stopka: „Zamknij” (obrys) i „Konwertuj” (żółty) w jednym rzędzie, 48 px (S48).
- **Pigułki** (`QPushButton[pigulka="true"]`): 40 px, zaznaczona zielona, reszta `icon-bg`, bez obrysu, bez wersalików. Jedna wartość albo kilka; „Inne” rozwija rzadsze wartości.
- **Przełącznik** (`SwitchBox`): tor 48×28, napis „Włączone / Wyłączone”; wyłączona treść karty przygaszona (nieprzezroczystość 50%).
- **Przyciski:** zielony główny i jeden drugorzędny z obrysem `btn2-border` (grey-500, S59) wersalikami; reszta cicha albo żółty „Konwertuj”; wysokości w rzędzie równe (S48).
- **Okno Ustawienia:** jedna przewijana strona z sekcjami i kotwicami (pod-zakładki z zieloną kreską 2 px); dół: „Resetuj” (cichy) | „Anuluj” (obrys), „OK” (zielony), 40 px.

## Filozofia
- Płaskie panele (`QFrame#panel`), bez ciężkich `QGroupBox`
- Strefa plików (`#dropPanel`) — najciemniejsza w dark mode
- Jedna rodzina przycisków: `btnSecondary`, `btnTool`, `primaryBtn`
- Checkboxy z widocznym checkmarkiem (`@CHECK_ICON@`)

## Light
| Token | Hex | Użycie |
|-------|-----|--------|
| bg | #f1f5f9 | tło okna |
| panel | #ffffff | panele ustawień |
| drop | #ffffff | lista plików |
| text | #0f172a | tekst |
| muted | #64748b | podpowiedzi |
| border | #e2e8f0 | obramowania |
| accent | #0ea5e9 | CTA, zaznaczenie |
| accent-violet | #6366f1 | przełącznik motywu |

## Dark (granat + fiolet)
| Token | Hex | Użycie |
|-------|-----|--------|
| bg | #0a0f1e | tło okna |
| panel | #151d33 | panel ustawień (jaśniejszy) |
| drop | #050810 | lista / drop (najciemniejszy) |
| text | #f1f5f9 | tekst |
| muted | #94a3b8 | podpowiedzi |
| border | #2d3a5c | obramowania |
| accent | #818cf8 | CTA, zaznaczenie (fiolet) |
| accent-sky | #38bdf8 | suwak, linki |

## Eksport wieloformatowy
- Checkboxy formatów (jak w skrypcie PS)
- Przy 2+ formatach: opcja segregacji do `output/webp/`, `output/jpg/` itd.
