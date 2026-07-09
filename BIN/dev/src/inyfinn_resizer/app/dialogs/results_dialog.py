"""Raport po konwersji — po polsku, układ jak FastStone (przesuwalne kolumny)."""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.app.user_settings import (
    restore_results_dialog_geometry,
    restore_results_table_header,
    save_results_dialog_geometry,
    save_results_table_header,
)
from inyfinn_resizer.core.job import JobResult, JobStatus

_STATUS_PL = {
    JobStatus.OK: "OK",
    JobStatus.ERROR: "Błąd",
    JobStatus.SKIPPED: "Pominięto",
    JobStatus.PENDING: "Oczekuje",
}

_PROFILE_PL = {
    "xl": "XL (master)",
    "sklep": "Sklep",
    "standard": "Standard",
}

RESULTS_DIALOG_WIDTH = 1018
RESULTS_DIALOG_HEIGHT = 608
RESULTS_DIALOG_MIN_WIDTH = 720
RESULTS_DIALOG_MIN_HEIGHT = 420

_COL_LP = 0
_COL_IN = 1
_COL_OUT = 2
_COL_STATUS = 3
_COL_OLD = 4
_COL_NEW = 5
_COL_RATIO = 6
_COL_SAVE = 7

_DEFAULT_WIDTHS = {
    _COL_LP: 44,
    _COL_IN: 200,
    _COL_OUT: 200,
    _COL_STATUS: 280,
    _COL_OLD: 100,
    _COL_NEW: 100,
    _COL_RATIO: 110,
    _COL_SAVE: 110,
}


def _configure_results_table(table: QTableWidget) -> QHeaderView:
    table.setObjectName("resultsTable")
    table.setShowGrid(True)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setCornerButtonEnabled(False)

    hdr = table.horizontalHeader()
    hdr.setStretchLastSection(True)
    hdr.setSectionsMovable(True)
    hdr.setSectionsClickable(True)
    hdr.setHighlightSections(True)
    hdr.setMinimumSectionSize(56)
    hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    hdr.setSectionResizeMode(_COL_LP, QHeaderView.ResizeMode.Fixed)
    for col, width in _DEFAULT_WIDTHS.items():
        table.setColumnWidth(col, width)
    hdr.setSortIndicatorShown(False)
    return hdr


