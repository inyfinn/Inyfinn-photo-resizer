"""Lekki ekran startowy — widoczny od pierwszej klatki."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget, QApplication


class StartupSplash(QWidget):
    def __init__(self, icon: QIcon | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("startupSplash")
        self.setFixedSize(400, 156)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        title = QLabel("Inyfinn Photo Resizer")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self._status = QLabel("Ładowanie aplikacji…")
        self._status.setObjectName("splashStatus")
        self._status.setAlignment(Qt.AlignCenter)
        root.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setObjectName("splashProgress")
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
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
                border-radius: 4px;
            }
            QProgressBar#splashProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #76b82a, stop:1 #008834);
                border-radius: 4px;
            }
            """
        )
        self._pulse = QPropertyAnimation(self._bar, b"maximum")
        self._pulse.setDuration(900)
        self._pulse.setStartValue(0)
        self._pulse.setEndValue(1)
        self._pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse.setLoopCount(-1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._pulse.start()

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
        self._pulse.stop()
        self.set_status("Gotowe")
        QApplication.processEvents()
        self.close()
