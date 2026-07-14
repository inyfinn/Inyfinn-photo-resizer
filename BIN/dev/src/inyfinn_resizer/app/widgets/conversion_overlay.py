"""Overlay postępu konwersji — karty per plik na środku okna."""

from __future__ import annotations

import time
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer.app.i18n_pl import FORMAT_LABEL_PL
from inyfinn_resizer.app.i18n_tooltips import UI_TOOLTIPS


@dataclass
class FileProgressItem:
    name: str
    fmt: str
    state: str = "Oczekiwanie"
    percent: int = 0
    detail: str = ""


class _FileCard(QFrame):
    def __init__(self, item: FileProgressItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fileProgressCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._item = item

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        self._icon = QLabel(item.fmt.upper())
        self._icon.setObjectName("fileProgressExt")
        self._icon.setFixedSize(36, 36)
        self._icon.setAlignment(Qt.AlignCenter)
        top.addWidget(self._icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name = QLabel(item.name)
        self._name.setObjectName("fileProgressName")
        self._meta = QLabel()
        self._meta.setObjectName("fileProgressMeta")
        text_col.addWidget(self._name)
        text_col.addWidget(self._meta)
        top.addLayout(text_col, stretch=1)

        self._pct = QLabel("0%")
        self._pct.setObjectName("fileProgressPct")
        self._pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._pct.setMinimumWidth(36)
        top.addWidget(self._pct)
        root.addLayout(top)

        self._bar = QProgressBar()
        self._bar.setObjectName("fileProgressBar")
        self._bar.setFixedHeight(6)
        self._bar.setTextVisible(False)
        self._bar.setRange(0, 100)
        root.addWidget(self._bar)

        self.refresh()

    def refresh(self) -> None:
        fmt_label = FORMAT_LABEL_PL.get(self._item.fmt, self._item.fmt.upper())
        size_hint = self._item.detail or self._item.state
        self._meta.setText(f"{fmt_label} · {size_hint}")
        self._bar.setValue(self._item.percent)
        self._pct.setText(f"{self._item.percent}%")
        self.setProperty("status", self._status_key())
        self.style().unpolish(self)
        self.style().polish(self)

    def _status_key(self) -> str:
        st = self._item.state.lower()
        if "błąd" in st or "error" in st:
            return "error"
        if "gotow" in st or "zakoń" in st:
            return "done"
        if "przetwarz" in st or "kompres" in st or "usuwanie" in st:
            return "active"
        return "waiting"


class ConversionOverlay(QWidget):
    """Półprzezroczysta warstwa z kartami postępu — część głównego okna."""

    abort_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("conversionOverlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.hide()

        self._started_at = 0.0
        self._eta_sec: float | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        self._panel = QFrame()
        self._panel.setObjectName("conversionOverlayPanel")
        self._panel.setFrameShape(QFrame.Shape.NoFrame)
        self._panel.setMaximumWidth(540)
        self._panel.setMinimumWidth(400)
        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(16, 12, 16, 14)
        panel_lay.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self._title = QLabel("Konwersja plików")
        self._title.setObjectName("conversionOverlayTitle")
        title_row.addWidget(self._title, stretch=1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("overlayAbortBtn")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setToolTip("Przerwij konwersję (Esc)")
        self._close_btn.clicked.connect(self._request_abort)
        title_row.addWidget(self._close_btn, 0, Qt.AlignTop | Qt.AlignRight)
        panel_lay.addLayout(title_row)

        self._summary = QLabel("")
        self._summary.setObjectName("conversionOverlaySummary")
        panel_lay.addWidget(self._summary)

        self._bg_hint = QLabel("")
        self._bg_hint.setObjectName("conversionOverlayHint")
        self._bg_hint.setWordWrap(True)
        self._bg_hint.hide()
        panel_lay.addWidget(self._bg_hint)

        self._time_label = QLabel("Czas: 00:00  ·  ETA: --:--")
        self._time_label.setObjectName("conversionOverlayTime")
        panel_lay.addWidget(self._time_label)

        scroll = QScrollArea()
        scroll.setObjectName("conversionOverlayScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setLineWidth(0)
        scroll.setMaximumHeight(280)

        self._list_host = QWidget()
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_host)
        panel_lay.addWidget(scroll)

        self._overall = QProgressBar()
        self._overall.setObjectName("conversionOverlayOverall")
        self._overall.setFixedHeight(8)
        self._overall.setTextVisible(False)
        panel_lay.addWidget(self._overall)

        outer.addWidget(self._panel, alignment=Qt.AlignCenter)

        self._items: list[FileProgressItem] = []
        self._cards: list[_FileCard] = []

        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._update_clock)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self._request_abort()
            event.accept()
            return
        super().keyPressEvent(event)

    def _request_abort(self) -> None:
        self.abort_requested.emit()

    def start_batch(
        self,
        jobs: list[tuple[str, str]],
        *,
        bg_fast_hint: bool = False,
    ) -> None:
        self._clear_cards()
        self._started_at = time.monotonic()
        self._eta_sec = None
        if bg_fast_hint:
            self._bg_hint.setText(UI_TOOLTIPS["bg_fast_conversion_hint"])
            self._bg_hint.show()
        else:
            self._bg_hint.hide()
        self._items = [FileProgressItem(name=n, fmt=f) for n, f in jobs]
        for item in self._items:
            card = _FileCard(item, self._list_host)
            self._cards.append(card)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)
        self._overall.setMaximum(max(1, len(self._items)))
        self._overall.setValue(0)
        self._update_summary()
        self._update_clock()
        self._clock.start()
        self.show()
        self.raise_()
        self.setFocus()

    def set_eta_seconds(self, seconds: float | None) -> None:
        self._eta_sec = seconds
        self._update_clock()

    def set_file_state(
        self,
        index: int,
        *,
        state: str | None = None,
        percent: int | None = None,
        detail: str | None = None,
        force: bool = False,
    ) -> None:
        if index < 0 or index >= len(self._items):
            return
        item = self._items[index]
        if state is not None:
            item.state = state
        if percent is not None:
            new_pct = max(0, min(100, percent))
            if force or new_pct >= item.percent or new_pct == 100:
                item.percent = new_pct
        if detail is not None:
            item.detail = detail
        if index < len(self._cards):
            self._cards[index].refresh()

    def set_overall(self, current: int, total: int) -> None:
        self._overall.setMaximum(max(1, total))
        self._overall.setValue(min(current, total))
        done = sum(
            1 for i in self._items
            if "gotow" in i.state.lower() or "zakoń" in i.state.lower()
        )
        err = sum(1 for i in self._items if "błąd" in i.state.lower())
        self._summary.setText(
            f"Przetworzono {done} z {total}" + (f" · {err} błędów" if err else "")
        )

    def finish(self) -> None:
        self._clock.stop()
        self.hide()

    def _fmt_clock(self, sec: float) -> str:
        sec = max(0, int(sec))
        m, s = divmod(sec, 60)
        return f"{m:02d}:{s:02d}"

    def _update_clock(self) -> None:
        if not self.isVisible():
            return
        elapsed = time.monotonic() - self._started_at
        if self._eta_sec is not None and self._eta_sec > 0:
            eta_txt = self._fmt_clock(self._eta_sec)
        else:
            eta_txt = "--:--"
        self._time_label.setText(f"Czas: {self._fmt_clock(elapsed)}  ·  ETA: {eta_txt}")

    def _update_summary(self) -> None:
        total = len(self._items)
        self._summary.setText(f"0 z {total} plików")

    def _clear_cards(self) -> None:
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._items.clear()
