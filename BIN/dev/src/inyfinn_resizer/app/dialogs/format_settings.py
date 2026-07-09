"""Opcje formatu wyjściowego — po polsku."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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

from inyfinn_resizer.app.dialogs.advanced_options import (
    BRAND_GRADIENT_1,
    BRAND_GRADIENT_2,
    AdvancedSettingsPanel,
)
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.i18n_tooltips import FORMAT_EXTENSION_TIPS
from inyfinn_resizer.app.widgets.layout_helpers import style_dropdown
from inyfinn_resizer.core.job import FormatOptions, ResizeOptions, TransformOptions
from inyfinn_resizer.core.quality_map import gif_lossy_for_quality, palette_colors_for_quality


def _preview_gradient_style(
    c1: str,
    c2: str,
    *,
    gradient_type: str = "linear",
    reverse: bool = False,
) -> str:
    if reverse:
        c1, c2 = c2, c1
    border = "border: 1px solid #94a3b8; border-radius: 4px;"
    if gradient_type == "radial":
        return (
            f"background: qradialgradient(cx:0.5, cy:0.5, radius:0.85, "
            f"fx:0.5, fy:0.5, stop:0 {c1}, stop:1 {c2}); {border}"
        )
    return (
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c1}, stop:1 {c2}); {border}"
    )


def _swatch_style(hex_color: str) -> str:
    return f"background-color: {hex_color}; border: 1px solid #94a3b8; border-radius: 4px;"


class FormatSettingsDialog(AppDialog):
    def __init__(
        self,
        fmt: str,
        opts: FormatOptions,
        parent=None,
        *,
        resize: ResizeOptions | None = None,
        transforms: TransformOptions | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia rozszerzenia")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._opts = opts
        self._fmt = fmt
        self._resize = resize or ResizeOptions()
        self._transforms = transforms or TransformOptions()

        self._jpeg_progressive: QCheckBox | None = None
        self._jpeg_lossless_src: QCheckBox | None = None
        self._jpeg_matte_mode: QComboBox | None = None
        self._jpeg_gradient_type: QComboBox | None = None
        self._jpeg_gradient_reverse: QCheckBox | None = None
        self._jpeg_matte_noise: QCheckBox | None = None
        self._jpeg_color_btn: QPushButton | None = None
        self._jpeg_color2_btn: QPushButton | None = None
        self._jpeg_preview: QLabel | None = None
        self._png_lossless: QCheckBox | None = None
        self._png_mode: QComboBox | None = None
        self._webp_lossless: QCheckBox | None = None
        self._keep_meta: QCheckBox | None = None
        self._subsampling: QComboBox | None = None
        self._gif_dither: QCheckBox | None = None
        self._gif_lossy: QSpinBox | None = None
        self._gif_from_quality: QCheckBox | None = None
        self._gif_colors_label: QLabel | None = None
        self._advanced_panel: AdvancedSettingsPanel | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        tabs = QTabWidget()
        tabs.setObjectName("dialogTabs")

        tabs.addTab(self._jpeg_tab(), "JPEG")
        tabs.addTab(self._png_tab(), "PNG")
        tabs.addTab(self._webp_tab(), "WebP")
        tabs.addTab(self._generic_tab("AVIF"), "AVIF")
        tabs.addTab(self._gif_tab(), "GIF")
        self._advanced_panel = AdvancedSettingsPanel(self._resize, self._transforms)
        tabs.addTab(self._advanced_panel, "Zaawansowane")

        idx = {"jpeg": 0, "png": 1, "webp": 2, "avif": 3, "gif": 4}.get(fmt, 2)
        tabs.setCurrentIndex(idx)
        layout.addWidget(tabs)

        hint = QLabel(FORMAT_EXTENSION_TIPS.get(fmt, ""))
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        reset_row = QHBoxLayout()
        reset_btn = QPushButton("Resetuj")
        reset_btn.setObjectName("btnSecondary")
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._reset)
        reset_row.addWidget(reset_btn)
        reset_row.addStretch()
        layout.addLayout(reset_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_from_opts()

    def _jpeg_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        fl.setSpacing(10)

        self._jpeg_matte_mode = style_dropdown(QComboBox())
        self._jpeg_matte_mode.addItems([
            "Białe tło",
            "Czarne tło",
            "Własny kolor",
            "Gradient (dwa kolory)",
        ])
        self._jpeg_matte_mode.setToolTip(
            "JPG nie ma przezroczystości. Gdy źródło ma „dziury” (np. PNG), "
            "program wypełnia je wybranym tłem przed zapisem."
        )
        self._jpeg_matte_mode.currentIndexChanged.connect(self._sync_matte_controls)
        fl.addRow("Tło pod przezroczystość:", self._jpeg_matte_mode)

        preset_row = QHBoxLayout()
        preset_btn = QPushButton("Preset Inyfinn")
        preset_btn.setObjectName("btnSecondary")
        preset_btn.setToolTip(f"Gradient marki: {BRAND_GRADIENT_1} → {BRAND_GRADIENT_2}")
        preset_btn.clicked.connect(self._apply_brand_gradient_preset)
        preset_row.addWidget(preset_btn)
        preset_row.addStretch()
        preset_wrap = QWidget()
        preset_wrap.setLayout(preset_row)
        fl.addRow("Wstępne:", preset_wrap)

        self._jpeg_gradient_type = style_dropdown(QComboBox())
        self._jpeg_gradient_type.addItems(["Liniowy", "Radialny"])
        self._jpeg_gradient_type.currentIndexChanged.connect(self._update_matte_preview)
        fl.addRow("Typ gradientu:", self._jpeg_gradient_type)

        self._jpeg_gradient_reverse = QCheckBox("Odwróć gradient")
        self._jpeg_gradient_reverse.toggled.connect(self._update_matte_preview)
        fl.addRow(self._jpeg_gradient_reverse)

        self._jpeg_matte_noise = QCheckBox("Szum (dithering) na tle")
        self._jpeg_matte_noise.setToolTip("Dodaje delikatny szum na tle — gładkie przejścia gradientu.")
        fl.addRow(self._jpeg_matte_noise)

        color_row = QHBoxLayout()
        self._jpeg_color_btn = QPushButton("Kolor 1…")
        self._jpeg_color_btn.setObjectName("btnSecondary")
        self._jpeg_color_btn.clicked.connect(lambda: self._pick_color(1))
        self._jpeg_color2_btn = QPushButton("Kolor 2…")
        self._jpeg_color2_btn.setObjectName("btnSecondary")
        self._jpeg_color2_btn.clicked.connect(lambda: self._pick_color(2))
        self._jpeg_preview = QLabel()
        self._jpeg_preview.setFixedSize(100, 100)
        self._jpeg_preview.setObjectName("mattePreview")
        color_row.addWidget(self._jpeg_color_btn)
        color_row.addWidget(self._jpeg_color2_btn)
        color_row.addWidget(self._jpeg_preview)
        color_row.addStretch()
        color_wrap = QWidget()
        color_wrap.setLayout(color_row)
        fl.addRow("Podgląd tła:", color_wrap)

        self._jpeg_lossless_src = QCheckBox("Użyj jakości JPEG z pliku źródłowego, jeśli możliwe")
        fl.addRow(self._jpeg_lossless_src)
        self._subsampling = style_dropdown(QComboBox())
        self._subsampling.addItems(["RGB", "4:2:0 średnie", "4:2:0 silne"])
        self._subsampling.setToolTip("Mniejsza przestrzeń kolorów = mniejszy plik, lekka utrata szczegółów.")
        fl.addRow("Przestrzeń kolorów:", self._subsampling)
        self._jpeg_progressive = QCheckBox("Postępowy JPEG")
        self._jpeg_progressive.setToolTip("Plik ładuje się stopniowo w przeglądarce (jak rozmyty podgląd).")
        fl.addRow(self._jpeg_progressive)
        self._keep_meta = QCheckBox("Zachowaj dane EXIF / IPTC")
        fl.addRow(self._keep_meta)
        return w

    def _png_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self._png_mode = style_dropdown(QComboBox())
        self._png_mode.addItems([
            "Auto (z suwaka jakości)",
            "PNG-8 (mała paleta kolorów)",
            "PNG-24 (pełne kolory)",
        ])
        self._png_mode.setToolTip(
            "PNG-8 = mniejszy plik, ograniczona liczba kolorów. "
            "PNG-24 = pełna jakość, większy plik. Auto dobiera z suwaka Jakość."
        )
        fl.addRow("Tryb PNG:", self._png_mode)
        self._png_lossless = QCheckBox("Tylko bezstratny (oxipng)")
        self._png_lossless.setToolTip("Bez pngquant — tylko lekka optymalizacja bez utraty jakości.")
        fl.addRow(self._png_lossless)
        cb = QCheckBox("Zachowaj dane EXIF / IPTC")
        cb.setChecked(self._opts.keep_metadata)
        fl.addRow(cb)
        return w

    def _webp_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self._webp_lossless = QCheckBox("Bezstratny WebP")
        self._webp_lossless.setToolTip("Większy plik, zero strat — jak archiwum.")
        fl.addRow(self._webp_lossless)
        cb = QCheckBox("Zachowaj dane EXIF / IPTC")
        cb.setChecked(self._opts.keep_metadata)
        fl.addRow(cb)
        return w

    def _gif_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self._gif_dither = QCheckBox("Dithering (szum — gładkie przejścia kolorów)")
        self._gif_dither.setToolTip(
            "Dithering dodaje drobny szum, żeby gradienty wyglądały ładniej przy małej liczbie kolorów."
        )
        fl.addRow(self._gif_dither)

        self._gif_from_quality = QCheckBox("Lossy i kolory z suwaka jakości")
        self._gif_from_quality.setToolTip(
            "Gdy włączone, lossy i liczba kolorów są liczone z głównego suwaka Jakość (jak PNG)."
        )
        self._gif_from_quality.toggled.connect(self._sync_gif_controls)
        fl.addRow(self._gif_from_quality)

        self._gif_lossy = QSpinBox()
        self._gif_lossy.setRange(0, 200)
        self._gif_lossy.setToolTip("Lossy usuwa niewidoczne detale — mniejszy plik. 0 = wyłączone.")
        fl.addRow("Lossy (0–200):", self._gif_lossy)

        self._gif_colors_label = QLabel()
        self._gif_colors_label.setObjectName("hintLabel")
        fl.addRow("Liczba kolorów:", self._gif_colors_label)

        cb = QCheckBox("Zachowaj dane EXIF / IPTC")
        cb.setChecked(self._opts.keep_metadata)
        fl.addRow(cb)
        return w

    def _generic_tab(self, _name: str) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        cb = QCheckBox("Zachowaj dane EXIF / IPTC")
        cb.setChecked(self._opts.keep_metadata)
        fl.addRow(cb)
        return w

    def _apply_brand_gradient_preset(self) -> None:
        if self._jpeg_matte_mode:
            self._jpeg_matte_mode.setCurrentIndex(3)
        self._opts.jpeg_matte_color = BRAND_GRADIENT_1
        self._opts.jpeg_matte_color2 = BRAND_GRADIENT_2
        if self._jpeg_gradient_type:
            self._jpeg_gradient_type.setCurrentIndex(0)
        self._sync_matte_controls()

    def _matte_mode_index(self, mode: str) -> int:
        return {"white": 0, "black": 1, "custom": 2, "gradient": 3}.get(mode, 0)

    def _matte_mode_value(self, index: int) -> str:
        return ["white", "black", "custom", "gradient"][index]

    def _gradient_type_value(self, index: int) -> str:
        return ["linear", "radial"][index]

    def _sync_matte_controls(self) -> None:
        if not self._jpeg_matte_mode:
            return
        idx = self._jpeg_matte_mode.currentIndex()
        custom = idx in (2, 3)
        gradient = idx == 3
        if self._jpeg_color_btn:
            self._jpeg_color_btn.setEnabled(custom)
        if self._jpeg_color2_btn:
            self._jpeg_color2_btn.setEnabled(gradient)
        if self._jpeg_gradient_type:
            self._jpeg_gradient_type.setEnabled(gradient)
        if self._jpeg_gradient_reverse:
            self._jpeg_gradient_reverse.setEnabled(gradient)
        self._update_matte_preview()

    def _sync_gif_controls(self) -> None:
        auto = bool(self._gif_from_quality and self._gif_from_quality.isChecked())
        if self._gif_lossy:
            self._gif_lossy.setEnabled(not auto)
        self._update_gif_labels()

    def _update_gif_labels(self) -> None:
        if not self._gif_colors_label:
            return
        q = self._opts.quality
        colors = palette_colors_for_quality(q)
        lossy = gif_lossy_for_quality(q)
        auto = bool(self._gif_from_quality and self._gif_from_quality.isChecked())
        if auto:
            self._gif_colors_label.setText(f"{colors} (z jakości {q}%)")
            if self._gif_lossy:
                self._gif_lossy.blockSignals(True)
                self._gif_lossy.setValue(lossy)
                self._gif_lossy.blockSignals(False)
        else:
            self._gif_colors_label.setText(str(self._opts.gif_max_colors))

    def _update_matte_preview(self) -> None:
        if not self._jpeg_preview or not self._jpeg_matte_mode:
            return
        idx = self._jpeg_matte_mode.currentIndex()
        c1 = self._opts.jpeg_matte_color
        c2 = self._opts.jpeg_matte_color2
        gtype = "linear"
        reverse = False
        if self._jpeg_gradient_type:
            gtype = self._gradient_type_value(self._jpeg_gradient_type.currentIndex())
        if self._jpeg_gradient_reverse:
            reverse = self._jpeg_gradient_reverse.isChecked()
        if idx == 0:
            self._jpeg_preview.setStyleSheet(_swatch_style("#ffffff"))
        elif idx == 1:
            self._jpeg_preview.setStyleSheet(_swatch_style("#000000"))
        elif idx == 3:
            self._jpeg_preview.setStyleSheet(
                _preview_gradient_style(c1, c2, gradient_type=gtype, reverse=reverse)
            )
        else:
            self._jpeg_preview.setStyleSheet(_swatch_style(c1))

    def _pick_color(self, which: int) -> None:
        from PySide6.QtWidgets import QColorDialog

        start = self._opts.jpeg_matte_color if which == 1 else self._opts.jpeg_matte_color2
        color = QColorDialog.getColor(QColor(start), self, "Wybierz kolor tła")
        if not color.isValid():
            return
        hex_color = color.name()
        if which == 1:
            self._opts.jpeg_matte_color = hex_color
        else:
            self._opts.jpeg_matte_color2 = hex_color
        self._update_matte_preview()

    def _load_from_opts(self) -> None:
        if self._jpeg_progressive:
            self._jpeg_progressive.setChecked(self._opts.progressive)
        if self._keep_meta:
            self._keep_meta.setChecked(self._opts.keep_metadata)
        if self._webp_lossless:
            self._webp_lossless.setChecked(self._opts.lossless)
        if self._png_lossless:
            self._png_lossless.setChecked(self._opts.lossless)
        if self._jpeg_matte_mode:
            self._jpeg_matte_mode.setCurrentIndex(self._matte_mode_index(self._opts.jpeg_matte_mode))
        if self._jpeg_gradient_type:
            gmap = {"linear": 0, "radial": 1}
            self._jpeg_gradient_type.setCurrentIndex(gmap.get(self._opts.jpeg_gradient_type, 0))
        if self._jpeg_gradient_reverse:
            self._jpeg_gradient_reverse.setChecked(self._opts.jpeg_gradient_reverse)
        if self._jpeg_matte_noise:
            self._jpeg_matte_noise.setChecked(self._opts.jpeg_matte_noise)
        if self._png_mode:
            mode_map = {"auto": 0, "png8": 1, "png24": 2}
            self._png_mode.setCurrentIndex(mode_map.get(self._opts.png_mode, 0))
        if self._gif_dither:
            self._gif_dither.setChecked(self._opts.gif_dither)
        if self._gif_lossy:
            self._gif_lossy.setValue(self._opts.gif_lossy)
        if self._gif_from_quality:
            self._gif_from_quality.setChecked(self._opts.gif_from_quality)
        self._sync_matte_controls()
        self._sync_gif_controls()

    def _reset(self) -> None:
        self._opts = FormatOptions()
        self._load_from_opts()
        if self._advanced_panel:
            self._advanced_panel.reset_all()

    def get_options(self) -> FormatOptions:
        if self._jpeg_progressive:
            self._opts.progressive = self._jpeg_progressive.isChecked()
        if self._keep_meta:
            self._opts.keep_metadata = self._keep_meta.isChecked()
        if self._webp_lossless:
            self._opts.lossless = self._webp_lossless.isChecked()
        if self._png_lossless:
            self._opts.lossless = self._png_lossless.isChecked()
        if self._jpeg_matte_mode:
            self._opts.jpeg_matte_mode = self._matte_mode_value(self._jpeg_matte_mode.currentIndex())
        if self._jpeg_gradient_type:
            self._opts.jpeg_gradient_type = self._gradient_type_value(
                self._jpeg_gradient_type.currentIndex()
            )
        if self._jpeg_gradient_reverse:
            self._opts.jpeg_gradient_reverse = self._jpeg_gradient_reverse.isChecked()
        if self._jpeg_matte_noise:
            self._opts.jpeg_matte_noise = self._jpeg_matte_noise.isChecked()
        if self._png_mode:
            modes = ["auto", "png8", "png24"]
            self._opts.png_mode = modes[self._png_mode.currentIndex()]
        if self._gif_dither:
            self._opts.gif_dither = self._gif_dither.isChecked()
        if self._gif_from_quality:
            self._opts.gif_from_quality = self._gif_from_quality.isChecked()
        if self._gif_lossy:
            self._opts.gif_lossy = self._gif_lossy.value()
        if self._opts.gif_from_quality:
            self._opts.gif_max_colors = palette_colors_for_quality(self._opts.quality)
            self._opts.gif_lossy = gif_lossy_for_quality(self._opts.quality)
        return self._opts

    def get_resize(self) -> ResizeOptions:
        if self._advanced_panel:
            return self._advanced_panel.get_resize()
        return self._resize

    def get_transforms(self) -> TransformOptions:
        if self._advanced_panel:
            return self._advanced_panel.get_transforms()
        return self._transforms
