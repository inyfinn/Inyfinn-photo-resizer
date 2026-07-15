"""Główne okno — układ FastStone, siatka wierszy/kolumn."""

from __future__ import annotations

from dataclasses import replace

import os
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QGuiApplication, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from inyfinn_resizer.app.dialogs.message_boxes import (
    ask_confirm_delete,
    ask_overwrite_inplace,
    ask_yes_no,
    show_about,
    show_critical,
    show_info,
    show_warning,
)

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.custom_size_preset import CustomSizePresetDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.dialogs.help_guide import show_help_guide
from inyfinn_resizer.app.update_manager import UpdateManager
from inyfinn_resizer.app.widgets.update_status_bar import UpdateStatusBar
from inyfinn_resizer.app.dialogs.rename_dialog import RenameDialog
from inyfinn_resizer.app.i18n_tooltips import FORMAT_EXTENSION_TIPS, UI_TOOLTIPS
from inyfinn_resizer.app.dialogs.results_dialog import ResultsDialog, WizResultsDialog
from inyfinn_resizer.core.wiz_sequence import discover_wiz_folders
from inyfinn_resizer.app.widgets.conversion_overlay import ConversionOverlay
from inyfinn_resizer.app.widgets.progress_simulator import FileProgressSimulator
from inyfinn_resizer.app.widgets.format_multi_combo import FormatMultiCombo
from inyfinn_resizer.app.widgets.input_file_tree import InputFileTree
from inyfinn_resizer.app.widgets.theme_toggle import ThemeToggle
from inyfinn_resizer.app.widgets.layout_helpers import (
    BTN_H,
    COMPACT_CONTROL_ROW_H,
    COMPACT_LABEL_W,
    SECTION_GAP,
    browse_button,
    compact_row,
    field_label,
    footer_button,
    make_step_section,
    slider_control,
    style_dropdown,
    tool_button_row,
)
from inyfinn_resizer.app.widgets.section_icons import (
    action_icon_folder_orange,
    action_icon_refresh_path,
    action_icon_restore,
)
from inyfinn_resizer.app.widgets.tool_icons import (
    icon_clear_gray,
    icon_folder_green,
    icon_image_file,
    icon_minus_red,
    icon_plus_green,
)
from inyfinn_resizer.app.user_settings import (
    load_session,
    load_theme,
    persist_all,
    restore_geometry,
    save_theme,
    snapshot_from_window,
)
from inyfinn_resizer.core.formats.registry import is_image_file, output_extension, output_format_for_input
from inyfinn_resizer.core.job import (
    CONVERTED_FOLDER_NAME,
    BatchSettings,
    DEFAULT_QUALITY,
    FormatOptions,
    JobSpec,
    MetadataPolicy,
    RenameRule,
    ResizeOptions,
    TransformOptions,
)
from inyfinn_resizer.core.pipeline import build_output_path
from inyfinn_resizer.core.presets import (
    apply_preset,
    auto_save_profile_rotating,
    load_preset,
    save_preset,
    settings_to_dict,
)
from inyfinn_resizer.core.retail_presets import (
    RETAIL_NONE,
    RETAIL_PRESETS,
    retail_preset_by_id,
    retail_snapshot_from_preset,
)
from inyfinn_resizer.core.size_presets import (
    BUILTIN_PRESETS,
    PRESET_ORIGINAL,
    PRESET_SAVE_CUSTOM,
    PRESET_TOOLTIPS,
    apply_size_preset,
    delete_custom_preset,
    is_custom_preset,
    load_custom_presets,
    preset_summary,
    save_custom_preset,
)
from inyfinn_resizer.utils.app_log import log_event
from inyfinn_resizer.core.rename.templates import preview_rename
from inyfinn_resizer.app.widgets.wheel_controls import WheelIntLineEdit, WheelSlider
from inyfinn_resizer.workers.batch_worker import BatchThread, BatchWorker
from inyfinn_resizer.workers.wiz_worker import WizThread, WizWorker


DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = DEFAULT_WINDOW_WIDTH
MIN_WINDOW_HEIGHT = 720
RIGHT_PANEL_MIN_WIDTH = 500


