"""Główne okno — układ FastStone, siatka wierszy/kolumn."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt
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
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.dialogs.advanced_options import AdvancedOptionsDialog
from inyfinn_resizer.app.dialogs.format_settings import FormatSettingsDialog
from inyfinn_resizer.app.dialogs.results_dialog import ResultsDialog
from inyfinn_resizer.app.widgets.format_multi_combo import FormatMultiCombo
from inyfinn_resizer.app.widgets.layout_helpers import (
    ROW_GAP,
    action_button,
    add_form_row,
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inyfinn Photo Resizer 1.0")
        self.resize(940, 520)
        self.setMinimumSize(860, 480)
        self.setAcceptDrops(True)

        self._queue: list[Path] = []
        self._base_root: Path | None = None
        self._format_opts = FormatOptions(quality=85)
        self._resize = ResizeOptions()
        self._transforms = TransformOptions()
        self._metadata = MetadataPolicy()
        self._rename = RenameRule()
        self._batch = BatchSettings()
        self._batch_thread: BatchThread | None = None
        self._theme = "light"

        self._build_menu()
        self._build_ui()
        self.statusBar().showMessage("Gotowe — przeciągnij zdjęcia na listę po lewej")

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
        title = QLabel("Inyfinn Photo Resizer")
        title.setObjectName("appTitle")
        header.addWidget(title)
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

        # —— Prawy panel: ustawienia (kompakt) ——
        right_shell, right_layout = self._make_panel("Ustawienia konwersji", "panel")
        right_shell.setMinimumWidth(360)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setContentsMargins(0, 0, 0, 0)

        self.format_combo = FormatMultiCombo()
        self.format_combo.selectionChanged.connect(self._on_formats_changed)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        fmt_row.addWidget(self.format_combo, stretch=1)
        self.settings_btn = QPushButton("Ustawienia…")
        self.settings_btn.setObjectName("btnSecondary")
        self.settings_btn.setFixedSize(108, 36)
        self.settings_btn.clicked.connect(self._open_format_settings)
        fmt_row.addWidget(self.settings_btn)
        fmt_wrap = QWidget()
        fmt_wrap.setLayout(fmt_row)
        add_form_row(form, 0, "Format:", fmt_wrap)

        self.segregate_cb = QCheckBox("Segreguj do podfolderów (webp/, jpg/…)")
        self.segregate_cb.setChecked(True)
        self.segregate_cb.setEnabled(False)
        form.addWidget(self.segregate_cb, 1, 1)

        self.size_combo = QComboBox()
        self.size_combo.setMinimumHeight(36)
        self.size_combo.addItems([
            "Oryginalny rozmiar",
            "Maks. 1800 px (szerokość)",
            "Maks. 1200 px",
            "50%",
        ])
        add_form_row(form, 2, "Rozmiar:", self.size_combo)

        qual_wrap = QWidget()
        qual_row = QHBoxLayout(qual_wrap)
        qual_row.setContentsMargins(0, 0, 0, 0)
        qual_row.setSpacing(8)
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        self.quality_label = QLabel("85")
        self.quality_label.setObjectName("qualityValue")
        self.quality_label.setFixedWidth(28)
        self.quality_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        qual_row.addWidget(self.quality_slider, stretch=1)
        qual_row.addWidget(self.quality_label)
        add_form_row(form, 3, "Jakość:", qual_wrap)

        adv_row = QHBoxLayout()
        self.advanced_cb = QCheckBox("Opcje zaawansowane")
        adv_row.addWidget(self.advanced_cb)
        self.advanced_btn = QPushButton("Otwórz…")
        self.advanced_btn.setObjectName("btnSecondary")
        self.advanced_btn.setFixedSize(88, 36)
        self.advanced_btn.clicked.connect(self._open_advanced)
        adv_row.addWidget(self.advanced_btn)
        adv_wrap = QWidget()
        adv_wrap.setLayout(adv_row)
        add_form_row(form, 4, "Zaawans.:", adv_wrap)

        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Folder docelowy…")
        self.output_dir_edit.setMinimumHeight(36)
        browse_out = QPushButton("Przeglądaj…")
        browse_out.setObjectName("btnSecondary")
        browse_out.setFixedSize(108, 36)
        browse_out.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_dir_edit, stretch=1)
        out_row.addWidget(browse_out)
        out_wrap = QWidget()
        out_wrap.setLayout(out_row)
        add_form_row(form, 5, "Wyjście:", out_wrap)

        right_layout.addLayout(form)

        more_box = QGroupBox("Więcej opcji")
        more_box.setObjectName("moreOptions")
        more_box.setCheckable(True)
        more_box.setChecked(False)
        more_lay = QVBoxLayout(more_box)
        more_lay.setContentsMargins(10, 12, 10, 10)
        more_lay.setSpacing(6)
        for text, attr, checked in [
            ("Zachowaj strukturę folderów", "preserve_cb", True),
            ("Zachowaj datę i godzinę", "keep_dates_cb", True),
            ("Pytaj przed nadpisaniem", "overwrite_cb", True),
            ("Wiele plików naraz (szybciej)", "parallel_cb", True),
        ]:
            cb = QCheckBox(text)
            cb.setChecked(checked)
            setattr(self, attr, cb)
            more_lay.addWidget(cb)
        preview_row = QHBoxLayout()
        self.preview_cb = QCheckBox("Podgląd")
        self.preview_cb.setChecked(True)
        preview_row.addWidget(self.preview_cb)
        preview_row.addStretch()
        more_lay.addLayout(preview_row)
        prev_row = QHBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewBox")
        self.preview_label.setFixedSize(72, 72)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.size_info = QLabel("")
        self.size_info.setObjectName("previewMeta")
        self.size_info.setWordWrap(True)
        prev_row.addWidget(self.preview_label)
        prev_row.addWidget(self.size_info, stretch=1)
        more_lay.addLayout(prev_row)
        right_layout.addWidget(more_box)

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
        splitter.setSizes([560, 420])
        return splitter

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
        preview_btn.setFixedHeight(36)
        preview_btn.clicked.connect(self._preview_rename)
        layout.addWidget(preview_btn, alignment=Qt.AlignLeft)
        return w

    def _toggle_theme(self) -> None:
        self._set_theme("dark" if self._theme == "light" else "light")

    def _set_theme(self, theme: str) -> None:
        from PySide6.QtWidgets import QApplication

        from inyfinn_resizer.app.themes import apply_theme

        self._theme = theme
        apply_theme(QApplication.instance(), theme)
        self.theme_btn.setText("Jasny motyw" if theme == "dark" else "Ciemny motyw")

    def _on_formats_changed(self) -> None:
        n = len(self.format_combo.selected_formats())
        self.segregate_cb.setEnabled(n > 1)
        if n <= 1:
            self.segregate_cb.setChecked(False)

    def _selected_formats(self) -> list[str]:
        fmts = self.format_combo.selected_formats()
        return fmts if fmts else ["webp"]

    def _on_quality_changed(self, v: int) -> None:
        self.quality_label.setText(str(v))
        self._format_opts.quality = v

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
        item.setToolTip(0, str(path))
        self.input_tree.addTopLevelItem(item)
        if self._base_root is None:
            self._base_root = path.parent
        self._update_queue_label()

    def _paths_from_items(self, items: list[QTreeWidgetItem]) -> list[Path]:
        paths = []
        for item in items:
            data = item.data(0, Qt.UserRole)
            if data:
                paths.append(Path(data))
        return paths

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
        if folder:
            root = Path(folder)
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
            for p in self._paths_from_items([item]):
                if p in self._queue:
                    self._queue.remove(p)
            idx = self.input_tree.indexOfTopLevelItem(item)
            if idx >= 0:
                self.input_tree.takeTopLevelItem(idx)
        self._update_queue_label()

    def _clear_queue(self) -> None:
        self._queue.clear()
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
        n = len(self._queue)
        word = "plik" if n == 1 else ("pliki" if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20) else "plików")
        self.queue_label.setText(f"{n} {word}")

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous) -> None:
        if not self.preview_cb.isChecked() or current is None:
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
            if p.is_file() and is_image_file(p):
                self._add_path_to_queue(p)
            elif p.is_dir():
                self._base_root = p
                for f in sorted(p.rglob("*")):
                    if f.is_file() and is_image_file(f):
                        self._add_path_to_queue(f)
        event.acceptProposedAction()

    def _open_format_settings(self) -> None:
        fmt = self.format_combo.first_selected()
        dlg = FormatSettingsDialog(fmt, self._format_opts, self)
        if dlg.exec():
            self._format_opts = dlg.get_options()

    def _open_advanced(self) -> None:
        dlg = AdvancedOptionsDialog(self._resize, self._transforms, self)
        if dlg.exec():
            self._resize = dlg.get_resize()
            self._transforms = dlg.get_transforms()
            self.advanced_cb.setChecked(self._resize.mode.value != "none")

    def _apply_size_preset(self) -> None:
        from inyfinn_resizer.core.job import ResizeMode

        idx = self.size_combo.currentIndex()
        if idx == 0:
            self._resize = ResizeOptions()
        elif idx == 1:
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
        if not self._queue:
            QMessageBox.warning(self, "Konwersja", "Lista plików jest pusta.")
            return
        if not self.format_combo.selected_formats():
            QMessageBox.warning(self, "Konwersja", "Zaznacz co najmniej jeden format wyjściowy.")
            return
        jobs = self._build_jobs()
        overwrite = True
        if self.overwrite_cb.isChecked():
            existing = [j for j in jobs if j.output_path.exists()]
            if existing:
                r = QMessageBox.question(
                    self,
                    "Nadpisanie",
                    f"{len(existing)} plik(ów) już istnieje. Nadpisać?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if r != QMessageBox.Yes:
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
        worker.error.connect(lambda e: QMessageBox.critical(self, "Błąd", e))
        self._batch_thread.start()

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
        self.rename_preview.clear()
        fmt = self.format_combo.first_selected()
        rule = RenameRule(
            enabled=True,
            template=self.rename_template.text(),
            search=self.rename_search.text(),
            replace=self.rename_replace.text(),
        )
        for old, new in preview_rename(self._queue, rule, fmt):
            self.rename_preview.addItem(f"{old.name}  →  {new}")

    def _load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Wczytaj ustawienia", "", "JSON (*.json)")
        if path:
            data = load_preset(Path(path))
            applied = apply_preset(data)
            self._format_opts = applied["format_opts"]
            self._resize = applied["resize"]
            self._transforms = applied["transforms"]
            self.quality_slider.setValue(self._format_opts.quality)
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
        QMessageBox.about(
            self,
            "Inyfinn Photo Resizer",
            "Inyfinn Photo Resizer 1.0\n\n"
            "Wsadowa konwersja i kompresja zdjęć.\n"
            "WebP, AVIF, HEIC, GIF i inne formaty.",
        )
