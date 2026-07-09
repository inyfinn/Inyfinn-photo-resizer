"""Opcje zaawansowane — panel do zakładki w ustawieniach formatu."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.widgets.layout_helpers import field_group, h_separator, style_dropdown
from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions

BRAND_GRADIENT_1 = "#76b82a"
BRAND_GRADIENT_2 = "#008834"


def _plain_spin() -> QSpinBox:
    spin = QSpinBox()
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setMinimumHeight(32)
    return spin


def _flat_section(title: str, tooltip: str = "") -> tuple[QWidget, QVBoxLayout]:
    wrap = QWidget()
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    hdr = QLabel(title)
    hdr.setObjectName("sectionTitle")
    if tooltip:
        hdr.setToolTip(tooltip)
        wrap.setToolTip(tooltip)
    lay.addWidget(hdr)
    lay.addWidget(h_separator())
    return wrap, lay


class AdvancedSettingsPanel(QWidget):
    """Zakładka Zaawansowane: resize, crop, obrót, korekcje."""

    def __init__(
        self,
        resize: ResizeOptions,
        transforms: TransformOptions,
        parent: QWidget | None = None,
        *,
        scroll: bool = True,
    ) -> None:
        super().__init__(parent)
        self._resize = resize
        self._transforms = transforms

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(12)
        body_lay.setContentsMargins(4, 4, 4, 4)

        resize_box, resize_lay = _flat_section(
            "Zmiana rozmiaru",
            "Włącz, gdy preset w głównym oknie nie wystarcza. Proporcje są zawsze zachowane.",
        )
        self.resize_enable = QCheckBox("Włącz własną zmianę rozmiaru")
        self.resize_enable.setChecked(self._resize.mode != ResizeMode.NONE)
        resize_lay.addWidget(self.resize_enable)

        row1 = QHBoxLayout()
        self.side_combo = style_dropdown(QComboBox())
        self.side_combo.addItems(["Szerokość", "Wysokość", "Dłuższy bok", "Krótszy bok"])
        row1.addWidget(field_group("Skaluj według", self.side_combo), stretch=1)
        self.dim_spin = _plain_spin()
        self.dim_spin.setRange(1, 32000)
        self.dim_spin.setValue(self._resize.dimension or 1800)
        row1.addWidget(field_group("Wymiar (px)", self.dim_spin), stretch=1)
        resize_lay.addLayout(row1)

        row2 = QHBoxLayout()
        self.filter_combo = style_dropdown(QComboBox())
        self.filter_combo.addItems(["Lanczos3 (domyślny)", "Lanczos2", "Cubic", "Linear"])
        row2.addWidget(field_group("Filtr skalowania", self.filter_combo), stretch=1)
        resize_lay.addLayout(row2)

        self.skip_smaller = QCheckBox("Nie powiększaj, gdy zdjęcie jest już mniejsze")
        self.skip_smaller.setChecked(self._resize.skip_if_smaller)
        resize_lay.addWidget(self.skip_smaller)
        body_lay.addWidget(resize_box)

        crop_box, crop_lay = _flat_section(
            "Kadrowanie",
            "Przytnij obraz do wybranego prostokąta lub do przezroczystych pikseli.",
        )
        crop_grid = QGridLayout()
        crop_grid.setHorizontalSpacing(10)
        crop_grid.setVerticalSpacing(8)

        self.crop_enable = QCheckBox("Włącz kadrowanie (piksele)")
        crop_grid.addWidget(self.crop_enable, 0, 0, 1, 2)

        self.crop_x = _plain_spin()
        self.crop_x.setRange(0, 32000)
        self.crop_y = _plain_spin()
        self.crop_y.setRange(0, 32000)
        self.crop_w = _plain_spin()
        self.crop_w.setRange(0, 32000)
        self.crop_h = _plain_spin()
        self.crop_h.setRange(0, 32000)

        crop_grid.addWidget(field_group("X (lewy)", self.crop_x), 1, 0)
        crop_grid.addWidget(field_group("Y (górny)", self.crop_y), 1, 1)
        crop_grid.addWidget(field_group("Szerokość", self.crop_w), 2, 0)
        crop_grid.addWidget(field_group("Wysokość", self.crop_h), 2, 1)
        crop_lay.addLayout(crop_grid)

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
        body_lay.addWidget(crop_box)

        rotate_box, rotate_lay = _flat_section("Obrót i odbicia", "Korekta orientacji przed zapisem.")
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
        body_lay.addWidget(rotate_box)

        adjust_box, adjust_lay = _flat_section("Korekcje kolorów", "Proste filtry nakładane na cały obraz.")
        self.grayscale = QCheckBox("Czarno-biały")
        self.sepia = QCheckBox("Sepia")
        adjust_lay.addWidget(self.grayscale)
        adjust_lay.addWidget(self.sepia)
        body_lay.addWidget(adjust_box)
        if scroll:
            body_lay.addStretch()
            scroll_area = QScrollArea()
            scroll_area.setObjectName("settingsScroll")
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            scroll_area.setWidget(body)
            outer.addWidget(scroll_area)
        else:
            outer.addWidget(body)
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
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons


class AdvancedOptionsDialog(AppDialog):
    def __init__(self, resize: ResizeOptions, transforms: TransformOptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje zaawansowane")
        self.setMinimumSize(520, 520)
        self._panel = AdvancedSettingsPanel(resize, transforms, self)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(self._panel, stretch=1)

        bottom = QHBoxLayout()
        reset_btn = QPushButton("Resetuj wszystko")
        reset_btn.setObjectName("btnSecondary")
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._panel.reset_all)
        bottom.addWidget(reset_btn)
        bottom.addStretch()
        layout.addLayout(bottom)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_resize(self) -> ResizeOptions:
        return self._panel.get_resize()

    def get_transforms(self) -> TransformOptions:
        return self._panel.get_transforms()