class MainWindow(QMainWindow):
    DEFAULT_STATUS_MESSAGE = "Przeciągnij zdjęcia na listę po lewej"
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Inyfinn Photo Resizer {__version__}")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setAcceptDrops(True)
        self._initial_size_applied = False
        self._settings_body: QWidget | None = None
        self._main_splitter: QSplitter | None = None

        self._queue: list[Path] = []
        self._file_roots: dict[Path, Path] = {}
        self._base_root: Path | None = None
        self._output_dir_manual = False
        self._format_opts = FormatOptions()
        self._resize = ResizeOptions()
        self._transforms = TransformOptions()
        self._metadata = MetadataPolicy()
        self._rename = RenameRule()
        self._batch = BatchSettings()
        self._batch_thread: BatchThread | None = None
        self._active_jobs: list[JobSpec] = []
        self._wiz_thread: WizThread | None = None
        self._folder_queue: list[Path] = []
        self._theme = load_theme()
        self._output_settings_locked = False
        self._auto_format_pending = True
        self._programmatic_settings = False
        self._settings_dirty = False
        self._size_preset_ids: list[str] = []
        self._custom_preset_payloads: dict[str, dict] = {}
        self._last_size_preset_id = PRESET_ORIGINAL
        self._output_layout = "beside"
        self._retail_preset_snapshot: dict | None = None
        self._active_retail_preset_id = RETAIL_NONE

        self._build_menu()
        self._build_ui()
        self._sync_png_colors_from_quality()
        self._update_advanced_summary()
        self._apply_saved_theme()
        load_session(self)
        self._sync_remove_bg_ui()
        if self.output_dir_edit.text().strip():
            self._output_dir_manual = True
        self._geometry_restored = restore_geometry(self)
        if not self._geometry_restored:
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        if self.width() < MIN_WINDOW_WIDTH or self.height() < MIN_WINDOW_HEIGHT:
            self.resize(
                max(self.width(), MIN_WINDOW_WIDTH),
                max(self.height(), MIN_WINDOW_HEIGHT),
            )
        self._app_footer = QLabel(f"Inyfinn Photo Resizer · v{__version__}")
        self._app_footer.setObjectName("appFooter")
        self.statusBar().addPermanentWidget(self._app_footer)

        self._update_status = UpdateStatusBar()
        self._update_status.hide()
        self.statusBar().addWidget(self._update_status, 0)
        self.statusBar().showMessage(self.DEFAULT_STATUS_MESSAGE)

        self._update_manager = UpdateManager(self, self._update_status)
        self._update_attach_done = False

    def restore_default_status_message(self) -> None:
        self.statusBar().showMessage(self.DEFAULT_STATUS_MESSAGE)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_conversion_overlay") and self.centralWidget():
            self._conversion_overlay.setGeometry(self.centralWidget().rect())
        if hasattr(self, "_update_manager"):
            self._update_manager.reposition_toast()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if hasattr(self, "_conversion_overlay") and self.centralWidget():
            self._conversion_overlay.setGeometry(self.centralWidget().rect())
        if hasattr(self, "_update_manager") and not self._update_attach_done:
            self._update_attach_done = True
            self._update_manager.attach()
        if not self._initial_size_applied:
            self._initial_size_applied = True
            QTimer.singleShot(0, self._fit_initial_window_size)

    def _fit_initial_window_size(self) -> None:
        """Domyślny rozmiar 1200×765 — nie mniejszy niż MIN."""
        screen = self.screen().availableGeometry()
        w = max(MIN_WINDOW_WIDTH, min(DEFAULT_WINDOW_WIDTH, screen.width()))
        h = max(MIN_WINDOW_HEIGHT, min(DEFAULT_WINDOW_HEIGHT, screen.height()))
        if not getattr(self, "_geometry_restored", False):
            self.resize(w, h)
        if splitter := self._main_splitter:
            right_w = max(RIGHT_PANEL_MIN_WIDTH, int(self.width() * 0.46))
            left_w = max(400, self.width() - right_w)
            splitter.setSizes([left_w, self.width() - left_w])

    @staticmethod
    def _make_panel(
        title: str,
        object_name: str = "panel",
        *,
        titled: bool = True,
        margins: tuple[int, int, int, int] = (20, 16, 20, 16),
    ) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setFrameShape(QFrame.StyledPanel)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(*margins)
        outer.setSpacing(8)
        if titled:
            lbl = QLabel(title)
            lbl.setObjectName("panelTitle")
            outer.addWidget(lbl)
        return frame, outer

    def _build_menu(self) -> None:
        menubar = QMenuBar()
        menubar.setNativeMenuBar(False)
        file_menu = menubar.addMenu("&Plik")
        file_menu.addAction("Wczytaj ustawienia…", self._load_preset)
        file_menu.addAction("Zapisz ustawienia…", self._save_preset)
        file_menu.addSeparator()
        file_menu.addAction("W&yjście", self.close)

        tools_menu = menubar.addMenu("&Narzędzia")
        tools_menu.addAction("Zmiana nazw…", self._open_rename_dialog)
        tools_menu.addSeparator()
        tools_menu.addAction("Jasny motyw", lambda: self._set_theme("light"))
        tools_menu.addAction("Ciemny motyw", lambda: self._set_theme("dark"))
        tools_menu.addSeparator()
        tools_menu.addAction("Wczytaj ustawienia…", self._load_preset)
        tools_menu.addAction("Zapisz ustawienia…", self._save_preset)

        help_menu = menubar.addMenu("Pomo&c")
        help_menu.addAction("Przewodnik użytkownika…", lambda: show_help_guide(self))
        help_menu.addSeparator()
        help_menu.addAction("Sprawdź aktualizacje…", self._check_updates_manual)
        help_menu.addAction("O programie", self._about)

        self._theme_toggle = ThemeToggle(dark=(self._theme == "dark"))
        self._theme_toggle.toggled.connect(self._on_theme_toggle)

        menu_strip = QWidget()
        menu_strip.setObjectName("menuStrip")
        menu_strip.setMinimumHeight(40)
        strip_lay = QHBoxLayout(menu_strip)
        strip_lay.setContentsMargins(0, 0, 12, 0)
        strip_lay.setSpacing(8)
        strip_lay.addWidget(menubar, stretch=1)
        strip_lay.addSpacing(24)
        preset_lbl = QLabel("Presety")
        preset_lbl.setObjectName("menuPresetLabel")
        preset_lbl.setToolTip("Preset sieci handlowej — ustawia format, wymiary i tło")
        strip_lay.addWidget(preset_lbl, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.retail_preset_combo = style_dropdown(QComboBox())
        self.retail_preset_combo.setObjectName("retailPresetCombo")
        self.retail_preset_combo.setMinimumWidth(200)
        self.retail_preset_combo.addItem("— wybierz sieć —", RETAIL_NONE)
        for preset in RETAIL_PRESETS:
            idx = self.retail_preset_combo.count()
            self.retail_preset_combo.addItem(preset.label, preset.id)
            self.retail_preset_combo.setItemData(idx, preset.tooltip, Qt.ToolTipRole)
        self.retail_preset_combo.currentIndexChanged.connect(self._on_retail_preset_changed)
        strip_lay.addWidget(self.retail_preset_combo, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.restore_retail_btn = QPushButton("Przywróć preset")
        self.restore_retail_btn.setObjectName("btnSecondary")
        self.restore_retail_btn.setIcon(action_icon_restore())
        self.restore_retail_btn.setIconSize(QSize(16, 16))
        self.restore_retail_btn.setToolTip("Przywraca ustawienia wybranej sieci po ręcznych zmianach")
        self.restore_retail_btn.setEnabled(False)
        self.restore_retail_btn.clicked.connect(self._restore_retail_preset)
        strip_lay.addWidget(self.restore_retail_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        theme_lbl = QLabel("Motyw")
        theme_lbl.setObjectName("themeToggleLabel")
        theme_lbl.setToolTip("Przełącz jasny lub ciemny motyw")
        strip_lay.addWidget(theme_lbl, 0, Qt.AlignRight | Qt.AlignVCenter)
        self._theme_toggle.setMinimumSize(72, 32)
        self._theme_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._theme_toggle.setVisible(True)
        strip_lay.addWidget(self._theme_toggle, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.setMenuWidget(menu_strip)

    def _on_theme_toggle(self, dark: bool) -> None:
        self._set_theme("dark" if dark else "light")

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(0)
        root.addWidget(self._build_convert_body(), stretch=1)
        self._conversion_overlay = ConversionOverlay(central)
        self._conversion_overlay.hide()
        self._conversion_overlay.abort_requested.connect(self._on_overlay_abort)
        self._progress_simulator = FileProgressSimulator(self)
        self._progress_simulator.tick.connect(self._on_simulated_progress)
        self._batch_cancelled = False

    def _build_convert_body(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setChildrenCollapsible(False)
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
        self.sort_combo = style_dropdown(QComboBox())
        self.sort_combo.setMinimumWidth(160)
        self.sort_combo.addItems(["Bez sortowania", "Nazwa A→Z", "Nazwa Z→A", "Rozmiar"])
        self.sort_combo.currentIndexChanged.connect(self._sort_queue)
        meta_row.addWidget(sort_lbl)
        meta_row.addWidget(self.sort_combo)
        left_layout.addLayout(meta_row)

        left_layout.addLayout(tool_button_row([
            ("Dodaj pliki", self._add_files_dialog, icon_plus_green()),
            ("Dodaj folder", self._add_folder_dialog, icon_folder_green()),
            ("Usuń", self._remove_selected, icon_minus_red()),
            ("Wyczyść", self._clear_queue, icon_clear_gray()),
        ]))

        self.input_tree = InputFileTree(self)
        self.input_tree.setObjectName("inputList")
        self.input_tree.setHeaderLabels(["Nazwa pliku", "Rozmiar"])
        self.input_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.input_tree.setRootIsDecorated(True)
        self.input_tree.setIconSize(QSize(16, 16))
        self.input_tree.setAlternatingRowColors(True)
        hdr = self.input_tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setMinimumSectionSize(72)
        self.input_tree.setColumnWidth(1, 88)
        self.input_tree.currentItemChanged.connect(self._on_selection_changed)
        self.input_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.input_tree.customContextMenuRequested.connect(self._show_file_context_menu)
        left_layout.addWidget(self.input_tree, stretch=1)

        left_layout.addWidget(self._build_preview_panel())

        splitter.addWidget(left_box)

        # —— Prawy panel: ustawienia (płasko jak FastStone) ——
        right_shell, right_layout = self._make_panel("", "panel", titled=False, margins=(16, 8, 16, 12))
        right_shell.setMinimumWidth(RIGHT_PANEL_MIN_WIDTH)
        settings_scroll = QScrollArea()
        settings_scroll.setObjectName("settingsScroll")
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        settings_body = self._build_settings_panel()
        settings_scroll.setWidget(settings_body)
        right_layout.addWidget(settings_scroll, stretch=1)

        progress_wrap = QWidget()
        progress_col = QVBoxLayout(progress_wrap)
        progress_col.setContentsMargins(0, 0, 0, 0)
        progress_col.setSpacing(4)
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("progressStatus")
        self.progress_label.setVisible(False)
        self.progress = QProgressBar()
        self.progress.setObjectName("mainProgress")
        self.progress.setVisible(False)
        self.progress.setFixedHeight(18)
        self.progress.setTextVisible(False)
        self.progress.setFormat("")
        progress_col.addWidget(self.progress_label)
        progress_col.addWidget(self.progress)
        right_layout.addWidget(progress_wrap)

        action_bar = QFrame()
        action_bar.setObjectName("actionFooterBar")
        action_row = QHBoxLayout(action_bar)
        action_row.setContentsMargins(10, 8, 10, 8)
        action_row.setSpacing(10)
        action_row.addStretch(1)
        self.convert_btn = footer_button("Konwertuj", primary=True, slot=self._start_convert)
        self.convert_btn.setObjectName("footerConvert")
        self.convert_btn.setFixedSize(132, 36)
        close_btn = footer_button("Zamknij", primary=False, slot=self.close)
        close_btn.setObjectName("footerClose")
        close_btn.setFixedSize(112, 36)
        action_row.addWidget(self.convert_btn)
        action_row.addWidget(close_btn)
        right_layout.addWidget(action_bar)

        splitter.addWidget(right_shell)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([648, 552])
        return splitter

    def _build_preview_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("previewPanel")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(6)

        self.preview_cb = QCheckBox("Podgląd zaznaczonego pliku")
        self.preview_cb.setObjectName("previewToggle")
        self.preview_cb.setChecked(True)
        self.preview_cb.setToolTip(UI_TOOLTIPS["preview"])
        self.preview_cb.toggled.connect(self._on_preview_toggled)
        outer.addWidget(self.preview_cb)

        body = QWidget()
        body.setObjectName("previewBody")
        self._preview_body = body
        body_row = QHBoxLayout(body)
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(10)

        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewBox")
        self.preview_label.setFixedSize(112, 112)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setScaledContents(False)
        body_row.addWidget(self.preview_label, 0, Qt.AlignmentFlag.AlignTop)

        meta_col = QVBoxLayout()
        meta_col.setContentsMargins(0, 0, 0, 0)
        meta_col.setSpacing(4)
        meta_hint = QLabel("Nazwa, rozmiar i folder źródłowy")
        meta_hint.setObjectName("previewHint")
        meta_hint.setWordWrap(True)
        self.size_info = QLabel("Zaznacz plik na liście")
        self.size_info.setObjectName("previewMeta")
        self.size_info.setWordWrap(True)
        self.size_info.setAlignment(Qt.AlignmentFlag.AlignTop)
        meta_col.addWidget(meta_hint)
        meta_col.addWidget(self.size_info, stretch=1)
        body_row.addLayout(meta_col, stretch=1)

        outer.addWidget(body)
        return panel

    def _on_preview_toggled(self, checked: bool) -> None:
        self._mark_dirty()
        self._preview_body.setVisible(checked)
        if checked:
            self._on_selection_changed(self.input_tree.currentItem(), None)
        else:
            self.preview_label.clear()
            self.size_info.setText("Podgląd wyłączony")

    def _build_settings_panel(self) -> QWidget:
        body = QWidget()
        self._settings_body = body
        body.setObjectName("settingsBody")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        root = QVBoxLayout(body)
        root.setSpacing(SECTION_GAP)
        root.setContentsMargins(0, 0, 8, 12)

        flow_hint = QLabel(
            "Krok po kroku: format i jakość, wymiary, na końcu zapis plików."
        )
        flow_hint.setObjectName("workflowHint")
        flow_hint.setWordWrap(True)

        section1_box, section1 = make_step_section(
            "Format i jakość",
            "Rozszerzenie, tło, sekwencja wizek i suwaki jakości",
            step_key="format",
        )
        section2_box, section2 = make_step_section(
            "Wymiary",
            "Skala, min. krawędź i preset formatu",
            step_key="dimensions",
        )
        section3_box, section3 = make_step_section(
            "Zapis plików",
            "Folder wyjściowy i opcje wsadowe",
            step_key="save",
        )

        # Rozszerzenie + ustawienia formatu (jeden wiersz jak Jakość / Format)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        fmt_row.setContentsMargins(0, 0, 0, 0)
        self.format_combo = FormatMultiCombo()
        style_dropdown(self.format_combo)
        self.format_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.format_combo.selectionChanged.connect(self._on_formats_changed)
        fmt_row.addWidget(self.format_combo, stretch=1)
        self.settings_btn = QPushButton("Ustawienia…")
        self.settings_btn.setObjectName("btnSecondary")
        self.settings_btn.setMinimumHeight(BTN_H)
        self.settings_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.settings_btn.setToolTip(
            "Szczegóły rozszerzenia: PNG-8/24, tło JPG, kompresja GIF, kadrowanie i opcje zaawansowane."
        )
        self.settings_btn.clicked.connect(self._open_format_settings)
        fmt_row.addWidget(self.settings_btn, 0, Qt.AlignRight)
        fmt_controls = QWidget()
        fmt_controls.setLayout(fmt_row)
        self.fmt_wrap = fmt_controls
        section1.addWidget(compact_row(
            "Rozszerzenie",
            fmt_controls,
            tooltip=UI_TOOLTIPS["extension"],
            height=COMPACT_CONTROL_ROW_H,
        ))
        section1.addSpacing(2)

        top_opts_grid = QGridLayout()
        top_opts_grid.setSpacing(4)
        top_opts_grid.setContentsMargins(0, 0, 0, 0)

        self.segregate_cb = QCheckBox("Segreguj do podfolderów")
        self.segregate_cb.setChecked(False)
        self.segregate_cb.setToolTip(UI_TOOLTIPS["segregate"])
        top_opts_grid.addWidget(self.segregate_cb, 0, 0)

        bg_group = QFrame()
        bg_group.setObjectName("bgRemoveGroup")
        bg_group_layout = QHBoxLayout(bg_group)
        bg_group_layout.setContentsMargins(8, 4, 8, 4)
        bg_group_layout.setSpacing(4)
        self.remove_bg_cb = QCheckBox("Usuń tło")
        self.remove_bg_cb.setToolTip(UI_TOOLTIPS["remove_background"])
        self.remove_bg_cb.toggled.connect(self._on_remove_bg_toggled)
        bg_group_layout.addWidget(self.remove_bg_cb)
        self.bg_model_combo = QComboBox()
        self.bg_model_combo.setObjectName("bgModelCombo")
        self.bg_model_combo.setMinimumWidth(120)
        self.bg_model_combo.addItem("Najlepsza jakość", "birefnet-general")
        self.bg_model_combo.setItemData(0, UI_TOOLTIPS["bg_model_general"], Qt.ItemDataRole.ToolTipRole)
        self.bg_model_combo.addItem("Szybko", "birefnet-general-lite")
        self.bg_model_combo.setItemData(1, UI_TOOLTIPS["bg_model_lite"], Qt.ItemDataRole.ToolTipRole)
        self.bg_model_combo.setToolTip(UI_TOOLTIPS["bg_model_combo"])
        self.bg_model_combo.setCurrentIndex(0)
        self.bg_model_combo.currentIndexChanged.connect(self._on_bg_model_changed)
        style_dropdown(self.bg_model_combo)
        bg_group_layout.addWidget(self.bg_model_combo, stretch=1)
        top_opts_grid.addWidget(bg_group, 0, 1)

        self.wiz_sequence_cb = QCheckBox("Sekwencja wizek (XL/L/S/SKLEP)")
        self.wiz_sequence_cb.setToolTip(UI_TOOLTIPS["wiz"])
        self.wiz_sequence_cb.toggled.connect(self._on_wiz_mode_changed)
        top_opts_grid.addWidget(self.wiz_sequence_cb, 1, 0, 1, 2)
        top_opts_grid.setColumnStretch(0, 1)
        top_opts_grid.setColumnStretch(1, 1)
        section1.addLayout(top_opts_grid)
        section1.addSpacing(2)

        self.quality_slider = WheelSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        self.quality_label = QLabel(str(DEFAULT_QUALITY))
        section1.addWidget(compact_row(
            "Jakość",
            slider_control(
                self.quality_slider,
                self.quality_label,
                tooltip=UI_TOOLTIPS["quality"],
            ),
            tooltip=UI_TOOLTIPS["quality"],
            tight=True,
        ))

        self.png_colors_slider = WheelSlider(Qt.Orientation.Horizontal)
        self.png_colors_slider.setRange(24, 256)
        self.png_colors_slider.setValue(256)
        self.png_colors_slider.valueChanged.connect(self._on_png_colors_changed)
        self.png_colors_label = QLabel("256")
        colors_slider_row = slider_control(
            self.png_colors_slider,
            self.png_colors_label,
            tooltip=UI_TOOLTIPS["color_count"],
        )
        colors_extras = QHBoxLayout()
        colors_extras.setContentsMargins(0, 0, 0, 0)
        colors_extras.setSpacing(4)
        colors_extras.addWidget(colors_slider_row, stretch=1)
        self.png_colors_auto_cb = QCheckBox("Z jakości")
        self.png_colors_auto_cb.setChecked(True)
        self.png_colors_auto_cb.setToolTip(UI_TOOLTIPS["color_count"])
        self.png_colors_auto_cb.toggled.connect(self._on_png_colors_auto)
        self.png_colors_slider.setEnabled(False)
        colors_extras.addWidget(self.png_colors_auto_cb)
        colors_wrap = QWidget()
        colors_wrap.setLayout(colors_extras)
        section1.addWidget(compact_row(
            "Liczba kolorów",
            colors_wrap,
            tooltip=UI_TOOLTIPS["color_count"],
            tight=True,
        ))
        section1.addStretch(1)

        self.scale_slider = WheelSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100)
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        self.scale_label = QLabel("100%")
        section2.addWidget(compact_row(
            "Skala",
            slider_control(
                self.scale_slider,
                self.scale_label,
                tooltip=UI_TOOLTIPS["scale"],
            ),
            tooltip=UI_TOOLTIPS["scale"],
            tight=True,
        ))

        min_row_widget = QWidget()
        min_row_widget.setMinimumHeight(COMPACT_CONTROL_ROW_H)
        min_row = QHBoxLayout(min_row_widget)
        min_row.setContentsMargins(COMPACT_LABEL_W + 8, 0, 0, 0)
        min_row.setSpacing(6)
        self.min_longest_cb = QCheckBox("Min. najdłuższa krawędź")
        self.min_longest_cb.setChecked(True)
        self.min_longest_cb.setToolTip(UI_TOOLTIPS["min_longest"])
        self.min_longest_cb.toggled.connect(self._on_min_longest_toggled)
        min_row.addWidget(self.min_longest_cb)
        self.min_longest_edit = WheelIntLineEdit("1080", min_val=1, max_val=16384, step=10)
        self.min_longest_edit.setObjectName("minLongestEdit")
        self.min_longest_edit.setValidator(QIntValidator(1, 16384, self))
        self.min_longest_edit.setPlaceholderText("1080 px")
        self.min_longest_edit.setToolTip(UI_TOOLTIPS["min_longest_px"])
        self.min_longest_edit.setMaximumWidth(72)
        self.min_longest_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.min_longest_edit.textChanged.connect(self._on_min_longest_text_changed)
        min_row.addWidget(self.min_longest_edit)
        px_lbl = QLabel("px")
        px_lbl.setObjectName("hintLabel")
        min_row.addWidget(px_lbl)
        min_row.addStretch(1)
        section2.addWidget(min_row_widget)
        section2.addSpacing(2)

        self.size_combo = style_dropdown(QComboBox())
        self.size_combo.setToolTip(UI_TOOLTIPS["dimension_format"])
        self.size_combo.currentIndexChanged.connect(self._on_size_preset_changed)
        self.delete_preset_btn = QPushButton()
        self.delete_preset_btn.setObjectName("toolBtn")
        self.delete_preset_btn.setIcon(icon_minus_red())
        self.delete_preset_btn.setIconSize(self.delete_preset_btn.iconSize())
        self.delete_preset_btn.setFixedSize(BTN_H, BTN_H)
        self.delete_preset_btn.setToolTip("Usuń własny preset wymiarów")
        self.delete_preset_btn.clicked.connect(self._delete_custom_size_preset)
        self.delete_preset_btn.setEnabled(False)
        format_row = QWidget()
        format_row_layout = QHBoxLayout(format_row)
        format_row_layout.setContentsMargins(0, 0, 0, 0)
        format_row_layout.setSpacing(6)
        format_row_layout.addWidget(self.size_combo, stretch=1)
        format_row_layout.addWidget(self.delete_preset_btn)
        section2.addWidget(compact_row("Format", format_row, tooltip=UI_TOOLTIPS["dimension_format"], height=COMPACT_CONTROL_ROW_H))
        self._reload_size_combo(select_id=PRESET_ORIGINAL)
        section2.addStretch(1)

        out_section = QWidget()
        out_section_layout = QVBoxLayout(out_section)
        out_section_layout.setContentsMargins(0, 0, 0, 0)
        out_section_layout.setSpacing(2)
        wyjscie_lbl = field_label("Wyjście", UI_TOOLTIPS["output_dir"])
        out_section_layout.addWidget(wyjscie_lbl)

        self.output_enabled_cb = QCheckBox("Zapisz do folderu wyjściowego")
        self.output_enabled_cb.setChecked(False)
        self.output_enabled_cb.setToolTip(UI_TOOLTIPS["output_enabled"])
        self.output_enabled_cb.toggled.connect(self._on_output_enabled_toggled)
        out_section_layout.addWidget(self.output_enabled_cb)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setObjectName("outputDirEdit")
        self.output_dir_edit.setPlaceholderText(
            "Dodaj zdjęcia, potem kliknij „Aktualizuj ścieżkę”"
        )
        self.output_dir_edit.setToolTip(UI_TOOLTIPS["output_dir"])
        self.output_dir_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.output_dir_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.output_dir_edit.setMinimumHeight(BTN_H)
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setEnabled(False)
        out_section_layout.addWidget(self.output_dir_edit)

        path_btn_row = QHBoxLayout()
        path_btn_row.setContentsMargins(0, 0, 0, 0)
        path_btn_row.setSpacing(8)
        self.update_output_btn = QPushButton("Aktualizuj ścieżkę")
        self.update_output_btn.setObjectName("btnUpdatePath")
        self.update_output_btn.setIcon(action_icon_refresh_path())
        self.update_output_btn.setIconSize(QSize(16, 16))
        self.update_output_btn.setToolTip(UI_TOOLTIPS["output_update_path"])
        self.update_output_btn.setMinimumHeight(BTN_H)
        self.update_output_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.update_output_btn.clicked.connect(self._update_output_path)
        path_btn_row.addWidget(self.update_output_btn, stretch=1)
        browse_out = browse_button(
            "PRZEGLĄDAJ",
            tooltip="Wybierz inny folder na gotowe zdjęcia",
            slot=self._browse_output,
        )
        browse_out.setIcon(action_icon_folder_orange())
        browse_out.setIconSize(QSize(16, 16))
        browse_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        path_btn_row.addWidget(browse_out, stretch=1)
        out_section_layout.addLayout(path_btn_row)

        self._out_row = out_section
        self._out_control = out_section
        section3.addWidget(out_section)
        self.output_dir_edit.textChanged.connect(self._sync_output_tooltip)
        self._sync_output_tooltip()

        # Opcje wsadowe — siatka 2×2 (bez ucinania etykiet)
        cb_grid = QGridLayout()
        cb_grid.setSpacing(6)
        cb_grid.setContentsMargins(0, 4, 0, 0)
        for i, (text, attr, tip_key, checked) in enumerate([
            ("Zachowaj strukturę folderów", "preserve_cb", "preserve_structure", True),
            ("Zachowaj datę i godzinę", "keep_dates_cb", "keep_dates", True),
            ("Pytaj przed nadpisaniem", "overwrite_cb", "overwrite", True),
            ("Wiele plików naraz", "parallel_cb", "parallel", True),
        ]):
            cb = QCheckBox(text)
            cb.setChecked(checked)
            cb.setToolTip(UI_TOOLTIPS[tip_key])
            cb.toggled.connect(lambda _v: self._mark_dirty())
            setattr(self, attr, cb)
            cb_grid.addWidget(cb, i // 2, i % 2)
        section3.addLayout(cb_grid)

        root.addWidget(flow_hint, 0)
        root.addWidget(section1_box, 0)
        root.addWidget(section2_box, 0)
        root.addWidget(section3_box, 0)
        self._step_section_boxes = [section1_box, section2_box, section3_box]

        self.segregate_cb.toggled.connect(lambda _v: self._mark_dirty())
        self.wiz_sequence_cb.toggled.connect(lambda _v: self._mark_dirty())
        self.output_dir_edit.textChanged.connect(lambda _v: self._mark_dirty())

        return body

    def _open_rename_dialog(self) -> None:
        dlg = RenameDialog(self._rename, self._queue, self)
        if dlg.exec():
            self._rename = dlg.get_rule()

    def _mark_dirty(self) -> None:
        if not self._programmatic_settings:
            self._settings_dirty = True

    def _on_retail_preset_changed(self, _index: int) -> None:
        preset_id = self.retail_preset_combo.currentData()
        if not preset_id or preset_id == RETAIL_NONE:
            self._active_retail_preset_id = RETAIL_NONE
            self._retail_preset_snapshot = None
            self.restore_retail_btn.setEnabled(False)
            return
        preset = retail_preset_by_id(str(preset_id))
        if preset is None:
            return
        self._active_retail_preset_id = preset.id
        self._retail_preset_snapshot = retail_snapshot_from_preset(preset)
        self._apply_settings_snapshot(self._retail_preset_snapshot)
        self.restore_retail_btn.setEnabled(True)
        log_event("Preset sieci", preset.label)
        self.statusBar().showMessage(f"Preset: {preset.label}", 4000)

    def _restore_retail_preset(self) -> None:
        if not self._retail_preset_snapshot:
            return
        self._apply_settings_snapshot(self._retail_preset_snapshot)
        preset = retail_preset_by_id(self._active_retail_preset_id)
        if preset:
            self.statusBar().showMessage(f"Przywrócono preset: {preset.label}", 4000)

    def _apply_settings_snapshot(self, snapshot: dict) -> None:
        self._lock_output_settings()
        self._format_opts = snapshot["format_opts"]
        self._resize = snapshot["resize"]
        self._transforms = snapshot["transforms"]
        self._programmatic_settings = True
        self.format_combo.blockSignals(True)
        self.size_combo.blockSignals(True)
        try:
            fmt_keys = snapshot.get("formats") or [snapshot["output_format"]]
            self.format_combo.apply_format_state(
                fmt_keys,
                alpha_only=bool(snapshot["remove_background"]),
            )
            self.quality_slider.setValue(int(snapshot["quality"]))
            self.quality_label.setText(str(snapshot["quality"]))
            self.png_colors_auto_cb.setChecked(bool(snapshot["png_colors_auto"]))
            self.png_colors_slider.setValue(int(snapshot["png_max_colors"]))
            self.png_colors_slider.setEnabled(not snapshot["png_colors_auto"])
            self.png_colors_label.setText(str(snapshot["png_max_colors"]))
            self.scale_slider.setValue(int(round(float(snapshot["scale_percent"]))))
            self.scale_label.setText(f"{int(round(float(snapshot['scale_percent'])))}%")
            self.min_longest_cb.setChecked(bool(snapshot["min_longest_enabled"]))
            self.min_longest_edit.setText(str(snapshot["min_longest_px"]))
            self.remove_bg_cb.setChecked(bool(snapshot["remove_background"]))
            model = snapshot.get("bg_model") or "birefnet-general"
            idx = self.bg_model_combo.findData(model)
            if idx >= 0:
                self.bg_model_combo.setCurrentIndex(idx)
            self.segregate_cb.setChecked(bool(snapshot.get("segregate", False)))
            self.wiz_sequence_cb.setChecked(bool(snapshot.get("wiz_sequence", False)))
            self.output_enabled_cb.setChecked(bool(snapshot.get("output_enabled", False)))
            self.preserve_cb.setChecked(bool(snapshot.get("preserve_structure", True)))
            self.keep_dates_cb.setChecked(bool(snapshot.get("keep_dates", True)))
            self.overwrite_cb.setChecked(bool(snapshot.get("overwrite_prompt", True)))
            self.parallel_cb.setChecked(bool(snapshot.get("parallel", True)))
            size_id = snapshot.get("size_preset", PRESET_ORIGINAL)
            self._last_size_preset_id = size_id
            if size_id in self._size_preset_ids:
                self.size_combo.setCurrentIndex(self._size_preset_ids.index(size_id))
            else:
                self._reload_size_combo(select_id=size_id)
            self._format_opts.jpeg_matte_mode = snapshot.get(
                "jpeg_matte_mode", self._format_opts.jpeg_matte_mode
            )
        finally:
            self.format_combo.blockSignals(False)
            self.size_combo.blockSignals(False)
            self._programmatic_settings = False
        self._on_wiz_mode_changed(self.wiz_sequence_cb.isChecked())
        self._on_output_enabled_toggled(self.output_enabled_cb.isChecked())
        self._update_delete_preset_btn()
        self._settings_dirty = False

    def _apply_saved_theme(self) -> None:
        from PySide6.QtWidgets import QApplication

        from inyfinn_resizer.app.themes import apply_theme

        apply_theme(QApplication.instance(), self._theme)
        self._refresh_step_icons()

    def _set_theme(self, theme: str) -> None:
        from PySide6.QtWidgets import QApplication

        from inyfinn_resizer.app.themes import apply_theme

        self._theme = theme
        apply_theme(QApplication.instance(), theme)
        save_theme(theme)
        self._refresh_step_icons()
        if hasattr(self, "_theme_toggle"):
            self._theme_toggle.blockSignals(True)
            self._theme_toggle.set_dark(theme == "dark")
            self._theme_toggle.blockSignals(False)
        self._mark_dirty()

    def _refresh_step_icons(self) -> None:
        """Przemaluj kolorowe ikony sekcji po zmianie motywu (jasny/ciemny)."""
        from inyfinn_resizer.app.widgets.section_icons import step_pixmap

        for box in getattr(self, "_step_section_boxes", []):
            icon = getattr(box, "_step_icon_label", None)
            key = getattr(box, "_step_key", None)
            if icon is not None and key:
                icon.setPixmap(step_pixmap(key))

    def _reload_size_combo(self, *, select_id: str | None = None) -> None:
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        self._size_preset_ids = []
        self._custom_preset_payloads = {}
        for label, pid in BUILTIN_PRESETS:
            self.size_combo.addItem(label)
            idx = self.size_combo.count() - 1
            tip = PRESET_TOOLTIPS.get(pid, "")
            if tip:
                self.size_combo.setItemData(idx, tip, Qt.ItemDataRole.ToolTipRole)
            self._size_preset_ids.append(pid)
        for name, pid, payload in load_custom_presets():
            self.size_combo.addItem(f"★ {name}")
            self._size_preset_ids.append(pid)
            self._custom_preset_payloads[pid] = payload
        self.size_combo.addItem("＋ Zapisz własny preset…")
        self._size_preset_ids.append(PRESET_SAVE_CUSTOM)
        target = select_id or self._last_size_preset_id or PRESET_ORIGINAL
        if target in self._size_preset_ids:
            self.size_combo.setCurrentIndex(self._size_preset_ids.index(target))
        self.size_combo.blockSignals(False)
        self._update_delete_preset_btn()

    def _update_delete_preset_btn(self) -> None:
        pid = self._current_size_preset_id()
        self.delete_preset_btn.setEnabled(is_custom_preset(pid))

    def _delete_custom_size_preset(self) -> None:
        pid = self._current_size_preset_id()
        if not is_custom_preset(pid):
            return
        payload = self._custom_preset_payloads.get(pid, {})
        name = str(payload.get("name", pid))
        if not ask_confirm_delete(
            self,
            "Usuń preset",
            f"Czy na pewno usunąć własny preset „{name}”?",
        ):
            return
        if delete_custom_preset(pid):
            log_event("Usunięto preset wymiarów", name)
            self._last_size_preset_id = PRESET_ORIGINAL
            self._reload_size_combo(select_id=PRESET_ORIGINAL)
            self._apply_resize_preset()
            self._mark_dirty()

    def _current_size_preset_id(self) -> str:
        idx = self.size_combo.currentIndex()
        if 0 <= idx < len(self._size_preset_ids):
            return self._size_preset_ids[idx]
        return PRESET_ORIGINAL

    def _sync_output_tooltip(self) -> None:
        text = self.output_dir_edit.text().strip()
        tip = text if text else UI_TOOLTIPS["output_dir"]
        self.output_dir_edit.setToolTip(tip)
        self._out_control.setToolTip(tip)
        self._out_row.setToolTip(tip)

    def _save_custom_size_preset(self) -> None:
        dlg = CustomSizePresetDialog(self._resize, self._transforms, self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            self._reload_size_combo(select_id=self._last_size_preset_id)
            return
        name = dlg.preset_name()
        if not name:
            self._reload_size_combo(select_id=self._last_size_preset_id)
            return
        resize = dlg.get_resize()
        transforms = dlg.get_transforms()
        self._resize = resize
        self._transforms = transforms
        pid = save_custom_preset(name, resize, transforms)
        self._last_size_preset_id = pid
        self._reload_size_combo(select_id=pid)
        self._mark_dirty()
        log_event("Zapis presetu wymiarów", f"{name} — {preset_summary(resize)}")

    def _on_wiz_mode_changed(self, enabled: bool) -> None:
        self.format_combo.setEnabled(not enabled)
        self.settings_btn.setEnabled(not enabled)
        self.fmt_wrap.setEnabled(not enabled)
        self.remove_bg_cb.setEnabled(not enabled)
        self.bg_model_combo.setEnabled(not enabled)
        if enabled:
            self.segregate_cb.setChecked(False)
            self.segregate_cb.setEnabled(False)
            self.remove_bg_cb.setChecked(False)
            self.output_enabled_cb.setEnabled(False)
            self.output_dir_edit.setEnabled(False)
            if hasattr(self, "update_output_btn"):
                self.update_output_btn.setEnabled(False)
            self.convert_btn.setText("Konwertuj wizek")
        else:
            self.segregate_cb.setEnabled(True)
            self.output_enabled_cb.setEnabled(True)
            self._on_output_enabled_toggled(self.output_enabled_cb.isChecked())
            self.convert_btn.setText("Konwertuj")

    def _on_remove_bg_toggled(self, enabled: bool) -> None:
        self._transforms.remove_background = enabled
        self._programmatic_settings = True
        try:
            if enabled:
                current = self.format_combo.selected_formats()
                if not any(f in ("png", "webp", "avif") for f in current):
                    current = ["png"]
                self.format_combo.apply_format_state(current, alpha_only=True)
            else:
                current = self.format_combo.selected_formats()
                if not current or all(f in ("png", "webp", "avif") for f in current):
                    current = ["jpeg"]
                self.format_combo.apply_format_state(current, alpha_only=False)
        finally:
            self._programmatic_settings = False
        self._mark_dirty()

    def _on_bg_model_changed(self, _index: int) -> None:
        data = self.bg_model_combo.currentData()
        if data:
            self._transforms.bg_model = str(data)
            tip = self.bg_model_combo.currentData(Qt.ToolTipRole)
            if tip:
                self.bg_model_combo.setToolTip(str(tip))
        self._mark_dirty()

    def _sync_remove_bg_ui(self) -> None:
        enabled = self._transforms.remove_background
        self.remove_bg_cb.setChecked(enabled)
        model = self._transforms.bg_model or "birefnet-general"
        idx = self.bg_model_combo.findData(model)
        if idx >= 0:
            self.bg_model_combo.setCurrentIndex(idx)
        self.format_combo.apply_format_state(
            self.format_combo.selected_formats() or ["webp"],
            alpha_only=enabled,
        )

    def _on_output_enabled_toggled(self, enabled: bool) -> None:
        if not self._programmatic_settings:
            self._mark_dirty()
        can_edit = enabled and not self.wiz_sequence_cb.isChecked()
        self.output_dir_edit.setEnabled(can_edit)
        self.output_dir_edit.setReadOnly(not can_edit)
        if hasattr(self, "update_output_btn"):
            self.update_output_btn.setEnabled(bool(self._queue or self._folder_queue))

    def _output_path_active(self) -> bool:
        return self.output_enabled_cb.isChecked() and not self.wiz_sequence_cb.isChecked()

    def _lock_output_settings(self) -> None:
        self._output_settings_locked = True
        self._auto_format_pending = False

    def _set_output_format_programmatically(self, fmt: str) -> None:
        self._programmatic_settings = True
        try:
            self.format_combo.set_selected([fmt])
        finally:
            self._programmatic_settings = False

    def _maybe_auto_format_from_first_file(self, path: Path) -> None:
        if self._output_settings_locked or not self._auto_format_pending:
            return
        if len(self._queue) != 1:
            return
        fmt = output_format_for_input(path)
        self._set_output_format_programmatically(fmt)
        self._auto_format_pending = False

    def _on_formats_changed(self) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
            self._mark_dirty()

    def _selected_formats(self) -> list[str]:
        fmts = self.format_combo.selected_formats()
        if not fmts:
            fmts = ["webp"]
        if self._transforms.remove_background:
            from inyfinn_resizer.app.i18n_tooltips import ALPHA_OUTPUT_FORMATS

            fmts = [f for f in fmts if f in ALPHA_OUTPUT_FORMATS] or ["png"]
        return fmts

    def _validate_bg_removal_ready(self) -> bool:
        if not self._transforms.remove_background:
            return True
        from inyfinn_resizer.core.transforms.background_removal import (
            missing_model_message,
            model_is_ready,
        )

        model = self._transforms.bg_model or "birefnet-general"
        if model_is_ready(model):
            return True
        show_warning(self, "Usuń tło", missing_model_message(model))
        return False

    def _on_quality_changed(self, v: int) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        self.quality_label.setText(str(v))
        self._format_opts.quality = v
        if self.png_colors_auto_cb.isChecked():
            self._sync_png_colors_from_quality()
        if self._format_opts.gif_from_quality:
            from inyfinn_resizer.core.quality_map import apply_quality_to_format_opts

            apply_quality_to_format_opts(self._format_opts)

    def _on_scale_changed(self, v: int) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        self.scale_label.setText(f"{v}%")
        self._resize.scale_percent = float(v)

    def _on_min_longest_toggled(self, enabled: bool) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        self._resize.min_longest_enabled = enabled

    def _on_min_longest_px_changed(self, v: int) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        self._resize.min_longest_px = v

    def _min_longest_px_value(self) -> int:
        try:
            return max(1, min(16384, int(self.min_longest_edit.text() or "1080")))
        except ValueError:
            return 1080

    def _on_min_longest_text_changed(self, text: str) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        if text.strip().isdigit():
            self._resize.min_longest_px = int(text)

    def _resize_for_job(self) -> ResizeOptions:
        return replace(
            self._resize,
            scale_percent=float(self.scale_slider.value()),
            min_longest_enabled=self.min_longest_cb.isChecked(),
            min_longest_px=self._min_longest_px_value(),
        )

    def _sync_png_colors_from_quality(self) -> None:
        from inyfinn_resizer.core.compressors.png import png_max_colors_for_quality

        colors = png_max_colors_for_quality(self.quality_slider.value())
        self.png_colors_slider.blockSignals(True)
        self.png_colors_slider.setValue(colors)
        self.png_colors_slider.blockSignals(False)
        self.png_colors_label.setText(str(colors))
        self._format_opts.png_max_colors = colors

    def _on_png_colors_changed(self, v: int) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
        self.png_colors_label.setText(str(v))
        self._format_opts.png_max_colors = v

    def _on_png_colors_auto(self, enabled: bool) -> None:
        if not self._programmatic_settings:
            self._lock_output_settings()
        self._mark_dirty()
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

    def _anchor_path_for_output(self) -> Path | None:
        selected = self._selected_file_paths()
        if selected:
            return selected[0]
        if self._queue:
            return self._queue[0]
        if self._folder_queue:
            return self._folder_queue[0]
        return None

    def _suggested_output_dir(self, anchor: Path | None = None) -> Path | None:
        if anchor is None:
            anchor = self._anchor_path_for_output()
        if anchor is None:
            return None
        if anchor.is_file():
            return anchor.parent / CONVERTED_FOLDER_NAME
        return anchor / CONVERTED_FOLDER_NAME

    def _update_output_path(self) -> None:
        suggested = self._suggested_output_dir()
        if suggested is None:
            self.statusBar().showMessage("Najpierw dodaj zdjęcia na listę po lewej", 4000)
            return
        self._output_dir_manual = False
        self._programmatic_settings = True
        try:
            self.output_enabled_cb.setChecked(True)
            self.output_dir_edit.setText(str(suggested))
        finally:
            self._programmatic_settings = False
        self._sync_output_tooltip()
        log_event("Folder wyjściowy (sugestia)", str(suggested))
        self.statusBar().showMessage(f"Folder wyjściowy: {suggested}", 5000)

    def _structure_root_for(self, path: Path) -> Path:
        return self._file_roots.get(path, path.parent)

    def _make_file_item(self, path: Path, *, label: str | None = None) -> QTreeWidgetItem:
        item = QTreeWidgetItem([label or path.name, self._format_size(path)])
        item.setIcon(0, icon_image_file())
        item.setData(0, Qt.UserRole, str(path))
        item.setData(0, Qt.UserRole + 1, "file")
        item.setToolTip(0, str(path))
        return item

    def _make_folder_item(self, folder: Path) -> QTreeWidgetItem:
        item = QTreeWidgetItem([folder.name, "folder"])
        item.setIcon(0, icon_folder_green())
        item.setData(0, Qt.UserRole, str(folder))
        item.setData(0, Qt.UserRole + 1, "folder")
        item.setToolTip(0, str(folder))
        return item

    def _add_path_to_queue(self, path: Path, *, parent_item: QTreeWidgetItem | None = None) -> None:
        path = path.resolve()
        if path in self._queue:
            return
        self._queue.append(path)
        self._file_roots[path] = path.parent
        item = self._make_file_item(path)
        if parent_item is not None:
            parent_item.addChild(item)
        else:
            self.input_tree.addTopLevelItem(item)
        if self._base_root is None:
            self._base_root = path.parent
        self._maybe_auto_format_from_first_file(path)
        self._update_queue_label()

    def _import_batch_folder(self, folder: Path) -> None:
        folder = folder.resolve()
        if folder in self._folder_queue:
            return
        self._folder_queue.append(folder)
        folder_item = self._make_folder_item(folder)
        for f in sorted(folder.rglob("*")):
            if not f.is_file() or not is_image_file(f):
                continue
            f = f.resolve()
            if f in self._queue:
                continue
            self._queue.append(f)
            self._file_roots[f] = folder
            rel = f.relative_to(folder)
            child = self._make_file_item(f, label=str(rel))
            folder_item.addChild(child)
        self.input_tree.addTopLevelItem(folder_item)
        folder_item.setExpanded(True)
        if self._base_root is None:
            self._base_root = folder
        if self._queue:
            self._maybe_auto_format_from_first_file(self._queue[0])
        self._update_queue_label()

    def _add_folder_to_queue(self, folder: Path) -> None:
        folder = folder.resolve()
        if folder in self._folder_queue:
            return
        self._folder_queue.append(folder)
        item = self._make_folder_item(folder)
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
        self._import_batch_folder(root)

    def _handle_dropped_urls(self, urls) -> None:
        for url in urls:
            p = Path(url.toLocalFile())
            if not p.exists():
                continue
            if p.is_dir():
                if self.wiz_sequence_cb.isChecked():
                    self._add_folder_to_queue(p)
                else:
                    self._import_batch_folder(p)
            elif p.is_file() and is_image_file(p):
                self._add_path_to_queue(p)

    def _selected_file_paths(self) -> list[Path]:
        paths: list[Path] = []
        for item in self.input_tree.selectedItems():
            if self._item_kind(item) != "file":
                continue
            data = item.data(0, Qt.UserRole)
            if data:
                paths.append(Path(data))
        return paths

    def _show_file_context_menu(self, pos) -> None:
        item = self.input_tree.itemAt(pos)
        if item is None:
            return
        if item not in self.input_tree.selectedItems():
            self.input_tree.setCurrentItem(item)

        selected = self.input_tree.selectedItems()
        files = self._selected_file_paths()
        folders = [item for item in selected if self._item_kind(item) == "folder"]

        menu = QMenu(self)
        if files:
            label = "Konwertuj zaznaczone"
            if len(files) == 1:
                label = "Konwertuj ten plik"
            menu.addAction(label, self._start_convert_selected)
            menu.addSeparator()
        if files or folders:
            menu.addAction("Usuń zaznaczone", self._remove_selected)
            menu.addSeparator()
        if len(files) == 1:
            menu.addAction("Otwórz lokalizację pliku", self._open_selected_in_explorer)
            menu.addAction("Kopiuj ścieżkę", self._copy_selected_path)
        elif len(folders) == 1 and not files:
            menu.addAction("Otwórz folder", self._open_selected_in_explorer)
            menu.addAction("Kopiuj ścieżkę", self._copy_selected_path)
        elif files:
            menu.addAction("Kopiuj ścieżki", self._copy_selected_path)
        if self.input_tree.topLevelItemCount() > 1:
            menu.addSeparator()
            menu.addAction("Zaznacz wszystkie", self.input_tree.selectAll)

        if not menu.actions():
            return
        menu.exec(self.input_tree.viewport().mapToGlobal(pos))

    def _open_selected_in_explorer(self) -> None:
        items = self.input_tree.selectedItems()
        if not items:
            return
        path = Path(items[0].data(0, Qt.UserRole))
        if not path.exists():
            show_warning(self, "Eksplorator", "Ścieżka nie istnieje.")
            return
        target = path if path.is_dir() else path.parent
        os.startfile(str(target))

    def _copy_selected_path(self) -> None:
        items = self.input_tree.selectedItems()
        if not items:
            return
        lines = []
        for item in items:
            data = item.data(0, Qt.UserRole)
            if data:
                lines.append(str(data))
        if lines:
            QGuiApplication.clipboard().setText("\n".join(lines))

    def _browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Folder wyjściowy")
        if folder:
            self.output_enabled_cb.setChecked(True)
            self._output_dir_manual = True
            self.output_dir_edit.setText(folder)
            log_event("Folder wyjściowy", folder)

    def _remove_files_for_folder(self, folder: Path) -> None:
        to_remove = [f for f in self._queue if self._file_roots.get(f) == folder]
        for f in to_remove:
            self._queue.remove(f)
            self._file_roots.pop(f, None)

    def _remove_selected(self) -> None:
        for item in self.input_tree.selectedItems():
            p = Path(item.data(0, Qt.UserRole))
            if self._item_kind(item) == "folder":
                if p in self._folder_queue:
                    self._folder_queue.remove(p)
                self._remove_files_for_folder(p)
            elif p in self._queue:
                self._queue.remove(p)
                self._file_roots.pop(p, None)
            parent = item.parent()
            if parent is not None and parent != self.input_tree.invisibleRootItem():
                parent.removeChild(item)
            else:
                idx = self.input_tree.indexOfTopLevelItem(item)
                if idx >= 0:
                    self.input_tree.takeTopLevelItem(idx)
        if not self._queue and not self._folder_queue:
            self._output_dir_manual = False
            self.output_dir_edit.clear()
        self._update_queue_label()

    def _clear_queue(self) -> None:
        self._queue.clear()
        self._folder_queue.clear()
        self._file_roots.clear()
        self._base_root = None
        self._output_dir_manual = False
        self.input_tree.clear()
        self.output_dir_edit.clear()
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
        if hasattr(self, "update_output_btn"):
            self.update_output_btn.setEnabled(bool(n_files or n_folders))
        if n_folders and not n_files:
            word = "folder" if n_folders == 1 else ("foldery" if 2 <= n_folders % 10 <= 4 else "folderów")
            self.queue_label.setText(f"{n_folders} {word}")
            return
        word = "plik" if n_files == 1 else ("pliki" if 2 <= n_files % 10 <= 4 and (n_files % 100 < 10 or n_files % 100 >= 20) else "plików")
        extra = f", {n_folders} folderów" if n_folders else ""
        self.queue_label.setText(f"{n_files} {word}{extra}")

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous) -> None:
        if not self.preview_cb.isChecked():
            return
        if current is None:
            self.preview_label.clear()
            self.size_info.setText("Zaznacz plik na liście")
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
                pix.scaled(112, 112, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        self.size_info.setText(f"{path.name}\n{self._format_size(path)}\n{path.parent}")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        self._handle_dropped_urls(event.mimeData().urls())
        event.acceptProposedAction()

    def _open_format_settings(self) -> None:
        self._lock_output_settings()
        fmt = self.format_combo.first_selected()
        dlg = FormatSettingsDialog(
            fmt,
            self._format_opts,
            self,
            resize=self._resize,
            transforms=self._transforms,
        )
        if dlg.exec():
            self._format_opts = dlg.get_options()
            self._resize = dlg.get_resize()
            self._transforms = dlg.get_transforms()
            self._last_size_preset_id = PRESET_ORIGINAL
            self._reload_size_combo(select_id=PRESET_ORIGINAL)
            self._mark_dirty()

    def _update_advanced_summary(self) -> None:
        """Zachowane dla kompatybilności sesji — zaawansowane są w zakładce ustawień formatu."""
        return

    def _on_size_preset_changed(self) -> None:
        if self._programmatic_settings:
            pid = self._current_size_preset_id()
            if pid != PRESET_SAVE_CUSTOM:
                self._last_size_preset_id = pid
            self._update_delete_preset_btn()
            return
        self._lock_output_settings()
        idx = self.size_combo.currentIndex()
        if idx < 0 or idx >= len(self._size_preset_ids):
            return
        pid = self._size_preset_ids[idx]
        if pid == PRESET_SAVE_CUSTOM:
            self._save_custom_size_preset()
            return
        payload = self._custom_preset_payloads.get(pid)
        self._apply_resize_preset()
        self._last_size_preset_id = pid
        self._update_delete_preset_btn()
        self._mark_dirty()

    def _preserve_bg_transform_fields(self, transforms: TransformOptions) -> TransformOptions:
        return replace(
            transforms,
            remove_background=self.remove_bg_cb.isChecked(),
            bg_model=str(self.bg_model_combo.currentData() or "birefnet-general"),
            bg_alpha_matting=True,
            bg_post_process_mask=True,
        )

    def _apply_resize_preset(self) -> None:
        pid = self._current_size_preset_id()
        if pid == PRESET_SAVE_CUSTOM:
            return
        payload = self._custom_preset_payloads.get(pid)
        resize, preset_transforms = apply_size_preset(pid, custom_payload=payload)
        self._resize = resize
        if is_custom_preset(pid) and payload and payload.get("transforms"):
            self._transforms = self._preserve_bg_transform_fields(preset_transforms)
        else:
            self._transforms = self._preserve_bg_transform_fields(self._transforms)

    def _apply_size_preset(self) -> None:
        self._apply_resize_preset()

    def _prepare_output_for_convert(self, inputs: list[Path]) -> bool:
        if self.wiz_sequence_cb.isChecked():
            return True
        if not self._output_path_active():
            return True
        explicit = self.output_dir_edit.text().strip()
        if explicit:
            self._output_layout = "single"
            return True
        self._output_layout = "beside"
        return True

    def _output_dir_for_input(self, inp: Path, queue: list[Path], explicit_out: str) -> Path:
        if explicit_out:
            return Path(explicit_out)
        root = self._structure_root_for(inp)
        return root / CONVERTED_FOLDER_NAME

    def _build_jobs(self, inputs: list[Path] | None = None) -> list[JobSpec]:
        queue = inputs if inputs is not None else self._queue
        use_output = self._output_path_active()
        explicit_out = self.output_dir_edit.text().strip() if use_output else ""
        formats = self._selected_formats()
        segregate = use_output and self.segregate_cb.isChecked() and len(formats) > 1
        self._apply_size_preset()
        self._format_opts.quality = self.quality_slider.value()

        jobs = []
        for fmt in formats:
            for inp in queue:
                if use_output:
                    out_dir = self._output_dir_for_input(inp, queue, explicit_out)
                else:
                    out_dir = inp.parent
                if self._rename.enabled:
                    name = preview_rename([inp], self._rename, fmt)[0][1]
                    if segregate:
                        sub = output_extension(fmt).lstrip(".").lower() or fmt.lower()
                        out = out_dir / sub / name
                    else:
                        out = out_dir / name
                else:
                    out = build_output_path(
                        inp, out_dir, fmt,
                        base_root=self._structure_root_for(inp) if use_output else None,
                        preserve_structure=use_output and self.preserve_cb.isChecked(),
                        segregate_by_extension=segregate,
                    )
                jobs.append(JobSpec(
                    input_path=inp,
                    output_path=out,
                    output_format=fmt,
                    resize=self._resize_for_job(),
                    transforms=self._transforms,
                    metadata=self._metadata,
                    format_opts=self._format_opts,
                ))
        return jobs

    def _filter_jobs_with_inplace_confirm(self, jobs: list[JobSpec]) -> list[JobSpec]:
        if self._output_path_active():
            return jobs
        existing = [j for j in jobs if j.output_path.exists()]
        if not existing:
            return jobs
        yes_all = False
        filtered: list[JobSpec] = []
        for i, job in enumerate(jobs):
            if not job.output_path.exists():
                filtered.append(job)
                continue
            if yes_all:
                filtered.append(job)
                continue
            remaining = sum(1 for j in jobs[i:] if j.output_path.exists())
            choice = ask_overwrite_inplace(
                self,
                filename=job.output_path.name,
                remaining=remaining,
            )
            if choice is None or choice == "no_all":
                return []
            if choice == "yes_all":
                yes_all = True
                filtered.append(job)
            elif choice == "yes":
                filtered.append(job)
            # "no" — pomiń ten plik
        return filtered

    def _start_convert_selected(self) -> None:
        paths = self._selected_file_paths()
        if not paths:
            show_warning(self, "Konwersja", "Zaznacz co najmniej jeden plik.")
            return
        self._start_convert_subset(paths)

    def _start_convert_subset(self, inputs: list[Path]) -> None:
        if self.wiz_sequence_cb.isChecked():
            show_warning(
                self,
                "Konwersja",
                "Przy sekwencji wizek użyj przycisku Konwertuj dla całej listy.",
            )
            return
        if not self.format_combo.selected_formats():
            show_warning(self, "Konwersja", "Zaznacz co najmniej jeden format wyjściowy.")
            return
        if not self._validate_bg_removal_ready():
            return
        if not self._prepare_output_for_convert(inputs):
            return
        jobs = self._build_jobs(inputs=inputs)
        jobs = self._filter_jobs_with_inplace_confirm(jobs)
        if not jobs:
            return
        overwrite = True
        if self._output_path_active() and self.overwrite_cb.isChecked():
            existing = [j for j in jobs if j.output_path.exists()]
            if existing:
                if not ask_yes_no(
                    self,
                    "Nadpisanie",
                    f"{len(existing)} plik(ów) już istnieje. Nadpisać?",
                ):
                    overwrite = False

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(False)
        self.progress_label.setVisible(False)
        self._batch_cancelled = False
        self._convert_start = time.time()
        self._active_jobs = jobs
        fmts = "+".join(self._selected_formats())
        preset = self._current_size_preset_id()
        log_event(
            "Start konwersji",
            f"{len(jobs)} zadań, formaty: {fmts}, preset: {preset}",
        )

        overlay_items = [(j.input_path.name, j.output_format) for j in jobs]
        bg_fast = any(
            j.transforms.remove_background
            and (j.transforms.bg_model or "birefnet-general") == "birefnet-general-lite"
            for j in jobs
        )
        self._conversion_overlay.start_batch(overlay_items, bg_fast_hint=bg_fast)

        worker = BatchWorker(jobs, parallel=self.parallel_cb.isChecked(), overwrite=overwrite)
        worker.progress.connect(self._on_progress)
        worker.file_started.connect(self._on_file_started)
        worker.file_finished.connect(self._on_file_finished)
        worker.finished.connect(self._on_finished)
        worker.error.connect(self._on_batch_error)
        worker.cancelled.connect(self._on_batch_cancelled)
        self._progress_simulator.tick.connect(self._on_simulated_progress)
        self._batch_thread = BatchThread(worker)
        self._batch_thread.start()

    def _on_overlay_abort(self) -> None:
        if not self._batch_thread or not self._batch_thread.isRunning():
            self._conversion_overlay.finish()
            return
        if not ask_yes_no(
            self,
            "Przerwać konwersję?",
            "Czy na pewno chcesz przerwać konwersję?\n"
            "Plik aktualnie przetwarzany może się jeszcze dokończyć.",
        ):
            return
        self._batch_cancelled = True
        self._batch_thread.request_cancel()
        self._progress_simulator.stop()
        self.statusBar().showMessage("Przerywanie konwersji…")

    def _on_batch_cancelled(self) -> None:
        self._batch_cancelled = True

    def _on_simulated_progress(self, index: int, percent: int, phase: str) -> None:
        if index < len(self._active_jobs):
            job = self._active_jobs[index]
            self._conversion_overlay.set_file_state(
                index,
                state=phase,
                percent=percent,
                detail=f"→ {job.output_format.upper()}",
            )
        eta = self._progress_simulator.estimate_remaining_sec()
        self._conversion_overlay.set_eta_seconds(eta)

    def _on_file_started(self, index: int, phase: str) -> None:
        if index >= len(self._active_jobs):
            return
        job = self._active_jobs[index]
        bg = job.transforms.remove_background
        self._progress_simulator.start_file(
            index,
            bg_removal=bg,
            bg_model=job.transforms.bg_model or "birefnet-general",
        )
        detail = f"→ {job.output_format.upper()}"
        if bg:
            model_label = (
                "Najlepsza jakość"
                if job.transforms.bg_model == "birefnet-general"
                else "Szybko"
            )
            detail = f"Usuwanie tła ({model_label}) · {job.output_format.upper()}"
        self._conversion_overlay.set_file_state(
            index,
            state=phase,
            percent=5,
            detail=detail,
            force=True,
        )
        eta = self._progress_simulator.estimate_remaining_sec()
        self._conversion_overlay.set_eta_seconds(eta)

    def _on_file_finished(self, index: int, status: str, message: str) -> None:
        self._progress_simulator.complete_file(index)
        ok = status == "OK"
        state = "Gotowe" if ok else "Błąd"
        detail = message[:120] if message and not ok else "Zapisano"
        self._conversion_overlay.set_file_state(
            index,
            state=state,
            percent=100 if ok else None,
            detail=detail,
            force=True,
        )
        self._conversion_overlay.set_eta_seconds(None)

    def _on_batch_error(self, message: str) -> None:
        log_event("Błąd konwersji", message, status="ERROR")
        self.convert_btn.setEnabled(True)
        self._progress_simulator.stop()
        self._conversion_overlay.finish()
        self._active_jobs = []
        show_critical(self, "Błąd", message)

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
        if not self._validate_bg_removal_ready():
            return
        self._start_convert_subset(self._queue)

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
        self.progress_label.setVisible(True)
        self.progress.setMaximum(len(folders))
        self.progress.setValue(0)
        self.progress_label.setText("Przygotowanie…")
        self._convert_start = time.time()
        log_event("Start sekwencji wizek", f"{len(folders)} folderów, jakość {self.quality_slider.value()}%")

        worker = WizWorker(folders, self.quality_slider.value())
        self._wiz_thread = WizThread(worker)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_wiz_finished)
        worker.error.connect(self._on_wiz_error)
        self._wiz_thread.start()

    def _on_wiz_error(self, message: str) -> None:
        log_event("Błąd sekwencji wizek", message, status="ERROR")
        show_critical(self, "Błąd", message)

    def _on_wiz_finished(self, results) -> None:
        elapsed = time.time() - self._convert_start
        self.convert_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.progress_label.setVisible(False)
        ok = sum(1 for r in results if r.status.value == "OK")
        err = len(results) - ok
        log_event(
            "Koniec sekwencji wizek",
            f"OK {ok}/{len(results)}, błędy {err}, {elapsed:.1f}s",
            status="OK" if err == 0 else "WARN",
        )
        self.statusBar().showMessage(f"Wizki gotowe — {ok}/{len(results)} folderów w {elapsed:.1f} s")
        dlg = WizResultsDialog(results, elapsed, self)
        dlg.exec()

    def _on_progress(self, current: int, total: int, name: str) -> None:
        self._conversion_overlay.set_overall(current, total)
        if total and current >= total:
            pct = 100
            line = f"Zakończono {current}/{total} ({pct}%) — {name}"
        elif total and current <= 0:
            pct = 0
            line = f"Przetwarzanie {name}…"
        else:
            pct = int(100 * current / total)
            line = f"Przetwarzanie {current}/{total} ({pct}%) — {name}"
        self.statusBar().showMessage(line)

    def _on_finished(self, results) -> None:
        elapsed = time.time() - self._convert_start
        self.convert_btn.setEnabled(True)
        self._progress_simulator.stop()
        self._conversion_overlay.set_overall(len(results), max(len(results), len(self._active_jobs)))
        self._conversion_overlay.finish()
        self._active_jobs = []
        if self._batch_cancelled:
            self.statusBar().showMessage("Konwersja przerwana przez użytkownika")
            if results:
                dlg = ResultsDialog(results, elapsed, self)
                dlg.exec()
            return
        ok = sum(1 for r in results if r.status.value == "OK")
        err = len(results) - ok
        log_event(
            "Koniec konwersji",
            f"OK {ok}/{len(results)}, błędy {err}, {elapsed:.1f}s",
            status="OK" if err == 0 else "WARN",
        )
        self.statusBar().showMessage(f"Gotowe — {ok}/{len(results)} plików w {elapsed:.1f} s")
        dlg = ResultsDialog(results, elapsed, self)
        dlg.exec()

    def _load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Wczytaj ustawienia", "", "JSON (*.json)")
        if path:
            self._lock_output_settings()
            data = load_preset(Path(path))
            applied = apply_preset(data)
            self._format_opts = applied["format_opts"]
            self._resize = applied["resize"]
            self._transforms = applied["transforms"]
            self._programmatic_settings = True
            try:
                self.quality_slider.setValue(self._format_opts.quality)
                self.png_colors_auto_cb.setChecked(self._format_opts.png_colors_auto)
                self.png_colors_slider.setValue(self._format_opts.png_max_colors)
                self.png_colors_slider.setEnabled(not self._format_opts.png_colors_auto)
                self.png_colors_label.setText(str(self._format_opts.png_max_colors))
                self.scale_slider.setValue(int(round(self._resize.scale_percent)))
                self.scale_label.setText(f"{int(round(self._resize.scale_percent))}%")
                self.min_longest_cb.setChecked(self._resize.min_longest_enabled)
                self.min_longest_edit.setText(str(self._resize.min_longest_px))
                self.format_combo.set_selected([applied["output_format"]])
            finally:
                self._programmatic_settings = False
            log_event("Wczytano preset JSON", path)

    def _save_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz ustawienia", "", "JSON (*.json)")
        if path:
            fmt = self.format_combo.first_selected()
            data = settings_to_dict(
                fmt, self._format_opts, self._resize, self._transforms,
                self._metadata, self._rename, self._batch,
            )
            save_preset(Path(path), data)
            log_event("Zapisano preset JSON", path)

    def _check_updates_manual(self) -> None:
        if not UpdateManager.is_supported():
            show_info(
                self,
                "Aktualizacje",
                "Automatyczne aktualizacje działają w wersji EXE (portable).\n"
                "Uruchom zbudowaną aplikację InyfinnPhotoResizer.exe.",
            )
            return
        self._update_manager.open_manual_dialog()

    def _about(self) -> None:
        show_about(
            self,
            "Inyfinn Photo Resizer",
            f"Inyfinn Photo Resizer {__version__}\n\n"
            "Wsadowa konwersja i kompresja zdjęć.\n"
            "WebP, AVIF, HEIC, GIF i inne formaty.",
        )

    def closeEvent(self, event) -> None:
        persist_all(self)
        if self._settings_dirty:
            auto_save_profile_rotating(snapshot_from_window(self))
        super().closeEvent(event)
