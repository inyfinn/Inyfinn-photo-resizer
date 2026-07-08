"""Główne okno — układ FastStone, siatka wierszy/kolumn."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from inyfinn_resizer.app.dialogs.message_boxes import (
    ask_yes_no,
    show_about,
    show_critical,
    show_info,
    show_warning,
)

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.dialogs.results_dialog import ResultsDialog, WizResultsDialog
from inyfinn_resizer.core.wiz_sequence import discover_wiz_folders
from inyfinn_resizer.app.widgets.format_multi_combo import FormatMultiCombo
from inyfinn_resizer.app.widgets.layout_helpers import (
    ROW_GAP,
    SECTION_GAP,
    action_button,
    add_form_row,
    add_grid_field,
    add_grid_span,
    field_group,
    make_section,
    make_settings_grid,
    slider_control,
    tool_button_row,
)
from inyfinn_resizer.core.formats.registry import is_image_file, output_extension
from inyfinn_resizer.core.job import (
    BatchSettings,
    FormatOptions,
    JobSpec,
    MetadataPolicy,
    RenameRule,
    ResizeOptions,
    TransformOptions,
)
from inyfinn_resizer.core.pipeline import build_output_path
from inyfinn_resizer.core.presets import apply_preset, load_preset, save_preset, settings_to_dict
from inyfinn_resizer.core.rename.templates import preview_rename
from inyfinn_resizer.workers.batch_worker import BatchThread, BatchWorker
from inyfinn_resizer.workers.wiz_worker import WizThread, WizWorker


DEFAULT_WINDOW_WIDTH = 1240
DEFAULT_WINDOW_HEIGHT = 940
MIN_WINDOW_WIDTH = 1080
MIN_WINDOW_HEIGHT = 760


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Inyfinn Photo Resizer {__version__}")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setAcceptDrops(True)
        self._initial_size_applied = False
        self._settings_scroll: QScrollArea | None = None
        self._settings_body: QWidget | None = None
        self._main_splitter: QSplitter | None = None

        self._queue: list[Path] = []
        self._base_root: Path | None = None
        self._format_opts = FormatOptions(quality=85)
        self._resize = ResizeOptions()
        self._transforms = TransformOptions()
        self._metadata = MetadataPolicy()
        self._rename = RenameRule()
        self._batch = BatchSettings()
        self._batch_thread: BatchThread | None = None
        self._wiz_thread: WizThread | None = None
        self._folder_queue: list[Path] = []
        self._theme = "light"

        self._build_menu()
        self._build_ui()
        self._sync_png_colors_from_quality()
        self._update_advanced_summary()
        self.statusBar().showMessage(f"Inyfinn Photo Resizer {__version__} — przeciągnij zdjęcia na listę po lewej")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._initial_size_applied:
            self._initial_size_applied = True
            QTimer.singleShot(0, self._fit_initial_window_size)

    def _fit_initial_window_size(self) -> None:
        """Dopasuj okno przy starcie — cały panel ustawień bez przewijania."""
        from PySide6.QtWidgets import QApplication

        scroll = self._settings_scroll
        if scroll is None:
            return

        screen = self.screen().availableGeometry()
        max_w = int(screen.width() * 0.96)
        max_h = int(screen.height() * 0.96)
        width = min(DEFAULT_WINDOW_WIDTH, max_w)
        height = min(DEFAULT_WINDOW_HEIGHT, max_h)
        self.resize(width, height)

        if splitter := self._main_splitter:
            right_w = max(500, int(width * 0.42))
            splitter.setSizes([width - right_w, right_w])

        QApplication.processEvents()

        bar = scroll.verticalScrollBar()
        for _ in range(24):
            if bar.maximum() <= 0 or height >= max_h:
                break
            height = min(height + 48, max_h)
            self.resize(width, height)
            QApplication.processEvents()

    @staticmethod
    def _make_panel(title: str, object_name: str = "panel") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setFrameShape(QFrame.StyledPanel)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(6)
        lbl = QLabel(title)
        lbl.setObjectName("panelTitle")
        outer.addWidget(lbl)
        return frame, outer

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Plik")
        file_menu.addAction("Wczytaj ustawienia…", self._load_preset)
        file_menu.addAction("Zapisz ustawienia…", self._save_preset)
        file_menu.addSeparator()
        file_menu.addAction("W&yjście", self.close)

        theme_menu = menubar.addMenu("&Motyw")
        theme_menu.addAction("Jasny", lambda: self._set_theme("light"))
        theme_menu.addAction("Ciemny", lambda: self._set_theme("dark"))

        help_menu = menubar.addMenu("Pomo&c")
        help_menu.addAction("O programie", self._about)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("Inyfinn Photo Resizer")
        title.setObjectName("appTitle")
        version_lbl = QLabel(f"Wersja {__version__}")
        version_lbl.setObjectName("versionBadge")
        title_col.addWidget(title)
        title_col.addWidget(version_lbl)
        header.addLayout(title_col)
        header.addStretch()
        self.theme_btn = QPushButton("Ciemny motyw")
        self.theme_btn.setObjectName("themeToggle")
        self.theme_btn.setFixedHeight(36)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header.addWidget(self.theme_btn)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        convert_tab = QWidget()
        convert_layout = QVBoxLayout(convert_tab)
        convert_layout.setContentsMargins(0, 8, 0, 0)
        convert_layout.addWidget(self._build_convert_body())
        self.tabs.addTab(convert_tab, "Konwersja wsadowa")
        self.tabs.addTab(self._build_rename_tab(), "Zmiana nazw")
        root.addWidget(self.tabs, stretch=1)

    def _build_convert_body(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        self._main_splitter = splitter

        # —— Lewy panel: lista plików ——
        left_box, left_layout = self._make_panel("Lista plików", "dropPanel")

        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)
        self.queue_label = QLabel("0 plików")
        self.queue_label.setObjectName("queueCount")
        meta_row.addWidget(self.queue_label)
        meta_row.addStretch()
        sort_lbl = QLabel("Sortuj:")
        sort_lbl.setObjectName("formLabelInline")
        self.sort_combo = QComboBox()
        self.sort_combo.setMinimumWidth(160)
        self.sort_combo.addItems(["Bez sortowania", "Nazwa A→Z", "Nazwa Z→A", "Rozmiar"])
        self.sort_combo.currentIndexChanged.connect(self._sort_queue)
        meta_row.addWidget(sort_lbl)
        meta_row.addWidget(self.sort_combo)
        left_layout.addLayout(meta_row)

        hint = QLabel("Przeciągnij zdjęcia tutaj lub użyj przycisków poniżej.")
        hint.setObjectName("dropHint")
        hint.setWordWrap(True)
        left_layout.addWidget(hint)

        left_layout.addLayout(tool_button_row([
            ("Dodaj pliki", self._add_files_dialog),
            ("Dodaj folder", self._add_folder_dialog),
            ("Usuń", self._remove_selected),
            ("Wyczyść", self._clear_queue),
        ]))

        self.input_tree = QTreeWidget()
        self.input_tree.setObjectName("inputList")
        self.input_tree.setHeaderLabels(["Nazwa pliku", "Rozmiar"])
        self.input_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.input_tree.setRootIsDecorated(False)
        self.input_tree.setAlternatingRowColors(True)
        self.input_tree.setColumnWidth(0, 300)
        self.input_tree.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.input_tree, stretch=1)

        splitter.addWidget(left_box)

        # —— Prawy panel: ustawienia ——
        right_shell, right_layout = self._make_panel("Ustawienia konwersji", "panel")
        right_shell.setMinimumWidth(460)
        right_layout.addWidget(self._build_settings_panel(), stretch=1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(10)
        right_layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        self.convert_btn = action_button("Konwertuj", "primaryBtn", self._start_convert)
        close_btn = action_button("Zamknij", "btnSecondary", self.close)
        btn_row.addWidget(self.convert_btn)
        btn_row.addWidget(close_btn)
        right_layout.addLayout(btn_row)

        splitter.addWidget(right_shell)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([640, 520])
        return splitter

    def _build_settings_panel(self) -> QScrollArea:
        scroll = QScrollArea()
        self._settings_scroll = scroll
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFocusPolicy(Qt.NoFocus)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        body = QWidget()
        self._settings_body = body
        body.setObjectName("settingsBody")
        body.setMinimumWidth(420)
        root = QVBoxLayout(body)
        root.setSpacing(SECTION_GAP)
        root.setContentsMargins(0, 0, 6, 16)

        # —— Format wyjściowy ——
        fmt_box, fmt_lay = make_section(
            "Format wyjściowy",
            "Wybierz format(y) zapisu. Przy wielu formatach możesz rozdzielić pliki do podfolderów.",
        )
        fmt_grid = make_settings_grid()

        self.format_combo = FormatMultiCombo()
        self.format_combo.selectionChanged.connect(self._on_formats_changed)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        fmt_row.addWidget(self.format_combo, stretch=1)
        self.settings_btn = QPushButton("Ustawienia formatu…")
        self.settings_btn.setObjectName("btnSecondary")
        self.settings_btn.setMinimumHeight(36)
        self.settings_btn.clicked.connect(self._open_format_settings)
        fmt_row.addWidget(self.settings_btn)
        fmt_controls = QWidget()
        fmt_controls.setLayout(fmt_row)
        self.fmt_wrap = fmt_controls
        add_grid_span(fmt_grid, 0, field_group("Format", fmt_controls))

        self.segregate_cb = QCheckBox("Segreguj do podfolderów (webp/, jpg/…)")
        self.segregate_cb.setChecked(False)
        self.segregate_cb.setToolTip(
            "Przy eksporcie do wielu formatów zapisuje pliki w podfolderach. "
            "Przy jednym formacie opcja jest ignorowana."
        )
        add_grid_span(fmt_grid, 1, self.segregate_cb)
        fmt_lay.addLayout(fmt_grid)
        root.addWidget(fmt_box)

        # —— Kompresja ——
        comp_box, comp_lay = make_section(
            "Kompresja",
            "Jakość wpływa na JPG/WebP/AVIF. Kolory PNG — paleta przy zapisie PNG.",
        )
        comp_grid = make_settings_grid()

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        self.quality_label = QLabel("85")
        qual_field = field_group(
            "Jakość",
            slider_control(self.quality_slider, self.quality_label),
            "Wyższa wartość = lepsza jakość, większy plik.",
        )
        add_grid_field(comp_grid, 0, 0, qual_field)

        self.png_colors_slider = QSlider(Qt.Horizontal)
        self.png_colors_slider.setRange(32, 256)
        self.png_colors_slider.setValue(256)
        self.png_colors_slider.valueChanged.connect(self._on_png_colors_changed)
        self.png_colors_label = QLabel("256")
        colors_slider_row = slider_control(self.png_colors_slider, self.png_colors_label)
        colors_extras = QHBoxLayout()
        colors_extras.setContentsMargins(0, 0, 0, 0)
        colors_extras.setSpacing(8)
        colors_extras.addWidget(colors_slider_row, stretch=1)
        self.png_colors_auto_cb = QCheckBox("Z jakości")
        self.png_colors_auto_cb.setChecked(True)
        self.png_colors_auto_cb.setToolTip(
            "Automatycznie: 256 kolorów od 80%, 192 przy 50%, min. 32 przy 5% jakości."
        )
        self.png_colors_auto_cb.toggled.connect(self._on_png_colors_auto)
        self.png_colors_slider.setEnabled(False)
        colors_extras.addWidget(self.png_colors_auto_cb)
        colors_wrap = QWidget()
        colors_wrap.setLayout(colors_extras)
        colors_field = field_group(
            "Kolory PNG",
            colors_wrap,
            "Liczba kolorów w palecie PNG (32–256).",
        )
        add_grid_field(comp_grid, 0, 1, colors_field)
        comp_lay.addLayout(comp_grid)
        root.addWidget(comp_box)

        # —— Rozmiar ——
        size_box, size_lay = make_section(
            "Rozmiar obrazu",
            "Szybki preset rozmiaru. Pełna kontrola (bok, filtr, obrót) — w sekcji Zaawansowane.",
        )
        self.size_combo = QComboBox()
        self.size_combo.setMinimumHeight(36)
        self.size_combo.addItems([
            "Oryginalny rozmiar",
            "Maks. 1800 px (szerokość)",
            "Maks. 1200 px",
            "50%",
        ])
        self.size_combo.currentIndexChanged.connect(self._on_size_preset_changed)
        size_lay.addWidget(field_group("Preset rozmiaru", self.size_combo))
        root.addWidget(size_box)

        # —— Sekwencja wizek ——
        wiz_box, wiz_lay = make_section(
            "Sekwencja wizek",
            "Bootstrap + kompresja pakietu XL / L / S / SKLEP in-place w folderze źródłowym.",
        )
        self.wiz_sequence_cb = QCheckBox("Konwertuj na sekwencję wizek")
        self.wiz_sequence_cb.setToolTip(
            "Ignoruje format z listy i folder wyjściowy — eksport PNG/JPG wg skryptu wizek."
        )
        self.wiz_sequence_cb.toggled.connect(self._on_wiz_mode_changed)
        wiz_lay.addWidget(self.wiz_sequence_cb)
        root.addWidget(wiz_box)

        # —— Folder wyjściowy ——
        out_box, out_lay = make_section(
            "Zapis",
            "Folder docelowy dla zwykłej konwersji. Przy wizek — pliki zostają w folderze źródłowym.",
        )
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Wybierz folder docelowy…")
        self.output_dir_edit.setMinimumHeight(36)
        browse_out = QPushButton("Przeglądaj…")
        browse_out.setObjectName("btnSecondary")
        browse_out.setMinimumHeight(36)
        browse_out.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_dir_edit, stretch=1)
        out_row.addWidget(browse_out)
        out_controls = QWidget()
        out_controls.setLayout(out_row)
        out_lay.addWidget(field_group("Folder wyjściowy", out_controls))
        root.addWidget(out_box)

        # —— Zaawansowane ——
        adv_box, adv_lay = make_section(
            "Zaawansowane",
            "Obrót, odbicia, korekcje kolorów oraz szczegółowa zmiana rozmiaru.",
        )
        self.advanced_summary = QLabel()
        self.advanced_summary.setObjectName("advancedSummary")
        self.advanced_summary.setWordWrap(True)
        adv_lay.addWidget(self.advanced_summary)
        self.advanced_btn = QPushButton("Edytuj opcje zaawansowane…")
        self.advanced_btn.setObjectName("btnSecondary")
        self.advanced_btn.setMinimumHeight(36)
        self.advanced_btn.clicked.connect(self._open_advanced)
        adv_lay.addWidget(self.advanced_btn)
        root.addWidget(adv_box)

        # —— Więcej opcji (zwijane) ——
        more_box, more_lay = make_section("Dodatkowe opcje", "Ustawienia wsadowe i podgląd miniatury.")
        self.more_toggle = QCheckBox("Pokaż dodatkowe opcje")
        self.more_toggle.setObjectName("moreToggle")
        self.more_toggle.setChecked(False)
        more_lay.addWidget(self.more_toggle)

        self.more_content = QFrame()
        self.more_content.setObjectName("moreOptions")
        self.more_content.setVisible(False)
        self.more_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        more_inner = QVBoxLayout(self.more_content)
        more_inner.setContentsMargins(0, 4, 0, 0)
        more_inner.setSpacing(8)
        for text, attr, checked in [
            ("Zachowaj strukturę folderów", "preserve_cb", True),
            ("Zachowaj datę i godzinę", "keep_dates_cb", True),
            ("Pytaj przed nadpisaniem", "overwrite_cb", True),
            ("Wiele plików naraz (szybciej)", "parallel_cb", True),
        ]:
            cb = QCheckBox(text)
            cb.setChecked(checked)
            setattr(self, attr, cb)
            more_inner.addWidget(cb)
        self.preview_cb = QCheckBox("Podgląd miniatury na liście")
        self.preview_cb.setChecked(True)
        more_inner.addWidget(self.preview_cb)
        prev_row = QHBoxLayout()
        prev_row.setSpacing(10)
        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewBox")
        self.preview_label.setFixedSize(72, 72)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.size_info = QLabel("")
        self.size_info.setObjectName("previewMeta")
        self.size_info.setWordWrap(True)
        prev_row.addWidget(self.preview_label)
        prev_row.addWidget(self.size_info, stretch=1)
        more_inner.addLayout(prev_row)
        self.more_toggle.toggled.connect(self.more_content.setVisible)
        more_lay.addWidget(self.more_content)
        root.addWidget(more_box)

        scroll.setWidget(body)
        return scroll

    def _build_rename_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(ROW_GAP)
        layout.addWidget(QLabel("Szablon nazwy (np. {name}_{counter:04d}):"))
        self.rename_template = QLineEdit("{name}_{counter:04d}")
        self.rename_template.setMinimumHeight(36)
        layout.addWidget(self.rename_template)
        sr = QGridLayout()
        sr.setHorizontalSpacing(10)
        sr.setVerticalSpacing(ROW_GAP)
        self.rename_search = QLineEdit()
        self.rename_replace = QLineEdit()
        add_form_row(sr, 0, "Szukaj:", self.rename_search)
        add_form_row(sr, 1, "Zamień na:", self.rename_replace)
        layout.addLayout(sr)
        self.rename_preview = QListWidget()
        layout.addWidget(self.rename_preview, stretch=1)
        preview_btn = QPushButton("Podgląd nazw")
        preview_btn.setObjectName("btnSecondary")
        preview_btn.setMinimumHeight(36)
        preview_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        preview_btn.clicked.connect(self._preview_rename)
        layout.addWidget(preview_btn)
        return w

    def _toggle_theme(self) -> None:
        self._set_theme("dark" if self._theme == "light" else "light")

    def _set_theme(self, theme: str) -> None:
        from PySide6.QtWidgets import QApplication

        from inyfinn_resizer.app.themes import apply_theme

        self._theme = theme
        apply_theme(QApplication.instance(), theme)
        self.theme_btn.setText("Jasny motyw" if theme == "dark" else "Ciemny motyw")

    def _on_wiz_mode_changed(self, enabled: bool) -> None:
        self.format_combo.setEnabled(not enabled)
        self.settings_btn.setEnabled(not enabled)
        self.fmt_wrap.setEnabled(not enabled)
        if enabled:
            self.segregate_cb.setChecked(False)
            self.segregate_cb.setEnabled(False)
            self.output_dir_edit.setEnabled(False)
            self.convert_btn.setText("Konwertuj wizek")
        else:
            self.segregate_cb.setEnabled(True)
            self.output_dir_edit.setEnabled(True)
            self.convert_btn.setText("Konwertuj")

    def _on_formats_changed(self) -> None:
        """Odświeżenie UI po zmianie formatów — segregacja pozostaje klikalna."""
        return

    def _selected_formats(self) -> list[str]:
        fmts = self.format_combo.selected_formats()
        return fmts if fmts else ["webp"]

    def _on_quality_changed(self, v: int) -> None:
        self.quality_label.setText(str(v))
        self._format_opts.quality = v
        if self.png_colors_auto_cb.isChecked():
            self._sync_png_colors_from_quality()

    def _sync_png_colors_from_quality(self) -> None:
        from inyfinn_resizer.core.compressors.png import png_max_colors_for_quality

        colors = png_max_colors_for_quality(self.quality_slider.value())
        self.png_colors_slider.blockSignals(True)
        self.png_colors_slider.setValue(colors)
        self.png_colors_slider.blockSignals(False)
        self.png_colors_label.setText(str(colors))
        self._format_opts.png_max_colors = colors

    def _on_png_colors_changed(self, v: int) -> None:
        self.png_colors_label.setText(str(v))
        self._format_opts.png_max_colors = v

    def _on_png_colors_auto(self, enabled: bool) -> None:
        self._format_opts.png_colors_auto = enabled
        self.png_colors_slider.setEnabled(not enabled)
        if enabled:
            self._sync_png_colors_from_quality()

    def _format_size(self, path: Path) -> str:
        try:
            kb = path.stat().st_size / 1024
            if kb >= 1024:
                return f"{kb / 1024:.1f} MB"
            return f"{kb:.0f} KB"
        except OSError:
            return "-"

    def _add_path_to_queue(self, path: Path) -> None:
        if path in self._queue:
            return
        self._queue.append(path)
        item = QTreeWidgetItem([path.name, self._format_size(path)])
        item.setData(0, Qt.UserRole, str(path))
        item.setData(0, Qt.UserRole + 1, "file")
        item.setToolTip(0, str(path))
        self.input_tree.addTopLevelItem(item)
        if self._base_root is None:
            self._base_root = path.parent
        self._update_queue_label()

    def _add_folder_to_queue(self, folder: Path) -> None:
        folder = folder.resolve()
        if folder in self._folder_queue:
            return
        self._folder_queue.append(folder)
        item = QTreeWidgetItem([f"📁 {folder.name}", "folder"])
        item.setData(0, Qt.UserRole, str(folder))
        item.setData(0, Qt.UserRole + 1, "folder")
        item.setToolTip(0, str(folder))
        self.input_tree.addTopLevelItem(item)
        if self._base_root is None:
            self._base_root = folder
        self._update_queue_label()

    def _paths_from_items(self, items: list[QTreeWidgetItem]) -> list[Path]:
        paths = []
        for item in items:
            data = item.data(0, Qt.UserRole)
            if data:
                paths.append(Path(data))
        return paths

    def _item_kind(self, item: QTreeWidgetItem) -> str:
        kind = item.data(0, Qt.UserRole + 1)
        return str(kind) if kind else "file"

    def _add_files_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Wybierz zdjęcia",
            "",
            "Obrazy (*.jpg *.jpeg *.png *.gif *.bmp *.tif *.tiff *.webp *.avif *.heic);;Wszystkie (*.*)",
        )
        for f in files:
            p = Path(f)
            if is_image_file(p):
                self._add_path_to_queue(p)

    def _add_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder ze zdjęciami")
        if not folder:
            return
        root = Path(folder)
        if self.wiz_sequence_cb.isChecked():
            self._add_folder_to_queue(root)
            return
        self._base_root = root
        for f in sorted(root.rglob("*")):
            if f.is_file() and is_image_file(f):
                self._add_path_to_queue(f)

    def _browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Folder wyjściowy")
        if folder:
            self.output_dir_edit.setText(folder)

    def _remove_selected(self) -> None:
        for item in self.input_tree.selectedItems():
            p = Path(item.data(0, Qt.UserRole))
            if self._item_kind(item) == "folder":
                if p in self._folder_queue:
                    self._folder_queue.remove(p)
            elif p in self._queue:
                self._queue.remove(p)
            idx = self.input_tree.indexOfTopLevelItem(item)
            if idx >= 0:
                self.input_tree.takeTopLevelItem(idx)
        self._update_queue_label()

    def _clear_queue(self) -> None:
        self._queue.clear()
        self._folder_queue.clear()
        self.input_tree.clear()
        self._update_queue_label()
        self.preview_label.clear()
        self.size_info.clear()

    def _sort_queue(self) -> None:
        idx = self.sort_combo.currentIndex()
        if idx == 0:
            return
        items: list[tuple[Path, QTreeWidgetItem]] = []
        for i in range(self.input_tree.topLevelItemCount()):
            item = self.input_tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if data:
                items.append((Path(data), item))
        if idx == 1:
            items.sort(key=lambda x: x[0].name.lower())
        elif idx == 2:
            items.sort(key=lambda x: x[0].name.lower(), reverse=True)
        elif idx == 3:
            items.sort(key=lambda x: x[0].stat().st_size if x[0].is_file() else 0, reverse=True)
        self.input_tree.clear()
        self._queue = []
        for path, _ in items:
            self._add_path_to_queue(path)

    def _update_queue_label(self) -> None:
        n_files = len(self._queue)
        n_folders = len(self._folder_queue)
        if n_folders and not n_files:
            word = "folder" if n_folders == 1 else ("foldery" if 2 <= n_folders % 10 <= 4 else "folderów")
            self.queue_label.setText(f"{n_folders} {word}")
            return
        word = "plik" if n_files == 1 else ("pliki" if 2 <= n_files % 10 <= 4 and (n_files % 100 < 10 or n_files % 100 >= 20) else "plików")
        extra = f", {n_folders} folderów" if n_folders else ""
        self.queue_label.setText(f"{n_files} {word}{extra}")

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous) -> None:
        if not self.preview_cb.isChecked() or current is None:
            return
        if self._item_kind(current) == "folder":
            path = Path(current.data(0, Qt.UserRole))
            self.preview_label.clear()
            self.size_info.setText(f"Folder wizek:\n{path}")
            return
        data = current.data(0, Qt.UserRole)
        if not data:
            return
        path = Path(data)
        pix = QPixmap(str(path))
        if not pix.isNull():
            self.preview_label.setPixmap(
                pix.scaled(112, 112, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self.size_info.setText(f"{path.name}\n{self._format_size(path)}\n{path.parent}")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                if self.wiz_sequence_cb.isChecked():
                    self._add_folder_to_queue(p)
                else:
                    self._base_root = p
                    for f in sorted(p.rglob("*")):
                        if f.is_file() and is_image_file(f):
                            self._add_path_to_queue(f)
            elif p.is_file() and is_image_file(p):
                self._add_path_to_queue(p)
        event.acceptProposedAction()

    def _open_format_settings(self) -> None:
        fmt = self.format_combo.first_selected()
        dlg = FormatSettingsDialog(fmt, self._format_opts, self)
        if dlg.exec():
            self._format_opts = dlg.get_options()

    def _advanced_summary_text(self) -> str:
        from inyfinn_resizer.core.job import ResizeMode

        parts: list[str] = []
        if self._resize.mode == ResizeMode.NONE:
            parts.append("Rozmiar: bez zmian (oryginał)")
        elif self._resize.mode == ResizeMode.PERCENT:
            parts.append(f"Rozmiar: {self._resize.percent}% oryginału")
        elif self._resize.mode == ResizeMode.MAX_DIMENSION:
            parts.append(f"Rozmiar: maks. {self._resize.dimension} px")
        else:
            side = {
                "width": "szerokość",
                "height": "wysokość",
                "longer": "dłuższy bok",
                "shorter": "krótszy bok",
            }.get(self._resize.side or "width", "szerokość")
            parts.append(f"Rozmiar: {self._resize.dimension} px ({side})")

        transforms: list[str] = []
        if self._transforms.rotate:
            transforms.append(f"obrót {self._transforms.rotate}°")
        if self._transforms.flip_h:
            transforms.append("odbicie poziome")
        if self._transforms.flip_v:
            transforms.append("odbicie pionowe")
        if self._transforms.grayscale:
            transforms.append("czarno-biały")
        if self._transforms.sepia:
            transforms.append("sepia")
        if self._transforms.auto_rotate_exif:
            transforms.append("autoobrót EXIF")
        if transforms:
            parts.append("Efekty: " + ", ".join(transforms))
        else:
            parts.append("Efekty: brak")
        return "\n".join(parts)

    def _update_advanced_summary(self) -> None:
        self.advanced_summary.setText(self._advanced_summary_text())

    def _open_advanced(self) -> None:
        dlg = AdvancedOptionsDialog(self._resize, self._transforms, self)
        if dlg.exec():
            self._resize = dlg.get_resize()
            self._transforms = dlg.get_transforms()
            self.size_combo.blockSignals(True)
            self.size_combo.setCurrentIndex(0)
            self.size_combo.blockSignals(False)
            self._update_advanced_summary()

    def _on_size_preset_changed(self) -> None:
        from inyfinn_resizer.core.job import ResizeMode

        idx = self.size_combo.currentIndex()
        if idx == 0:
            if self._resize.mode == ResizeMode.NONE:
                self._resize = ResizeOptions()
        elif idx == 1:
            self._resize = ResizeOptions(mode=ResizeMode.ONE_SIDE, side="width", dimension=1800)
        elif idx == 2:
            self._resize = ResizeOptions(mode=ResizeMode.MAX_DIMENSION, dimension=1200)
        elif idx == 3:
            self._resize = ResizeOptions(mode=ResizeMode.PERCENT, percent=50)
        self._update_advanced_summary()

    def _apply_size_preset(self) -> None:
        from inyfinn_resizer.core.job import ResizeMode

        idx = self.size_combo.currentIndex()
        if idx == 0:
            if self._resize.mode == ResizeMode.NONE:
                self._resize = ResizeOptions()
            return
        if idx == 1:
            self._resize = ResizeOptions(mode=ResizeMode.ONE_SIDE, side="width", dimension=1800)
        elif idx == 2:
            self._resize = ResizeOptions(mode=ResizeMode.MAX_DIMENSION, dimension=1200)
        elif idx == 3:
            self._resize = ResizeOptions(mode=ResizeMode.PERCENT, percent=50)

    def _build_jobs(self) -> list[JobSpec]:
        out_dir = Path(self.output_dir_edit.text()) if self.output_dir_edit.text() else None
        if not out_dir:
            out_dir = self._queue[0].parent / "output" if self._queue else Path.cwd() / "output"
        formats = self._selected_formats()
        segregate = self.segregate_cb.isChecked() and len(formats) > 1
        self._apply_size_preset()
        self._format_opts.quality = self.quality_slider.value()

        jobs = []
        for fmt in formats:
            for inp in self._queue:
                if self.tabs.currentIndex() == 1:
                    name = preview_rename([inp], RenameRule(
                        enabled=True,
                        template=self.rename_template.text(),
                        search=self.rename_search.text(),
                        replace=self.rename_replace.text(),
                    ), fmt)[0][1]
                    if segregate:
                        sub = output_extension(fmt).lstrip(".").lower() or fmt.lower()
                        out = out_dir / sub / name
                    else:
                        out = out_dir / name
                else:
                    out = build_output_path(
                        inp, out_dir, fmt,
                        base_root=self._base_root,
                        preserve_structure=self.preserve_cb.isChecked(),
                        segregate_by_extension=segregate,
                    )
                jobs.append(JobSpec(
                    input_path=inp,
                    output_path=out,
                    output_format=fmt,
                    resize=self._resize,
                    transforms=self._transforms,
                    metadata=self._metadata,
                    format_opts=self._format_opts,
                ))
        return jobs

    def _start_convert(self) -> None:
        if self.wiz_sequence_cb.isChecked():
            self._start_wiz_convert()
            return
        if not self._queue:
            show_warning(self, "Konwersja", "Lista plików jest pusta.")
            return
        if not self.format_combo.selected_formats():
            show_warning(self, "Konwersja", "Zaznacz co najmniej jeden format wyjściowy.")
            return
        jobs = self._build_jobs()
        overwrite = True
        if self.overwrite_cb.isChecked():
            existing = [j for j in jobs if j.output_path.exists()]
            if existing:
                if not ask_yes_no(
                    self,
                    "Nadpisanie",
                    f"{len(existing)} plik(ów) już istnieje. Nadpisać?",
                ):
                    overwrite = False

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(jobs))
        self.progress.setValue(0)
        self._convert_start = time.time()

        worker = BatchWorker(jobs, parallel=self.parallel_cb.isChecked(), overwrite=overwrite)
        self._batch_thread = BatchThread(worker)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.error.connect(lambda e: show_critical(self, "Błąd", e))
        self._batch_thread.start()

    def _start_wiz_convert(self) -> None:
        paths = list(self._folder_queue) + self._queue
        if not paths:
            show_warning(
                self,
                "Sekwencja wizek",
                "Dodaj foldery (lub pliki w folderach docelowych) do listy.",
            )
            return
        folders = discover_wiz_folders(paths)
        if not folders:
            show_warning(
                self,
                "Sekwencja wizek",
                "Nie znaleziono folderów z plikami PNG/JPG.",
            )
            return

        if not ask_yes_no(
            self,
            "Sekwencja wizek",
            f"Przetworzyć {len(folders)} folder(ów) in-place?\n"
            "Pliki zostaną nadpisane w miejscu (bootstrap + kompresja).",
        ):
            return

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(folders))
        self.progress.setValue(0)
        self._convert_start = time.time()

        worker = WizWorker(folders, self.quality_slider.value())
        self._wiz_thread = WizThread(worker)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_wiz_finished)
        worker.error.connect(lambda e: show_critical(self, "Błąd", e))
        self._wiz_thread.start()

    def _on_wiz_finished(self, results) -> None:
        elapsed = time.time() - self._convert_start
        self.convert_btn.setEnabled(True)
        self.progress.setVisible(False)
        ok = sum(1 for r in results if r.status.value == "OK")
        self.statusBar().showMessage(f"Wizki gotowe — {ok}/{len(results)} folderów w {elapsed:.1f} s")
        dlg = WizResultsDialog(results, elapsed, self)
        dlg.exec()

    def _on_progress(self, current: int, total: int, name: str) -> None:
        self.progress.setValue(current)
        self.statusBar().showMessage(f"Przetwarzanie {current}/{total}: {name}")

    def _on_finished(self, results) -> None:
        elapsed = time.time() - self._convert_start
        self.convert_btn.setEnabled(True)
        self.progress.setVisible(False)
        ok = sum(1 for r in results if r.status.value == "OK")
        self.statusBar().showMessage(f"Gotowe — {ok}/{len(results)} plików w {elapsed:.1f} s")
        dlg = ResultsDialog(results, elapsed, self)
        dlg.exec()

    def _preview_rename(self) -> None:
        self.tabs.setCurrentIndex(1)
        self.rename_preview.clear()
        if not self._queue:
            show_info(
                self,
                "Podgląd nazw",
                "Lista plików jest pusta.\nDodaj pliki na zakładce „Konwersja wsadowa”.",
            )
            return
        fmt = self.format_combo.first_selected()
        rule = RenameRule(
            enabled=True,
            template=self.rename_template.text().strip() or "{name}_{counter:04d}",
            search=self.rename_search.text(),
            replace=self.rename_replace.text(),
        )
        rows = preview_rename(self._queue, rule, fmt)
        if not rows:
            self.rename_preview.addItem("Brak wyników — sprawdź szablon nazwy.")
            return
        for old, new in rows:
            self.rename_preview.addItem(f"{old}  →  {new}")
        self.statusBar().showMessage(f"Podgląd nazw: {len(rows)} pozycji")

    def _load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Wczytaj ustawienia", "", "JSON (*.json)")
        if path:
            data = load_preset(Path(path))
            applied = apply_preset(data)
            self._format_opts = applied["format_opts"]
            self._resize = applied["resize"]
            self._transforms = applied["transforms"]
            self.quality_slider.setValue(self._format_opts.quality)
            self.png_colors_auto_cb.setChecked(self._format_opts.png_colors_auto)
            self.png_colors_slider.setValue(self._format_opts.png_max_colors)
            self.png_colors_slider.setEnabled(not self._format_opts.png_colors_auto)
            self.png_colors_label.setText(str(self._format_opts.png_max_colors))
            self.format_combo.set_selected([applied["output_format"]])

    def _save_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz ustawienia", "", "JSON (*.json)")
        if path:
            fmt = self.format_combo.first_selected()
            data = settings_to_dict(
                fmt, self._format_opts, self._resize, self._transforms,
                self._metadata, self._rename, self._batch,
            )
            save_preset(Path(path), data)

    def _about(self) -> None:
        show_about(
            self,
            "Inyfinn Photo Resizer",
            f"Inyfinn Photo Resizer {__version__}\n\n"
            "Wsadowa konwersja i kompresja zdjęć.\n"
            "WebP, AVIF, HEIC, GIF i inne formaty.",
        )
