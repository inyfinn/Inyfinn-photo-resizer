"""Opcje formatu wyjściowego — po polsku."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.core.job import FormatOptions


class FormatSettingsDialog(AppDialog):
    def __init__(self, fmt: str, opts: FormatOptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje formatu wyjściowego")
        self.setMinimumWidth(420)
        self._opts = opts
        self._fmt = fmt

        self._jpeg_progressive: QCheckBox | None = None
        self._jpeg_lossless_src: QCheckBox | None = None
        self._png_lossless: QCheckBox | None = None
        self._webp_lossless: QCheckBox | None = None
        self._keep_meta: QCheckBox | None = None
        self._subsampling: QComboBox | None = None

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setObjectName("dialogTabs")

        tabs.addTab(self._jpeg_tab(), "JPEG")
        tabs.addTab(self._png_tab(), "PNG")
        tabs.addTab(self._webp_tab(), "WebP")
        tabs.addTab(self._generic_tab("AVIF"), "AVIF")
        tabs.addTab(self._generic_tab("GIF"), "GIF")

        idx = {"jpeg": 0, "png": 1, "webp": 2, "avif": 3, "gif": 4}.get(fmt, 2)
        tabs.setCurrentIndex(idx)
        layout.addWidget(tabs)

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
        self._jpeg_lossless_src = QCheckBox("Użyj jakości JPEG z pliku źródłowego, jeśli możliwe")
        fl.addRow(self._jpeg_lossless_src)
        self._subsampling = QComboBox()
        self._subsampling.addItems(["RGB", "4:2:0 średnie", "4:2:0 silne"])
        fl.addRow("Przestrzeń kolorów:", self._subsampling)
        self._jpeg_progressive = QCheckBox("Postępowy JPEG")
        self._jpeg_progressive.setChecked(self._opts.progressive)
        fl.addRow(self._jpeg_progressive)
        self._keep_meta = QCheckBox("Zachowaj dane EXIF / IPTC")
        self._keep_meta.setChecked(self._opts.keep_metadata)
        fl.addRow(self._keep_meta)
        return w

    def _png_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self._png_lossless = QCheckBox("Tylko bezstratny (oxipng)")
        fl.addRow(self._png_lossless)
        cb = QCheckBox("Zachowaj dane EXIF / IPTC")
        cb.setChecked(self._opts.keep_metadata)
        fl.addRow(cb)
        return w

    def _webp_tab(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)
        self._webp_lossless = QCheckBox("Bezstratny WebP")
        fl.addRow(self._webp_lossless)
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

    def _load_from_opts(self) -> None:
        if self._jpeg_progressive:
            self._jpeg_progressive.setChecked(self._opts.progressive)
        if self._keep_meta:
            self._keep_meta.setChecked(self._opts.keep_metadata)
        if self._webp_lossless:
            self._webp_lossless.setChecked(self._opts.lossless)
        if self._png_lossless:
            self._png_lossless.setChecked(self._opts.lossless)

    def _reset(self) -> None:
        self._opts = FormatOptions()
        self._load_from_opts()

    def get_options(self) -> FormatOptions:
        if self._jpeg_progressive:
            self._opts.progressive = self._jpeg_progressive.isChecked()
        if self._keep_meta:
            self._opts.keep_metadata = self._keep_meta.isChecked()
        if self._webp_lossless:
            self._opts.lossless = self._webp_lossless.isChecked()
        if self._png_lossless:
            self._opts.lossless = self._png_lossless.isChecked()
        return self._opts
