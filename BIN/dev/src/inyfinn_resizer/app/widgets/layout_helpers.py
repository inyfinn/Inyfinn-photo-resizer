"""Pomocniki układu — siatka i sekcje jak CSS Grid / Flex."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

BTN_H = 36
FOOTER_BTN_H = 40
# Tryb prosty: dwie wysokości zamiast pięciu — kontrolki (pole, przeglądaj, dodaj) i akcje (Konwertuj, formaty).
CONTROL_H = 40
ACTION_H = 48  # design system Dobra Kaloria 1.5.0: qt.control-h-primary
ROW_GAP = 10
FIELD_GAP = 6
SECTION_GAP = 12  # odstępy sekcji w oknach dialogowych (changelog, przewodnik) — bez zmian od 2.6.4
# 2.6.5: jeden odstęp między kartami okna głównego (lewa↔prawa kolumna, karty w kolumnie, tryb prosty).
# To poziom 0 gęstości z window_fit.DENSITIES; przy niskim ekranie program zmniejsza go do 12, potem 8.
CARD_GAP = 16
TILE_PADDING = 20
TILE_PADDING_TOP = TILE_PADDING - 4  # nagłówki 8 px wyżej w kafelku
TILE_HEADER_SPACING = 10
TILE_INNER_SPACING = 10
TILE_TITLE_HEIGHT = 26
CROP_PICKER_HEIGHT = 90
STEP_ICON_SIZE = 28
COMPACT_LABEL_W = 100
COMPACT_SLIDER_ROW_H = 36
COMPACT_CONTROL_ROW_H = 40
# Lista plików w trybie zaawansowanym: nagłówek + ok. 5 wierszy, żeby przy niskim ekranie nie zniknęła.
LIST_MIN_H = 170
LIST_MIN_H_TIGHT = 90  # ostateczność: ekran niższy niż układ potrzebuje nawet przy najmniejszych odstępach


def hint_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hintLabel")
    lbl.setWordWrap(True)
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    return lbl


def field_label(text: str, tooltip: str = "") -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    if tooltip:
        lbl.setToolTip(tooltip)
    return lbl


def field_group(label: str, control: QWidget, hint: str = "") -> QWidget:
    """Etykieta + kontrolka; podpowiedź tylko w tooltipie."""
    wrap = QWidget()
    wrap.setObjectName("fieldGroup")
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(FIELD_GAP)
    lbl = field_label(label, hint)
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if hint:
        control.setToolTip(hint)
    lay.addWidget(lbl)
    lay.addWidget(control)
    return wrap


def compact_row(
    label: str,
    control: QWidget,
    *,
    tooltip: str = "",
    tight: bool = False,
    height: int | None = None,
) -> QWidget:
    """Jeden wiersz: etykieta | kontrolka (kompaktowy formularz)."""
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    row.setAlignment(Qt.AlignVCenter)
    lbl = field_label(label, tooltip)
    lbl.setMinimumWidth(COMPACT_LABEL_W)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    if tooltip:
        control.setToolTip(tooltip)
    row.addWidget(lbl, 0, Qt.AlignVCenter)
    row.addWidget(control, stretch=1, alignment=Qt.AlignVCenter)
    row_h = height
    if row_h is None and tight:
        row_h = COMPACT_SLIDER_ROW_H
    if row_h is not None:
        wrap.setMinimumHeight(row_h)
    return wrap


def slider_control(
    slider: QSlider,
    value_label: QLabel,
    *,
    value_width: int = 36,
    tooltip: str = "",
) -> QWidget:
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    value_label.setObjectName("qualityValue")
    value_label.setMinimumWidth(value_width)
    value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    slider.setMinimumHeight(20)
    slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if tooltip:
        slider.setToolTip(tooltip)
        value_label.setToolTip(tooltip)
    row.addWidget(slider, stretch=1)
    row.addWidget(value_label)
    return wrap


def make_section(title: str, tooltip: str = "") -> tuple[QFrame, QVBoxLayout]:
    box = QFrame()
    box.setObjectName("sectionBox")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(8, 4, 8, 6)
    lay.setSpacing(4)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    if tooltip:
        hdr.setToolTip(tooltip)
        box.setToolTip(tooltip)
    lay.addWidget(hdr)
    return box, lay


def stacked_field(label: str, control: QWidget, *, tooltip: str = "") -> QWidget:
    """Etykieta nad kontrolką (siatka 2-kolumnowa)."""
    wrap = QWidget()
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(FIELD_GAP)
    lbl = field_label(label, tooltip)
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if tooltip:
        control.setToolTip(tooltip)
    lay.addWidget(lbl)
    lay.addWidget(control)
    return wrap


def set_tile_fill(box: QFrame, fill: bool) -> None:
    """Kafelek wypełnia wolną wysokość kolumny (biała karta zamiast dziury w siatce)."""
    v_policy = QSizePolicy.Policy.Expanding if fill else QSizePolicy.Policy.Preferred
    box.setSizePolicy(QSizePolicy.Policy.Expanding, v_policy)
    outer = box.layout()
    if outer is None or outer.count() < 2:
        return
    content = outer.itemAt(1).widget()
    if content is not None:
        content.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding if fill else QSizePolicy.Policy.Maximum,
        )
        outer.setStretch(1, 1 if fill else 0)


def make_tile(
    title: str,
    subtitle: str = "",
    *,
    icon_key: str = "",
    tooltip: str = "",
    compact: bool = False,
    compact_content_h: int = 0,
    fill: bool = False,
    variant: str = "panel",
    eyebrow: bool = False,
    number: str = "",
) -> tuple[QFrame, QVBoxLayout]:
    """Kafelek Bento. ``variant`` (właściwość QSS ``variant``, każdy kafelek ją ma):

    - ``panel`` — szare tło (domyślnie), jedyny blok na ekranie wg wzorca „Stwórz prezentację”;
    - ``plain`` — bez tła, treść prosto na białym; wypełnienie poziome 0 (treść równa z krawędzią kolumny);
    - ``drop`` — szare tło z przerywanym obrysem 1 px = strefa upuszczania plików.

    ``eyebrow`` — tytuł jako nadtytuł sekcji (``sectionTitle``: Lato, wersaliki, zielony) zamiast Mindset;
    ``number`` — numer kroku (``stepNumber``, np. „1.”) w osobnej etykiecie przed tytułem.
    """
    from inyfinn_resizer.app.widgets.section_icons import step_pixmap

    box = QFrame()
    box.setObjectName("bentoTile")
    box.setProperty("variant", variant if variant in ("panel", "plain", "drop") else "panel")
    if fill:
        v_policy = QSizePolicy.Policy.Expanding
    elif compact:
        v_policy = QSizePolicy.Policy.Maximum
    else:
        v_policy = QSizePolicy.Policy.Preferred
    box.setSizePolicy(QSizePolicy.Policy.Expanding, v_policy)
    outer = QVBoxLayout(box)
    if box.property("variant") == "plain":
        outer.setContentsMargins(0, 0, 0, 0)
    else:
        outer.setContentsMargins(TILE_PADDING, TILE_PADDING_TOP, TILE_PADDING, TILE_PADDING)
    outer.setSpacing(TILE_HEADER_SPACING)

    header = QWidget()
    header.setObjectName("sectionStepHeader")
    header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    header_row = QHBoxLayout(header)
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(TILE_HEADER_SPACING)

    if icon_key:
        icon = QLabel()
        icon.setObjectName(f"sectionIcon{icon_key.capitalize()}")
        icon.setPixmap(step_pixmap(icon_key))
        icon.setFixedSize(STEP_ICON_SIZE, STEP_ICON_SIZE)
        header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        box.setProperty("stepKey", icon_key)
        box._step_icon_label = icon  # type: ignore[attr-defined]
        box._step_key = icon_key  # type: ignore[attr-defined]

    text_col = QVBoxLayout()
    text_col.setContentsMargins(0, 0, 0, 0)
    text_col.setSpacing(1)
    title_lbl = QLabel(title)
    title_lbl.setObjectName("sectionTitle" if eyebrow else "sectionStepTitle")
    if number:
        # Numer kroku to osobna etykieta (inny kolor w QSS); pełny napis zostaje dostępny dla czytników i testów.
        title_lbl.setAccessibleName(f"{number} {title}")
        number_lbl = QLabel(number)
        number_lbl.setObjectName("stepNumber")
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        title_row.addWidget(number_lbl, 0, Qt.AlignmentFlag.AlignBottom)
        title_row.addWidget(title_lbl, 0, Qt.AlignmentFlag.AlignBottom)
        title_row.addStretch(1)
        text_col.addLayout(title_row)
    else:
        text_col.addWidget(title_lbl)
    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("sectionStepHint")
        sub_lbl.setWordWrap(True)
        text_col.addWidget(sub_lbl)
    header_row.addLayout(text_col, stretch=1)
    outer.addWidget(header, 0, Qt.AlignmentFlag.AlignTop)

    content = QWidget()
    content.setSizePolicy(
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Expanding if fill else QSizePolicy.Policy.Maximum,
    )
    inner = QVBoxLayout(content)
    inner.setContentsMargins(0, 0, 0, 0)
    inner.setSpacing(TILE_INNER_SPACING)
    outer.addWidget(content, 1 if fill else 0)

    if compact and compact_content_h > 0:
        header_h = STEP_ICON_SIZE if icon_key else TILE_TITLE_HEIGHT
        box.setFixedHeight(
            TILE_PADDING_TOP
            + header_h
            + TILE_HEADER_SPACING
            + compact_content_h
            + TILE_PADDING
        )

    if tooltip:
        box.setToolTip(tooltip)
        title_lbl.setToolTip(tooltip)
    return box, inner


def apply_tile_density(box: QFrame, density) -> None:
    """Wypełnienia i odstępy jednej karty wg ``window_fit.Density`` (wysokości kontrolek bez zmian).

    Trzy warianty (``variant``): ``panel`` i ``drop`` mają wypełnienie z gęstości, ``plain`` (treść na białym,
    bez tła) nie ma wypełnienia — rytm pionowy daje odstęp między kartami i linie ``groupSep`` w kontenerze.
    Tytuł karty dostaje miejsce na akcenty wersalików (``fit_title_height`` — kilka px wyżej niż sama czcionka);
    w kartach z wypełnieniem o tyle samo zmniejszamy górne wypełnienie, więc linia pisma zostaje tam, gdzie była.
    """
    outer = box.layout()
    if outer is None:
        return
    header = outer.itemAt(0).widget() if outer.count() else None
    has_header = header is not None and header.objectName() == "sectionStepHeader"
    plain = box.property("variant") == "plain"
    extra = 0
    if has_header:
        for name in ("sectionStepTitle", "stepNumber"):
            for title in header.findChildren(QLabel, name):
                if title.text():
                    fit_title_height(title)
                    if name == "sectionStepTitle":
                        extra = max(0, title.minimumHeight() - QFontMetrics(title.font()).height())
    if plain:
        outer.setContentsMargins(0, 0, 0, 0)
    else:
        top = max(4, density.tile_pad_top - extra)
        outer.setContentsMargins(density.tile_pad, top, density.tile_pad, density.tile_pad)
    if not has_header:
        return  # karta bez nagłówka: zostają jej własne odstępy
    outer.setSpacing(density.tile_header_gap)
    if header.layout() is not None:
        header.layout().setSpacing(density.tile_header_gap)
    content = outer.itemAt(1).widget() if outer.count() > 1 else None
    if content is not None and content.layout() is not None:
        content.layout().setSpacing(density.tile_inner_gap)


def breakable_path(path) -> str:
    """Ścieżka do etykiety z zawijaniem słów (2.6.6): łamanie tylko PO separatorze, dysk ``C:\\`` w jednym kawałku.

    Qt łamał ``C:\\Users\\…`` po „C:” (separator ``\\`` nie daje okazji do łamania po sobie, a przed sobą daje).
    Znak niewidoczny U+200B po każdym ``\\`` lub ``/`` = okazja do łamania, U+2060 między ``C:`` a ``\\`` = zakaz.
    Etykieta nie jest zaznaczalna, więc dodatkowe znaki nie trafiają do schowka.
    """
    text = str(path)
    head = ""
    if len(text) > 2 and text[1] == ":" and text[2] in "\\/":
        head, text = text[:2] + "\u2060", text[2:]
    if text.startswith(("\\\\", "//")):  # UNC: dwa pierwsze znaki to prefiks, nie separator
        head, text = head + text[:2], text[2:]
    for sep in ("\\", "/"):
        text = text.replace(sep, sep + "\u200b")
    return head + text


def group_separator() -> QFrame:
    """Linia 1 px między grupami (``QFrame#groupSep``, kolor z QSS) — wzorzec: ustawienia na białym rozdzielone linią."""
    line = QFrame()
    line.setObjectName("groupSep")
    line.setFrameShape(QFrame.Shape.NoFrame)
    line.setFixedHeight(1)
    line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return line


def make_bento_column() -> tuple[QWidget, QVBoxLayout]:
    """Pionowa kolumna Bento — kafelki sklejają się bez pustych przerw między wierszami siatki."""
    col = QWidget()
    col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(CARD_GAP)
    return col, lay


def make_settings_grid() -> QGridLayout:
    grid = QGridLayout()
    grid.setHorizontalSpacing(ROW_GAP)
    grid.setVerticalSpacing(ROW_GAP)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    return grid


def add_grid_field(grid: QGridLayout, row: int, col: int, field: QWidget) -> None:
    grid.addWidget(field, row, col)


def add_grid_span(grid: QGridLayout, row: int, widget: QWidget) -> None:
    grid.addWidget(widget, row, 0, 1, 2)


ICON_TEXT_GAP = 8  # odstęp ikona ↔ napis na przycisku (px logiczne); styl Qt dawał ~0–2 px
ICON_SIZE = QSize(16, 16)


def apply_button_icon(btn: QPushButton) -> None:
    """(Prze)rysowuje ikonę przycisku z fabryki motywu; przycisk z napisem dostaje ``ICON_TEXT_GAP`` odstępu.

    Odstęp to przezroczysty pasek po prawej stronie ikony (jedno miejsce w całym programie — nie w każdym
    przycisku osobno i nie spacjami w napisach); ``iconSize`` rośnie o ten pasek, więc ikona nie jest skalowana.
    Przycisk bez napisu (tylko ikona) odstępu nie dostaje. Wołane przy tworzeniu, zmianie motywu i zmianie napisu.
    """
    factory = getattr(btn, "_icon_factory", None)
    if factory is None:
        return
    base: QSize = getattr(btn, "_icon_base_size", ICON_SIZE)
    icon = factory()
    if not btn.text():
        btn.setIconSize(base)
        btn.setIcon(icon)
        return
    dpr = max(1.0, btn.devicePixelRatioF())
    src = icon.pixmap(base, dpr)
    out = QPixmap(round((base.width() + ICON_TEXT_GAP) * dpr), round(base.height() * dpr))
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.drawPixmap(0, int((base.height() - src.height() / dpr) / 2), src)
    painter.end()
    btn.setIconSize(QSize(base.width() + ICON_TEXT_GAP, base.height()))
    btn.setIcon(QIcon(out))


def set_themed_icon(btn: QPushButton, factory: Callable[[], QIcon], size: QSize = ICON_SIZE) -> QPushButton:
    """Ikona rysowana z kolorów motywu — ``refresh_themed_icons`` odświeża ją po zmianie motywu.

    Rozmiar ikony podaje się tutaj (``size``), nie przez ``setIconSize`` po fakcie — ten ustawia ``apply_button_icon``.
    """
    btn._icon_factory = factory  # type: ignore[attr-defined]
    btn._icon_base_size = QSize(size)  # type: ignore[attr-defined]
    apply_button_icon(btn)
    return btn


def refresh_themed_icons(root: QWidget) -> None:
    for btn in root.findChildren(QPushButton):
        if getattr(btn, "_icon_factory", None) is not None:
            apply_button_icon(btn)


def tool_button_row(
    specs: list[tuple[str, Callable[[], None], "QIcon | Callable[[], QIcon]"]],
    parent: QWidget | None = None,
    *,
    large: bool = False,
) -> QHBoxLayout:
    """Jeden poziomy rząd przycisków z ikonami (large = wysokość CONTROL_H trybu prostego)."""
    row = QHBoxLayout()
    row.setSpacing(8 if large else 6)
    row.setContentsMargins(0, 0, 0, 0)
    for text, slot, icon in specs:
        btn = QPushButton(text, parent)
        btn.setObjectName("toolBtn")
        set_themed_icon(btn, icon if callable(icon) else (lambda ic=icon: ic))
        btn.setToolTip(text)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        if large:
            mark_large(btn)
        else:
            btn.setMinimumHeight(BTN_H)
        btn.clicked.connect(slot)
        row.addWidget(btn)
    row.addStretch()
    return row


def tool_button_grid(
    specs: list[tuple[str, Callable[[], None], "QIcon | Callable[[], QIcon]"]],
    parent: QWidget | None = None,
) -> tuple[QWidget, list[QPushButton]]:
    """Rząd przycisków z ikonami, który umie się przełożyć na dwa rzędy (2.6.5, napisy wersalikami są szersze).

    Zwraca kontener (jego szerokość nie wymusza minimum kolumny — poziomy rozmiar ``Ignored``) i przyciski.
    ``arrange_tool_grid`` ustawia je w jednym rzędzie albo w parach; decyzję podejmuje okno wg dostępnej szerokości.
    """
    box = QWidget(parent)
    box.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(6)
    buttons: list[QPushButton] = []
    for text, slot, icon in specs:
        btn = QPushButton(text, box)
        btn.setObjectName("toolBtn")
        set_themed_icon(btn, icon if callable(icon) else (lambda ic=icon: ic))
        btn.setToolTip(text)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.setMinimumHeight(BTN_H)
        btn.clicked.connect(slot)
        buttons.append(btn)
    arrange_tool_grid(box, buttons, len(buttons))
    return box, buttons


def arrange_tool_grid(box: QWidget, buttons: list[QPushButton], cols: int) -> None:
    """Ustawia przyciski po ``cols`` w rzędzie (reszta rzędu to rozciągliwy odstęp po prawej)."""
    grid = box.layout()
    for btn in buttons:
        grid.removeWidget(btn)
    for i, btn in enumerate(buttons):
        grid.addWidget(btn, i // cols, i % cols)
    for c in range(len(buttons) + 1):
        grid.setColumnStretch(c, 1 if c == cols else 0)
    grid.invalidate()


def pin_button_min_widths(root: QWidget, skip: "QWidget | None" = None, only: "list[QWidget] | None" = None) -> None:
    """Minimalna szerokość przycisku z napisem = jego żywy sizeHint (nigdy mniej niż minimum ze stylu).

    QSS ustawia ``min-width`` (np. 106 px), które przesłania minimum układu — przy braku miejsca układ ściskał
    przyciski poniżej szerokości napisu (napis ucięty). Wersaliki z DS 2.0 są o 12–20 % szersze, więc ściskanie
    byłoby widoczne. Wartość ze stylu zapamiętujemy raz (``_qss_min_w``) i używamy jako dolnej granicy.
    """
    allowed = set(only) if only is not None else None  # tylko przyciski z tych widżetów-rodziców (zakres pomiaru)
    for btn in root.findChildren(QPushButton):
        if not btn.text() or btn.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Ignored:
            continue
        if skip is not None and skip.isAncestorOf(btn):
            continue
        if allowed is not None and btn.parentWidget() not in allowed:
            continue
        btn.ensurePolished()  # min-width ze stylu musi być już nałożone, zanim je zapamiętamy
        qss_min = btn.property("_qss_min_w")
        if qss_min is None:
            qss_min = btn.minimumWidth()
            btn.setProperty("_qss_min_w", qss_min)
        want = max(int(qss_min), btn.sizeHint().width())
        if btn.minimumWidth() != want and btn.maximumWidth() >= want:
            btn.setMinimumWidth(want)


# Litery z akcentami nad wersalikiem — wyznaczają, ile miejsca nad linią pisma potrzebuje tytuł Mindset.
_TITLE_ACCENT_PROBE = "ŚĆÓŻŹĄĘŁŃ"


def fit_title_height(lbl: QLabel) -> None:
    """Wysokość tytułu z żywych metryk czcionki, nie ze stałej: akcenty wersalików sięgają wyżej niż ``ascent``.

    Czcionka Mindset ma ascent 18 px przy 22 px, a „Ś”, „Ć”, „Ó” sięgają 20 px nad linię pisma — etykieta o wysokości
    ``fontMetrics().height()`` ucinała 2 px czubków akcentów (widać było „JAKOSC”, „PLIKOW”). Etykieta dostaje
    wysokość = (najwyższy znak z akcentem) + descent i wyrównanie do dołu, więc zapas idzie nad tekst.
    Wołane po nałożeniu stylu (czcionka ze stylu i wersaliki z filtra typografii są już ustawione).
    """
    lbl.ensurePolished()
    fm = QFontMetrics(lbl.font())
    glyph_top = -fm.tightBoundingRect(_TITLE_ACCENT_PROBE).top()
    need = max(fm.height(), int(glyph_top + 0.999) + fm.descent() + 1)
    if lbl.minimumHeight() != need:
        lbl.setMinimumHeight(need)
    align = lbl.alignment()
    if not (align & Qt.AlignmentFlag.AlignBottom):
        lbl.setAlignment((align & ~Qt.AlignmentFlag.AlignVertical_Mask) | Qt.AlignmentFlag.AlignBottom)


def fit_title_heights(widgets) -> None:
    """``fit_title_height`` dla wszystkich tytułów Mindset (obiekty z ``typography.DISPLAY_OBJECTS``) w podanych widżetach."""
    from inyfinn_resizer.app.themes.typography import DISPLAY_OBJECTS

    names = set(DISPLAY_OBJECTS) | {"stepNumber", "dropEmptyTitle"}  # numer kroku i tytuł pustej strefy też są Mindset
    for w in widgets:
        if isinstance(w, QLabel) and w.objectName() in names and w.text():
            fit_title_height(w)


def mark_quiet(btn: QPushButton) -> QPushButton:
    """DS 2.0.1 (S13): przycisk „cichy” — bez obrysu, jasne tło (QSS: ``QPushButton[quiet="true"]``).

    W grupie przycisków: najwyżej jeden zielony główny, najwyżej jeden z obrysem, reszta cicha.
    """
    btn.setProperty("quiet", True)
    return btn


def mark_large(widget: QWidget, height: int = CONTROL_H) -> QWidget:
    """Właściwość QSS large=true + stała wysokość — jeden rozmiar kontrolek w trybie prostym."""
    widget.setProperty("large", True)
    widget.setFixedHeight(height)
    return widget


def style_dropdown(combo: QComboBox) -> QComboBox:
    """Niebieski obrys + strzałka listy rozwijanej (QSS)."""
    combo.setMinimumHeight(BTN_H)
    combo.setMaximumHeight(COMPACT_CONTROL_ROW_H)
    return combo


def footer_button(text: str, *, primary: bool, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("footerPrimary" if primary else "footerSecondary")
    btn.setFixedHeight(FOOTER_BTN_H)
    btn.setMinimumWidth(140 if primary else 108)
    btn.clicked.connect(slot)
    return btn


def action_button(text: str, object_name: str, slot: Callable[[], None], parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName(object_name)
    btn.setMinimumHeight(32 if object_name == "primaryBtn" else BTN_H)
    if object_name == "primaryBtn":
        btn.setMinimumWidth(116)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(88)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    btn.clicked.connect(slot)
    return btn


def h_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("hSeparator")
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    return line


def v_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("vSeparator")
    line.setFrameShape(QFrame.VLine)
    line.setFixedWidth(1)
    return line


def browse_button(text: str = "Przeglądaj", *, tooltip: str = "", slot=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("btnBrowse")
    btn.setMinimumHeight(BTN_H)
    btn.setFixedHeight(BTN_H)
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    if tooltip:
        btn.setToolTip(tooltip)
    if slot:
        btn.clicked.connect(slot)
    return btn


def add_form_row(grid: QGridLayout, row: int, label: str, widget: QWidget, *, span: int = 1) -> None:
    wrap = field_group(label, widget)
    grid.addWidget(wrap, row, 0, 1, span)
