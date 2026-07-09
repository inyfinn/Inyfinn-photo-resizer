"""Proste podpowiedzi (tooltips) — wyjaśnienia jak dla początkującego."""

from __future__ import annotations

FORMAT_EXTENSION_TIPS: dict[str, str] = {
    "webp": (
        "WebP to lekki format do internetu. Zwykle daje mniejszy plik niż JPG przy podobnej jakości. "
        "Dobry na strony www i sklepy online."
    ),
    "jpeg": (
        "JPG to zdjęcie bez przezroczystości. Tło staje się jednolite (białe, czarne lub wybrane przez Ciebie). "
        "Najczęściej używany format zdjęć."
    ),
    "png": (
        "PNG zachowuje przezroczystość, jeśli była w oryginale (np. logo na przezroczystym tle). "
        "PNG-24 = pełne kolory, PNG-8 = mniejszy plik z ograniczoną paletą."
    ),
    "gif": (
        "GIF to animacje i prosta grafika z małą liczbą kolorów. "
        "Można zmniejszyć plik przez mniej kolorów, dithering (szum) lub lossy."
    ),
    "avif": (
        "AVIF to nowoczesny format internetowy — bardzo małe pliki, ale starsze przeglądarki mogą go nie otworzyć."
    ),
    "tiff": (
        "TIFF to format do druku i archiwum — duże pliki, wysoka jakość."
    ),
    "heic": (
        "HEIC to format z iPhone'a. Na Windows czasem wymaga dodatkowych kodeków."
    ),
    "bmp": (
        "BMP to stary format Windows — duży plik, bez kompresji."
    ),
}

UI_TOOLTIPS: dict[str, str] = {
    "extension": (
        "Rozszerzenie pliku wynikowego (.jpg, .png, .webp…). "
        "To nie jest wielkość obrazu — tylko typ zapisu."
    ),
    "dimension_format": (
        "Wymiary wyniku w pikselach. "
        "„Najdłuższa krawędź” — dłuższy bok ma podaną długość (np. 3000×2000 → 1200×800). "
        "„Najkrótsza krawędź” — krótszy bok ma podaną długość (np. 3000×2000 → 1800×1200). "
        "Proporcje są zawsze zachowane."
    ),
    "quality": (
        "Jakość kompresji: wyżej = ładniej i większy plik, niżej = mniejszy plik i więcej strat. "
        "50% to dobry start dla internetu."
    ),
    "scale": (
        "Skala w procentach — zmniejsza oba wymiary (np. 50%: 3000×2000 → 1500×1000). "
        "Działa po presecie Format i przed zapisem."
    ),
    "min_longest": (
        "Gdy włączone — obraz nie będzie mniejszy niż podana długość najdłuższej krawędzi. "
        "Domyślnie 1080 px (docelowy rozmiar do internetu)."
    ),
    "min_longest_px": "Minimalna długość najdłuższej krawędzi w pikselach (domyślnie 1080 px).",
    "png_colors": (
        "Ile kolorów może mieć PNG. Mniej kolorów = mniejszy plik. "
        "Przy „Z jakości” program sam dobiera liczbę z suwaka Jakość."
    ),
    "output_dir": (
        "Folder na gotowe zdjęcia. Wymaga zaznaczenia „Zapisz do folderu wyjściowego”. "
        "Bez tego program zapisuje w miejscu źródła (z pytaniem przed nadpisaniem)."
    ),
    "output_enabled": (
        "Gdy włączone — zapis do podanego folderu (lub „Przekonwertowane” obok plików). "
        "Gdy wyłączone — nadpisanie w miejscu źródłowym."
    ),
    "segregate": "Gdy zapisujesz wiele rozszerzeń naraz, każde trafia do osobnego podfolderu (np. webp/, jpg/).",
    "wiz": "Specjalna sekwencja wizualizacji produktów — kompresja w miejscu w folderze XL/L/S/SKLEP.",
    "preserve_structure": "Zachowaj podfoldery z folderu źródłowego w folderze docelowym.",
    "keep_dates": "Data modyfikacji pliku wynikowego taka jak oryginału.",
    "overwrite": "Przed nadpisaniem istniejącego pliku pokaż pytanie Tak/Nie.",
    "parallel": "Przetwarzaj kilka plików jednocześnie (szybciej na mocnym komputerze).",
    "preview": "Pokaż miniaturę i rozmiar zaznaczonego pliku.",
    "advanced": "Dodatkowe opcje: obrót, odbicia, filtry, własne skalowanie.",
    "save_custom_size": "Zapisz obecne ustawienia wymiarów jako własny preset Format.",
}
