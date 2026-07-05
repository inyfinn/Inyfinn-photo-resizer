# PLAN — Triage ui-complete

| Pole | Wartość |
|------|---------|
| Deliverable | Native Qt desktop app |
| Stack | Python + PySide6 + libvips |
| Ścieżka | A (nie Elementor) — QSS tokeny |
| Język UI | PL/EN mix (jak FastStone) |

## Fazy ON/OFF

| Faza | Status |
|------|--------|
| 0 Brief | ON |
| 1 Triage | ON |
| 2 Narrative | ON |
| 3 UX (MASTER.md) | ON |
| 4 Aesthetic | ON |
| 5 QSS styling | ON |
| 6 Build | ON |
| 7–8 Ralph (Qt screenshots) | ON |

## Deliverable release (faza 6)

| Plik / folder | Rola |
|---------------|------|
| `release/InyfinnPhotoResizer.exe` | Uruchomienie dwuklikiem |
| `release/InyfinnPhotoResizer.ico` | Ikona EXE i skrótu |
| `release/_internal/` | Zależności, pngquant, QSS |

Build: `build.bat` → `scripts/package_release.ps1`
