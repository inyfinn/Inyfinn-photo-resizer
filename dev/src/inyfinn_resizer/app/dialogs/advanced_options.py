"""Opcje zaawansowane — po polsku."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions


class AdvancedOptionsDialog(AppDialog):
    def __init__(self, resize: ResizeOptions, transforms: TransformOptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje zaawansowane")
        self.resize(520, 400)
        self._resize = resize
        self._transforms = transforms

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setObjectName("dialogTabs")
        tabs.addTab(self._resize_tab(), "Zmiana rozmiaru")
        tabs.addTab(self._rotate_tab(), "Obrót")
        tabs.addTab(self._adjust_tab(), "Korekcje")
        layout.addWidget(tabs)

        bottom = QHBoxLayout()
        for text in ("Resetuj wszystko", "Wczytaj z pliku", "Zapisz do pliku"):
            b = QPushButton(text)
            b.setObjectName("btnSecondary")
            b.setFixedHeight(36)
            if text == "Resetuj wszystko":
                b.clicked.connect(self._reset_all)
            bottom.addWidget(b)
        bottom.addStretch()
        layout.addLayout(bottom)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _resize_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        fl.setSpacing(8)
        self.resize_enable = QCheckBox("Włącz zmianę rozmiaru")
        self.resize_enable.setChecked(self._resize.mode != ResizeMode.NONE)
        fl.addRow(self.resize_enable)

        self.side_combo = QComboBox()
        self.side_combo.addItems(["Szerokość", "Wysokość", "Dłuższy bok", "Krótszy bok"])
        fl.addRow("Bok:", self.side_combo)

        self.dim_spin = QSpinBox()
        self.dim_spin.setRange(1, 32000)
        self.dim_spin.setValue(self._resize.dimension or 1800)
        fl.addRow("Wymiar (px):", self.dim_spin)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Lanczos3 (domyślny)", "Lanczos2", "Cubic", "Linear"])
        fl.addRow("Filtr:", self.filter_combo)

        self.skip_smaller = QCheckBox("Nie powiększaj, gdy zdjęcie jest już mniejsze")
        self.skip_smaller.setChecked(self._resize.skip_if_smaller)
        fl.addRow(self.skip_smaller)

        note = QLabel("Proporcje obrazu są zawsze zachowane.")
        note.setObjectName("hintLabel")
        note.setWordWrap(True)
        fl.addRow(note)
        return w

    def _rotate_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self.flip_h = QCheckBox("Odbicie poziome")
        self.flip_v = QCheckBox("Odbicie pionowe")
        self.auto_exif = QCheckBox("Autoobrót według EXIF")
        self.auto_exif.setChecked(self._transforms.auto_rotate_exif)
        fl.addRow(self.flip_h)
        fl.addRow(self.flip_v)
        fl.addRow(self.auto_exif)
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["0°", "90°", "180°", "270°"])
        fl.addRow("Obrót:", self.rotate_combo)
        return w

    def _adjust_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self.grayscale = QCheckBox("Czarno-biały")
        self.sepia = QCheckBox("Sepia")
        fl.addRow(self.grayscale)
        fl.addRow(self.sepia)
        return w

    def _reset_all(self) -> None:
        self._resize = ResizeOptions()
        self._transforms = TransformOptions()
        self.resize_enable.setChecked(False)
        self.dim_spin.setValue(1800)
        self.skip_smaller.setChecked(True)
        self.auto_exif.setChecked(True)

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
