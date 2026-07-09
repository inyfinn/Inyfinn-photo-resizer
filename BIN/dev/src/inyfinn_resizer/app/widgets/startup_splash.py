"""Lekki ekran startowy — widoczny od pierwszej klatki."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QColor, QPen
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget, QApplication


class _SpinnerWidget(QWidget):
    """Obracający się pierścień ładowania."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)
        pen = QPen(QColor("#cbd5e1"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        pen.setColor(QColor("#008834"))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        span = 90 * 16
        start = -self._angle * 16
        painter.drawArc(rect, start, span)
        painter.end()

    def stop(self) -> None:
        self._timer.stop()


class StartupSplash(QWidget):
    def __init__(self, icon: QIcon | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("startupSplash")
        self.setFixedSize(400, 196)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)

        title = QLabel("Inyfinn Photo Resizer")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self._spinner = _SpinnerWidget(self)
        root.addWidget(self._spinner, alignment=Qt.AlignCenter)

        self._status = QLabel("Ładowanie aplikacji…")
        self._status.setObjectName("splashStatus")
        self._status.setAlignment(Qt.AlignCenter)
        root.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setObjectName("splashProgress")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        root.addWidget(self._bar)

        if icon is not None:
            self.setWindowIcon(icon)

        self.setStyleSheet(
            """
            QWidget#startupSplash {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f1f5f9);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 10px;
            }
            QLabel#splashTitle {
                font-size: 16px;
                font-weight: 700;
                color: #0f172a;
            }
            QLabel#splashStatus {
                font-size: 12px;
                color: #64748b;
            }
            QProgressBar#splashProgress {
                background: rgba(0, 0, 0, 0.06);
                border: none;
                border-radius: 3px;
            }
            QProgressBar#splashProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #76b82a, stop:1 #008834);
                border-radius: 3px;
            }
            """
        )
        self._slide = QPropertyAnimation(self._bar, b"value")
        self._slide.setDuration(1400)
        self._slide.setStartValue(8)
        self._slide.setEndValue(92)
        self._slide.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._slide.setLoopCount(-1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._slide.start()

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.x() + (geo.width() - self.width()) // 2,
            geo.y() + (geo.height() - self.height()) // 2,
        )

    def finish(self, main_window: QWidget) -> None:
        self._slide.stop()
        self._spinner.stop()
        self._bar.setValue(100)
        self.set_status("Gotowe")
        QApplication.processEvents()
        self.close()
