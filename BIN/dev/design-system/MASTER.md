# Design System — Inyfinn Photo Resizer (Qt / QSS)

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