class ResultsDialog(AppDialog):
    def __init__(self, results: list[JobResult], elapsed_sec: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wyniki konwersji")
        self.resize(RESULTS_DIALOG_WIDTH, RESULTS_DIALOG_HEIGHT)
        self.setMinimumSize(RESULTS_DIALOG_MIN_WIDTH, RESULTS_DIALOG_MIN_HEIGHT)
        self.setSizeGripEnabled(True)
        self._results = results
        self._output_dir = None
        if results and results[0].job.output_path.parent:
            self._output_dir = results[0].job.output_path.parent

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        ok_count = sum(1 for r in results if r.status == JobStatus.OK)
        err_count = sum(1 for r in results if r.status == JobStatus.ERROR)
        status_line = f"Przetworzono: {ok_count} z {len(results)} plików"
        if err_count:
            status_line += f"  ({err_count} błędów)"
        header.addWidget(QLabel(status_line))
        header.addStretch()
        self.parallel_cb = QCheckBox("Wiele plików jednocześnie")
        self.parallel_cb.setChecked(True)
        self.parallel_cb.setEnabled(False)
        header.addWidget(self.parallel_cb)
        layout.addLayout(header)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            [
                "Lp.",
                "Plik wejściowy",
                "Plik wyjściowy",
                "Status",
                "Stary rozmiar",
                "Nowy rozmiar",
                "Stosunek (%)",
                "Oszczędność (KB)",
            ]
        )
        self._table_header = _configure_results_table(self.table)
        if not restore_results_table_header(self._table_header):
            pass
        restore_results_dialog_geometry(self)
        layout.addWidget(self.table, stretch=1)

        total_old = sum(r.old_bytes for r in results)
        total_new = sum(r.new_bytes for r in results)
        ratio = round(100.0 * total_new / total_old, 0) if total_old else 0
        saved = (total_old - total_new) / 1024.0

        self.progress = QProgressBar()
        self.progress.setObjectName("resultsProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(int(ratio))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(16)
        progress_row = QHBoxLayout()
        progress_row.addWidget(QLabel(f"Kompresja: {ratio:.0f}%"))
        progress_row.addWidget(self.progress, stretch=1)
        layout.addLayout(progress_row)

        footer = QHBoxLayout()
        footer.addWidget(
            QLabel(
                f"Razem przed: {total_old // 1024:,} KB  |  "
                f"Razem po: {total_new // 1024:,} KB  |  "
                f"Stosunek: {ratio:.0f}%  |  "
                f"Oszczędność: {saved:,.0f} KB"
            )
        )
        footer.addStretch()
        footer.addWidget(QLabel(f"Czas: {self._fmt_time(elapsed_sec)}"))
        layout.addLayout(footer)

        self.open_folder_cb = QCheckBox("Otwórz folder z wynikami")
        self.open_folder_cb.setChecked(False)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        polish_dialog_buttons(buttons)
        buttons.button(QDialogButtonBox.Ok).setText("Gotowe")
        buttons.accepted.connect(self._on_done)
        row = QHBoxLayout()
        row.addWidget(self.open_folder_cb)
        row.addStretch()
        row.addWidget(buttons)
        layout.addLayout(row)

        self._populate()

    def _fmt_time(self, sec: float) -> str:
        m, s = divmod(int(sec), 60)
        return f"{m:02d}:{s:02d}"

    def _cell(self, text: str, *, tooltip: str = "") -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tip = tooltip or text
        if tip:
            item.setToolTip(tip)
        return item

    def _populate(self) -> None:
        self.table.setRowCount(len(self._results))
        for i, r in enumerate(self._results):
            in_path = str(r.job.input_path)
            out_path = str(r.job.output_path)
            saved_kb = max(0.0, (r.old_bytes - r.new_bytes) / 1024.0)

            self.table.setItem(i, _COL_LP, self._cell(str(i + 1)))
            self.table.setItem(
                i, _COL_IN, self._cell(r.job.input_path.name, tooltip=in_path)
            )
            self.table.setItem(
                i, _COL_OUT, self._cell(r.job.output_path.name, tooltip=out_path)
            )

            status = _STATUS_PL.get(r.status, str(r.status.value))
            if r.status == JobStatus.ERROR and r.message:
                status = f"Błąd — {r.message}"
            status_item = self._cell(status, tooltip=r.message or status)
            if r.status == JobStatus.ERROR:
                status_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(i, _COL_STATUS, status_item)

            self.table.setItem(i, _COL_OLD, self._cell(f"{r.old_kb:,.0f} KB"))
            self.table.setItem(i, _COL_NEW, self._cell(f"{r.new_kb:,.0f} KB"))
            self.table.setItem(i, _COL_RATIO, self._cell(f"{r.ratio_pct:.0f}%"))
            self.table.setItem(i, _COL_SAVE, self._cell(f"{saved_kb:,.0f} KB"))

    def _on_done(self) -> None:
        save_results_table_header(self._table_header)
        save_results_dialog_geometry(self)
        if self.open_folder_cb.isChecked() and self._output_dir:
            if sys.platform == "win32":
                os.startfile(str(self._output_dir))
            else:
                subprocess.Popen(["xdg-open", str(self._output_dir)])
        self.accept()


class WizResultsDialog(AppDialog):
    def __init__(self, results, elapsed_sec: float, parent=None):
        super().__init__(parent)
        from inyfinn_resizer.core.wiz_sequence import WizFolderResult

        self.setWindowTitle("Wyniki sekwencji wizek")
        self.resize(RESULTS_DIALOG_WIDTH, RESULTS_DIALOG_HEIGHT)
        self.setMinimumSize(RESULTS_DIALOG_MIN_WIDTH, RESULTS_DIALOG_MIN_HEIGHT)
        self.setSizeGripEnabled(True)
        self._results: list[WizFolderResult] = results
        self._output_dir = results[0].folder if results else None

        layout = QVBoxLayout(self)
        ok = sum(1 for r in results if r.status == JobStatus.OK)
        layout.addWidget(QLabel(f"Foldery: {ok}/{len(results)} zakończone pomyślnie — przetwarzanie in-place"))

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Folder", "Plik", "Profil", "Status", "Przed", "Po"]
        )
        _configure_results_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, stretch=1)

        row = 0
        for folder_result in results:
            for fr in folder_result.files:
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(folder_result.folder.name))
                self.table.setItem(row, 1, QTableWidgetItem(fr.name))
                self.table.setItem(row, 2, QTableWidgetItem(_PROFILE_PL.get(fr.profile, fr.profile)))
                self.table.setItem(row, 3, QTableWidgetItem(_STATUS_PL.get(fr.status, fr.status.value)))
                self.table.setItem(row, 4, QTableWidgetItem(f"{fr.old_bytes // 1024} KB"))
                self.table.setItem(row, 5, QTableWidgetItem(f"{fr.new_bytes // 1024} KB"))
                row += 1

        total_old = sum(r.old_bytes for r in results)
        total_new = sum(r.new_bytes for r in results)
        layout.addWidget(QLabel(
            f"Razem: {total_old // 1024:,} KB → {total_new // 1024:,} KB  |  "
            f"Czas: {int(elapsed_sec // 60):02d}:{int(elapsed_sec % 60):02d}"
        ))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        polish_dialog_buttons(buttons)
        buttons.button(QDialogButtonBox.Ok).setText("Gotowe")
        self.open_folder_cb = QCheckBox("Otwórz pierwszy folder")
        buttons.accepted.connect(self._on_done)
        bottom = QHBoxLayout()
        bottom.addWidget(self.open_folder_cb)
        bottom.addStretch()
        bottom.addWidget(buttons)
        layout.addLayout(bottom)

    def _on_done(self) -> None:
        if self.open_folder_cb.isChecked() and self._output_dir:
            if sys.platform == "win32":
                os.startfile(str(self._output_dir))
            else:
                subprocess.Popen(["xdg-open", str(self._output_dir)])
        self.accept()
