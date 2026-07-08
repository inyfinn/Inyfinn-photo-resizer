"""Opcje zaawansowane — układ sekcji jak w głównym panelu."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.widgets.layout_helpers import field_group, make_section
from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions


class AdvancedOptionsDialog(AppDialog):
    def __init__(self, resize: ResizeOptions, transforms: TransformOptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje zaawansowane")
        self.setMinimumSize(520, 480)
        self._resize = resize
        self._transforms = transforms

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        intro = QLabel(
            "Tu ustawisz szczegółową zmianę rozmiaru, obrót i proste korekcje. "
            "Preset „Rozmiar obrazu” w głównym oknie nadpisuje te ustawienia przy konwersji."
        )
        intro.setObjectName("hintLabel")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(10)
        body_lay.setContentsMargins(0, 0, 4, 0)

        resize_box, resize_lay = make_section(
            "Zmiana rozmiaru",
            "Włącz, gdy preset w głównym oknie nie wystarcza. Proporcje są zawsze zachowane.",
        )
        self.resize_enable = QCheckBox("Włącz własną zmianę rozmiaru")
        self.resize_enable.setChecked(self._resize.mode != ResizeMode.NONE)
        resize_lay.addWidget(self.resize_enable)

        self.side_combo = QComboBox()
        self.side_combo.setMinimumHeight(36)
        self.side_combo.addItems(["Szerokość", "Wysokość", "Dłuższy bok", "Krótszy bok"])
        resize_lay.addWidget(field_group("Skaluj według", self.side_combo))

        self.dim_spin = QSpinBox()
        self.dim_spin.setRange(1, 32000)
        self.dim_spin.setValue(self._resize.dimension or 1800)
        self.dim_spin.setMinimumHeight(36)
        resize_lay.addWidget(field_group("Wymiar (px)", self.dim_spin))

        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumHeight(36)
        self.filter_combo.addItems(["Lanczos3 (domyślny)", "Lanczos2", "Cubic", "Linear"])
        resize_lay.addWidget(field_group("Filtr skalowania", self.filter_combo))

        self.skip_smaller = QCheckBox("Nie powiększaj, gdy zdjęcie jest już mniejsze")
        self.skip_smaller.setChecked(self._resize.skip_if_smaller)
        resize_lay.addWidget(self.skip_smaller)
        body_lay.addWidget(resize_box)

        rotate_box, rotate_lay = make_section("Obrót i odbicia", "Korekta orientacji przed zapisem.")
        self.flip_h = QCheckBox("Odbicie poziome")
        self.flip_v = QCheckBox("Odbicie pionowe")
        self.auto_exif = QCheckBox("Autoobrót według EXIF")
        self.auto_exif.setChecked(self._transforms.auto_rotate_exif)
        rotate_lay.addWidget(self.flip_h)
        rotate_lay.addWidget(self.flip_v)
        rotate_lay.addWidget(self.auto_exif)
        self.rotate_combo = QComboBox()
        self.rotate_combo.setMinimumHeight(36)
        self.rotate_combo.addItems(["0°", "90°", "180°", "270°"])
        rotate_lay.addWidget(field_group("Stały obrót", self.rotate_combo))
        body_lay.addWidget(rotate_box)

        adjust_box, adjust_lay = make_section("Korekcje kolorów", "Proste filtry nakładane na cały obraz.")
        self.grayscale = QCheckBox("Czarno-biały")
        self.sepia = QCheckBox("Sepia")
        adjust_lay.addWidget(self.grayscale)
        adjust_lay.addWidget(self.sepia)
        body_lay.addWidget(adjust_box)

        scroll.setWidget(body)
        layout.addWidget(scroll, stretch=1)

        bottom = QHBoxLayout()
        reset_btn = QPushButton("Resetuj wszystko")
        reset_btn.setObjectName("btnSecondary")
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._reset_all)
        bottom.addWidget(reset_btn)
        bottom.addStretch()
        layout.addLayout(bottom)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_state()

    def _load_state(self) -> None:
        self.flip_h.setChecked(self._transforms.flip_h)
        self.flip_v.setChecked(self._transforms.flip_v)
        self.grayscale.setChecked(self._transforms.grayscale)
        self.sepia.setChecked(self._transforms.sepia)
        rot_idx = [0, 90, 180, 270].index(self._transforms.rotate) if self._transforms.rotate in (0, 90, 180, 270) else 0
        self.rotate_combo.setCurrentIndex(rot_idx)

    def _reset_all(self) -> None:
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
        return r

    def get_transforms(self) -> TransformOptions:
        t = TransformOptions()
        t.flip_h = self.flip_h.isChecked()
        t.flip_v = self.flip_v.isChecked()
        t.auto_rotate_exif = self.auto_exif.isChecked()
        t.grayscale = self.grayscale.isChecked()
        t.sepia = self.sepia.isChecked()
        t.rotate = [0, 90, 180, 270][self.rotate_combo.currentIndex()]
        return t
