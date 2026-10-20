"""Opcje zaawansowane — panel kart (wariant B, 2.6.7): białe karty na szarym tle, „Włącz…” jako przełącznik DS w nagłówku.

Panel jest wspólny dla okna „Opcje zaawansowane”, sekcji „Zaawansowane” w oknie Ustawienia i okna zapisu własnego
presetu wymiarów. Karta „Zmiana rozmiaru” i część „kadr według współrzędnych” karty „Kadrowanie” mają przełącznik
(dawny checkbox „Włącz…” — ten sam stan: ``resize_enable``, ``crop_enable``); wyłączona treść jest przygaszona i
nieaktywna. Reszta opcji kadrowania (przezroczyste marginesy, proporcje) działa niezależnie, jak dotąd.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.dialogs.base_dialog import (
    DIALOG_ROW_GAP,
    DIALOG_SECTION_GAP,
)
from inyfinn_resizer.app.widgets.layout_helpers import field_group, h_separator, style_dropdown
from inyfinn_resizer.app.widgets.section_card import SectionCard
from inyfinn_resizer.app.widgets.switch import SwitchBox
from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions

BRAND_GRADIENT_1 = "#76b82a"
BRAND_GRADIENT_2 = "#008834"
DIM_OPACITY = 0.5  # przygaszona treść wyłączonej karty


def _plain_spin() -> QSpinBox:
    spin = QSpinBox()
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setMinimumHeight(32)
    return spin


def _card(key: str, title: str, tooltip: str = "") -> tuple[SectionCard, QVBoxLayout]:
    """Biała karta sekcji (L2) z tytułem Mindset; bez zwijania (``collapsible=False``)."""
    card = SectionCard(key, title, tooltip=tooltip, collapsible=False)
    return card, card.body_layout


def _dim_when_off(switch: QCheckBox, target: QWidget) -> None:
    """Wyłączony przełącznik: treść nieaktywna i przygaszona (DS 26.4); włączony: wraca do normy."""

    def apply(on: bool) -> None:
        target.setEnabled(on)
        if on:
            target.setGraphicsEffect(None)
        else:
            effect = QGraphicsOpacityEffect(target)
            effect.setOpacity(DIM_OPACITY)
            target.setGraphicsEffect(effect)

    switch.toggled.connect(apply)
    apply(switch.isChecked())


class AdvancedSettingsPanel(QWidget):
    """Zakładka / sekcja Zaawansowane: resize, crop, obrót, korekcje."""

    def __init__(
        self,
        resize: ResizeOptions,
        transforms: TransformOptions,
        parent: QWidget | None = None,
        *,
        scroll: bool = True,
        title: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._resize = resize
        self._transforms = transforms

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Szary panel (L1) z białymi kartami (L2) w środku; przewijanie (jeśli jest) leży WEWNĄTRZ panelu,
        # więc zaokrąglone rogi panelu zostają na miejscu.
        panel = QFrame()
        panel.setObjectName("cardPanel")
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(DIALOG_SECTION_GAP, DIALOG_SECTION_GAP, DIALOG_SECTION_GAP, DIALOG_SECTION_GAP)
        panel_lay.setSpacing(DIALOG_SECTION_GAP)
        if title:
            heading = QLabel(title)
            heading.setObjectName("settingsSectionTitle")
            panel_lay.addWidget(heading)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(DIALOG_SECTION_GAP)  # między kartami 16 px
        body_lay.setContentsMargins(0, 0, 0, 0)

        resize_card, resize_lay = _card(
            "resize",
            "Zmiana rozmiaru",
            "Włącz, gdy preset w głównym oknie nie wystarcza. Proporcje są zawsze zachowane.",
        )
        self.resize_enable = SwitchBox()
        self.resize_enable.setToolTip("Własna zmiana rozmiaru zamiast presetu z głównego okna")
        self.resize_enable.setChecked(self._resize.mode != ResizeMode.NONE)
        resize_card.add_header_action(self.resize_enable)
        resize_body = QWidget()
        resize_body_lay = QVBoxLayout(resize_body)
        resize_body_lay.setContentsMargins(0, 0, 0, 0)
        resize_body_lay.setSpacing(DIALOG_ROW_GAP)
        resize_lay.addWidget(resize_body)
        self._resize_body = resize_body  # treść gaszona przełącznikiem (testy, zrzuty)

        row1 = QHBoxLayout()
        row1.setSpacing(DIALOG_ROW_GAP)
        self.side_combo = style_dropdown(QComboBox())
        self.side_combo.addItems(["Szerokość", "Wysokość", "Dłuższy bok", "Krótszy bok"])
        row1.addWidget(field_group("Skaluj według", self.side_combo), stretch=1)
        self.dim_spin = _plain_spin()
        self.dim_spin.setRange(1, 32000)
        self.dim_spin.setValue(self._resize.dimension or 1800)
        row1.addWidget(field_group("Wymiar (px)", self.dim_spin), stretch=1)
        resize_body_lay.addLayout(row1)

        row2 = QHBoxLayout()
        self.filter_combo = style_dropdown(QComboBox())
        self.filter_combo.addItems(["Lanczos3 (domyślny)", "Lanczos2", "Cubic", "Linear"])
        row2.addWidget(field_group("Filtr skalowania", self.filter_combo), stretch=1)
        resize_body_lay.addLayout(row2)

        self.skip_smaller = QCheckBox("Nie powiększaj, gdy zdjęcie jest już mniejsze")
        self.skip_smaller.setChecked(self._resize.skip_if_smaller)
        resize_body_lay.addWidget(self.skip_smaller)
        body_lay.addWidget(resize_card)
        _dim_when_off(self.resize_enable, resize_body)

        crop_card, crop_lay = _card(
            "crop",
            "Kadrowanie",
            "Przytnij obraz do wybranego prostokąta lub do przezroczystych pikseli.",
        )
        self.crop_enable = SwitchBox()
        self.crop_enable.setToolTip("Kadrowanie do prostokąta: X, Y, szerokość i wysokość w pikselach")
        crop_card.add_header_action(self.crop_enable)
        crop_rect = QWidget()
        crop_grid = QGridLayout(crop_rect)
        crop_grid.setContentsMargins(0, 0, 0, 0)
        crop_grid.setHorizontalSpacing(DIALOG_ROW_GAP)
        crop_grid.setVerticalSpacing(DIALOG_ROW_GAP)

        self.crop_x = _plain_spin()
        self.crop_x.setRange(0, 32000)
        self.crop_y = _plain_spin()
        self.crop_y.setRange(0, 32000)
        self.crop_w = _plain_spin()
        self.crop_w.setRange(0, 32000)
        self.crop_h = _plain_spin()
        self.crop_h.setRange(0, 32000)

        crop_grid.addWidget(field_group("X (lewy)", self.crop_x), 0, 0)
        crop_grid.addWidget(field_group("Y (górny)", self.crop_y), 0, 1)
        crop_grid.addWidget(field_group("Szerokość", self.crop_w), 1, 0)
        crop_grid.addWidget(field_group("Wysokość", self.crop_h), 1, 1)
        crop_lay.addWidget(crop_rect)
        self._crop_rect = crop_rect
        _dim_when_off(self.crop_enable, crop_rect)

        # Poniżej: opcje kadrowania niezależne od prostokąta (działały i działają bez „Włącz kadrowanie”)
        crop_lay.addWidget(h_separator())
        self.trim_transparent = QCheckBox("Kadruj do przezroczystych pikseli")
        self.trim_transparent.setToolTip(
            "Automatycznie usuwa puste (przezroczyste) marginesy — jak Trim w Photoshop."
        )
        crop_lay.addWidget(self.trim_transparent)

        margin_row = QHBoxLayout()
        self.trim_margin = _plain_spin()
        self.trim_margin.setRange(0, 500)
        self.trim_margin.setSuffix(" px")
        margin_row.addWidget(field_group("Margines od przezroczystych pikseli", self.trim_margin), stretch=1)
        crop_lay.addLayout(margin_row)

        self.preserve_aspect = QCheckBox("Zachowaj proporcje obrazka")
        self.preserve_aspect.setChecked(self._resize.preserve_aspect)
        crop_lay.addWidget(self.preserve_aspect)
        body_lay.addWidget(crop_card)

        rotate_card, rotate_lay = _card("rotate", "Obrót i odbicia", "Korekta orientacji przed zapisem.")
        self.flip_h = QCheckBox("Odbicie poziome")
        self.flip_v = QCheckBox("Odbicie pionowe")
        self.auto_exif = QCheckBox("Autoobrót według EXIF")
        self.auto_exif.setChecked(self._transforms.auto_rotate_exif)
        rotate_lay.addWidget(self.flip_h)
        rotate_lay.addWidget(self.flip_v)
        rotate_lay.addWidget(self.auto_exif)
        self.rotate_combo = style_dropdown(QComboBox())
        self.rotate_combo.addItems(["0°", "90°", "180°", "270°"])
        rotate_lay.addWidget(field_group("Stały obrót", self.rotate_combo))
        body_lay.addWidget(rotate_card)

        adjust_card, adjust_lay = _card("adjust", "Korekcje kolorów", "Proste filtry nakładane na cały obraz.")
        self.grayscale = QCheckBox("Czarno-biały")
        self.sepia = QCheckBox("Sepia")
        adjust_lay.addWidget(self.grayscale)
        adjust_lay.addWidget(self.sepia)
        body_lay.addWidget(adjust_card)
        self.cards = [resize_card, crop_card, rotate_card, adjust_card]
        if scroll:
            body_lay.addStretch()
            scroll_area = QScrollArea()
            scroll_area.setObjectName("settingsScroll")
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            scroll_area.setWidget(body)
            panel_lay.addWidget(scroll_area, stretch=1)
        else:
            panel_lay.addWidget(body)
        outer.addWidget(panel)
        self._load_state()

    def _load_state(self) -> None:
        self.resize_enable.setChecked(self._resize.mode != ResizeMode.NONE)
        if self._resize.mode == ResizeMode.ONE_SIDE:
            self.dim_spin.setValue(self._resize.dimension or 1200)
            side_rev = {"width": 0, "height": 1, "longer": 2, "shorter": 3}
            self.side_combo.setCurrentIndex(side_rev.get(self._resize.side, 2))
            filters = ["lanczos3", "lanczos2", "cubic", "linear"]
            if self._resize.filter_name in filters:
                self.filter_combo.setCurrentIndex(filters.index(self._resize.filter_name))
            self.skip_smaller.setChecked(self._resize.skip_if_smaller)
        self.flip_h.setChecked(self._transforms.flip_h)
        self.flip_v.setChecked(self._transforms.flip_v)
        self.grayscale.setChecked(self._transforms.grayscale)
        self.sepia.setChecked(self._transforms.sepia)
        self.trim_transparent.setChecked(self._transforms.trim_transparent)
        self.trim_margin.setValue(self._transforms.trim_margin)
        has_crop = self._transforms.crop_w > 0 and self._transforms.crop_h > 0
        self.crop_enable.setChecked(has_crop)
        self.crop_x.setValue(self._transforms.crop_x)
        self.crop_y.setValue(self._transforms.crop_y)
        self.crop_w.setValue(self._transforms.crop_w)
        self.crop_h.setValue(self._transforms.crop_h)
        rot_idx = (
            [0, 90, 180, 270].index(self._transforms.rotate)
            if self._transforms.rotate in (0, 90, 180, 270)
            else 0
        )
        self.rotate_combo.setCurrentIndex(rot_idx)

    def reset_all(self) -> None:
        self._resize = ResizeOptions()
        self._transforms = TransformOptions()
        self.resize_enable.setChecked(False)
        self.dim_spin.setValue(1800)
        self.skip_smaller.setChecked(True)
        self.auto_exif.setChecked(True)
        self.flip_h.setChecked(False)
        self.flip_v.setChecked(False)
        self.grayscale.setChecked(False)
        self.sepia.setChecked(False)
        self.rotate_combo.setCurrentIndex(0)
        self.crop_enable.setChecked(False)
        self.crop_x.setValue(0)
        self.crop_y.setValue(0)
        self.crop_w.setValue(0)
        self.crop_h.setValue(0)
        self.trim_transparent.setChecked(False)
        self.trim_margin.setValue(0)
        self.preserve_aspect.setChecked(True)

    def get_resize(self) -> ResizeOptions:
        r = ResizeOptions()
        if self.resize_enable.isChecked():
            r.mode = ResizeMode.ONE_SIDE
            r.dimension = self.dim_spin.value()
            side_map = {0: "width", 1: "height", 2: "longer", 3: "shorter"}
            r.side = side_map.get(self.side_combo.currentIndex(), "width")
            r.skip_if_smaller = self.skip_smaller.isChecked()
            filters = ["lanczos3", "lanczos2", "cubic", "linear"]
            r.filter_name = filters[self.filter_combo.currentIndex()]
        r.preserve_aspect = self.preserve_aspect.isChecked()
        return r

    def get_transforms(self) -> TransformOptions:
        t = TransformOptions()
        t.flip_h = self.flip_h.isChecked()
        t.flip_v = self.flip_v.isChecked()
        t.auto_rotate_exif = self.auto_exif.isChecked()
        t.grayscale = self.grayscale.isChecked()
        t.sepia = self.sepia.isChecked()
        t.rotate = [0, 90, 180, 270][self.rotate_combo.currentIndex()]
        t.trim_transparent = self.trim_transparent.isChecked()
        t.trim_margin = self.trim_margin.value()
        if self.crop_enable.isChecked():
            t.crop_x = self.crop_x.value()
            t.crop_y = self.crop_y.value()
            t.crop_w = self.crop_w.value()
            t.crop_h = self.crop_h.value()
        return t


# Zachowaj dialog dla kompatybilności wstecznej (import z innych modułów).
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, apply_dialog_layout, build_dialog_footer


class AdvancedOptionsDialog(AppDialog):
    """Okno „Opcje zaawansowane”: szary panel z białymi kartami; dół: Resetuj wszystko | Anuluj, OK (DS 26.5)."""

    def __init__(self, resize: ResizeOptions, transforms: TransformOptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje zaawansowane")
        self.setMinimumSize(520, 520)
        self._panel = AdvancedSettingsPanel(resize, transforms, self)

        layout = QVBoxLayout(self)
        apply_dialog_layout(layout)
        layout.addWidget(self._panel, stretch=1)
        footer, *_buttons = build_dialog_footer(self, "Resetuj wszystko", self._panel.reset_all)
        layout.addLayout(footer)

    def get_resize(self) -> ResizeOptions:
        return self._panel.get_resize()

    def get_transforms(self) -> TransformOptions:
        return self._panel.get_transforms()
