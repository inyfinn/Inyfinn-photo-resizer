"""Raport po konwersji — po polsku, spójny motyw."""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.core.job import JobResult, JobStatus

_STATUS_PL = {
    JobStatus.OK: "OK",
    JobStatus.ERROR: "Błąd",
    JobStatus.SKIPPED: "Pominięto",
    JobStatus.PENDING: "Oczekuje",
}


class ResultsDialog(AppDialog):
    def __init__(self, results: list[JobResult], elapsed_sec: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wyniki konwersji")
        self.resize(880, 460)
        self._results = results
        self._output_dir = None
        if results and results[0].job.output_path.parent:
            self._output_dir = results[0].job.output_path.parent

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        ok_count = sum(1 for r in results if r.status == JobStatus.OK)
        header.addWidget(QLabel(f"Przetworzono: {ok_count} z {len(results)} plików"))
        header.addStretch()
        self.parallel_cb = QCheckBox("Wiele plików jednocześnie")
        self.parallel_cb.setChecked(True)
        self.parallel_cb.setEnabled(False)
        header.addWidget(self.parallel_cb)
        layout.addLayout(header)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("resultsTable")
        self.table.setHorizontalHeaderLabels(
            ["Lp.", "Plik wejściowy", "Plik wyjściowy", "Status", "Stary rozmiar", "Nowy rozmiar", "Stosunek (%)"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        total_old = sum(r.old_bytes for r in results)
        total_new = sum(r.new_bytes for r in results)
        ratio = round(100.0 * total_new / total_old, 0) if total_old else 0
        saved = (total_old - total_new) / 1024.0

        self.progress = QProgressBar()
        self.progress.setValue(100)
        layout.addWidget(self.progress)

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

    def _populate(self) -> None:
        self.table.setRowCount(len(self._results))
        for i, r in enumerate(self._results):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(r.job.input_path.name))
            self.table.setItem(i, 2, QTableWidgetItem(r.job.output_path.name))
            self.table.setItem(i, 3, QTableWidgetItem(_STATUS_PL.get(r.status, str(r.status.value))))
            self.table.setItem(i, 4, QTableWidgetItem(f"{r.old_kb:.1f} KB"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{r.new_kb:.1f} KB"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{r.ratio_pct:.0f}%"))

    def _on_done(self) -> None:
        if self.open_folder_cb.isChecked() and self._output_dir:
            if sys.platform == "win32":
                os.startfile(str(self._output_dir))
            else:
                subprocess.Popen(["xdg-open", str(self._output_dir)])
        self.accept()
