# Portable — później

Wersja portable będzie **rozpakowanym folderem** (EXE + `_internal`), bez one-file ~50 MB.

Po buildzie:

```powershell
powershell -File BIN\dev\scripts\package_release.ps1 -Portable
```

Wynik: `PORTABLE/InyfinnPhotoResizer/` — gotowy do skopiowania folder.
