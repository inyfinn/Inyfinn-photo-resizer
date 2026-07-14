"""Proste podpowiedzi (tooltips) — wyjaśnienia jak dla początkującego."""

from __future__ import annotations

ALPHA_OUTPUT_FORMATS = ("png", "webp", "avif")

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

FORMAT_ALPHA_TIPS: dict[str, str] = {
    "png": (
        "PNG — najpewniejszy wybór do UI, logotypów i wycięć. "
        "Pełna przezroczystość (kanał alpha) po usunięciu tła."
    ),
    "webp": (
        "WebP — obsługuje alpha (przezroczystość), zwykle mniejszy plik niż PNG. "
        "Dobry do internetu po wycięciu tła."
    ),
    "avif": (
        "AVIF — obsługuje przezroczystość i bywa jeszcze lżejszy wagowo, "
        "ale nie wszędzie jest tak wygodny jak PNG/WebP."
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
        "Ile kolorów może mieć obraz z paletą (PNG-8, GIF itd.). Mniej kolorów = mniejszy plik. "
        "Przy „Z jakości” program sam dobiera liczbę z suwaka Jakość."
    ),
    "color_count": (
        "Maksymalna liczba kolorów w palecie (PNG-8, GIF i inne formaty indeksowane). "
        "Mniej = mniejszy plik. „Z jakości” — auto z suwaka Jakość."
    ),
    "output_dir": (
        "Folder na gotowe zdjęcia. Zaznacz „Zapisz do folderu wyjściowego”, "
        "potem kliknij „Aktualizuj ścieżkę” (folder Przekonwertowane obok zdjęć) "
        "lub „Przeglądaj”, aby wybrać inny folder."
    ),
    "output_update_path": (
        "Ustawia folder wyjściowy na „Przekonwertowane” obok dodanych zdjęć. "
        "Przykład: zdjęcie z Pulpitu → Pulpit\\Przekonwertowane. "
        "Przy zaznaczonym pliku na liście bierze folder tego pliku."
    ),
    "output_enabled": (
        "Gdy włączone — zapis do podanego folderu. "
        "Gdy wyłączone — nadpisanie w miejscu źródłowym (z pytaniem przed nadpisaniem)."
    ),
    "segregate": "Gdy zapisujesz wiele rozszerzeń naraz, każde trafia do osobnego podfolderu (np. webp/, jpg/).",
    "remove_background": (
        "Usuwa tło produktu (AI BiRefNet). Wynik ma przezroczystość — wybierz PNG, WebP lub AVIF.\n\n"
        "Tryb obok:\n"
        "• Najlepsza jakość — dokładniejsze krawędzie, wolniejszy (zalecany do finalnego eksportu).\n"
        "• Szybko — krótszy czas, dobry do testów i dużych partii."
    ),
    "bg_model_combo": (
        "Model AI do wycinania tła. Domyślnie: Najlepsza jakość.\n"
        "Szybko — gdy liczy się czas; Najlepsza jakość — gdy liczy się precyzja wycięcia."
    ),
    "bg_model_general": (
        "Najlepsza jakość — model BiRefNet General (~950 MB). "
        "Najdokładniejsze wycięcie produktu, włoski i cienie na krawędzi. "
        "Wolniejszy, ale zalecany do finalnego eksportu do sklepu."
    ),
    "bg_model_lite": (
        "Szybko — model BiRefNet Lite (~220 MB). "
        "Około 2–3× szybszy niż Najlepsza jakość. Dobry do szybkiego podglądu i dużych partii. "
        "Gdy produkt źle oddziela się od tła, przełącz na Najlepsza jakość."
    ),
    "bg_fast_conversion_hint": (
        "Tryb Szybko: jeśli produkt źle oddzieli się od tła (postrzępione lub obcięte krawędzie), "
        "przerwij konwersję i powtórz z opcją „Najlepsza jakość”."
    ),
    "wiz": "Specjalna sekwencja wizualizacji produktów — kompresja w miejscu w folderze XL/L/S/SKLEP.",
    "preserve_structure": "Zachowaj podfoldery z folderu źródłowego w folderze docelowym.",
    "keep_dates": "Data modyfikacji pliku wynikowego taka jak oryginału.",
    "overwrite": "Przed nadpisaniem istniejącego pliku pokaż pytanie Tak/Nie.",
    "parallel": (
        "Równoległe przetwarzanie wątkami — kilka plików naraz na jednym CPU. "
        "Przyspiesza batch na mocnym PC; wyłącz, gdy chcesz mniejsze obciążenie lub stabilniejszą kolejność."
    ),
    "gif_mode_quality": (
        "Kompresja jakości — stała liczba klatek (2 z każdych 3), zmiana kolorów i lossy. "
        "Timing animacji zachowany."
    ),
    "gif_mode_frames": (
        "Redukcja klatek — mniej klatek bez utraty jakości obrazu. "
        "Czas każdej klatki proporcjonalny do pominiętych — pauzy i zamrożenia zachowane."
    ),
    "gif_mode_ultra": (
        "ULTRA — maks. 4 klatki: najdłużej zamrożone bloki + ostatnia klatka. "
        "Najmniejszy plik, widoczna redukcja animacji."
    ),
    "gif_level": "Poziom 1–10: wyżej = lepsza jakość / więcej klatek, niżej = mniejszy plik.",
    "preview": "Pokaż miniaturę i rozmiar zaznaczonego pliku.",
    "advanced": "Dodatkowe opcje: obrót, odbicia, filtry, własne skalowanie.",
    "save_custom_size": "Zapisz obecne ustawienia wymiarów jako własny preset Format.",
}
