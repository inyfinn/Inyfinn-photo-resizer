# Styling spec — QSS

Pliki: `src/inyfinn_resizer/app/themes/light.qss`, `dark.qss`

## Komponenty
| Komponent | ID / selektor | Notatki |
|-----------|---------------|---------|
| Convert CTA | `#primaryBtn` | zielony, 36px min-height |
| Listy | QListWidget, QTreeWidget | białe/ciemne tło |
| Slider quality | QSlider::handle | accent kolor |
| Progress | QProgressBar::chunk | #2d7d46 |

## Breakpointy okna (Ralph)
- 375px — wąski panel, splitter manual resize
- 768px — tablet
- 1024px — desktop pełny

## Screenshot helper
`python tests/screenshot_app.py light 1`
