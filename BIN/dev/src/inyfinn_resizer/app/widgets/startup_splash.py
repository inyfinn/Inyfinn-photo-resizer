"""Ekran startowy w stylu Dobra Kaloria — taki sam jak w programie „Stwórz prezentację” 1.1.2.

560×330, zieleń marki, białe logo, nazwa programu czcionką Mindset, na dole na żywo: kółko ładowania,
„Uruchamiam program…”, szacowany czas i żółty pasek postępu (dochodzi do 92% w przewidywanym czasie,
potem wolno pełznie; przed zamknięciem na chwilę 100%). Wzór: WORK\\src\\launcher\\launcher.cs (klasa Splash)
i WORK\\powitanie.py.

Przewidywany czas = zmierzony czas poprzedniego startu (QSettings ``startup/last_seconds``);
pierwszy start: 6 s z dysku lokalnego, 15 s z dysku sieciowego. Nowy czas zapisuje ``save_startup_seconds``
po pokazaniu głównego okna. Twardy limit wyświetlania: 120 s.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

from PySide6.QtCore import QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

SPLASH_W, SPLASH_H = 560, 330
BRAND_GREEN = QColor("#0F763E")
YELLOW = QColor("#FFD42A")
SOFT_TEXT = QColor("#E0ECE4")
TRACK = QColor(255, 255, 255, 70)  # ok. 27% bieli
APP_TITLE = "Inyfinn Photo Resizer"
DEFAULT_LOCAL_S = 6.0
DEFAULT_NETWORK_S = 15.0
MAX_SHOW_MS = 120_000
FRAME_MS = 30  # ~33 klatki na sekundę
_SETTINGS_KEY = "startup/last_seconds"


def _settings() -> QSettings:
    return QSettings("Inyfinn", "PhotoResizer")


def _on_network_drive(path: str) -> bool:
    if path.startswith("\\\\"):
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        root = str(Path(path).resolve().anchor) or path[:3]
        return ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)) == 4  # DRIVE_REMOTE
    except Exception:
        return False


def load_startup_seconds() -> float:
    """Czas poprzedniego startu albo wartość domyślna (lokalnie 6 s, sieć 15 s)."""
    try:
        raw = _settings().value(_SETTINGS_KEY, None)
        if raw is not None:
            value = float(raw)
            if 0.5 <= value <= 120:
                return value
    except (TypeError, ValueError):
        pass
    exe = sys.executable if getattr(sys, "frozen", False) else __file__
    return DEFAULT_NETWORK_S if _on_network_drive(exe) else DEFAULT_LOCAL_S


def save_startup_seconds(seconds: float) -> None:
    if 0.2 <= seconds <= 600:
        _settings().setValue(_SETTINGS_KEY, round(float(seconds), 2))


def _assets_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "themes" / "splash"


_ACTIVE: "StartupSplash | None" = None


def pulse() -> None:
    """Odśwież planszę w trakcie długiej pracy w wątku GUI (budowa okna).

    Tylko ``repaint()`` — bez ``processEvents``, więc żadne inne zdarzenia nie wchodzą w środek
    budowy okna. Poza startem (brak aktywnej planszy) nic nie robi.
    """
    splash = _ACTIVE
    if splash is not None and splash.isVisible():
        splash.repaint()


class StartupSplash(QWidget):
    """Rysowany ręcznie ekran startowy (bez arkusza stylów — wygląda tak samo w każdym motywie)."""

    def __init__(
        self,
        icon: QIcon | None = None,
        parent: QWidget | None = None,
        *,
        t0: float | None = None,
        expected_seconds: float | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("startupSplash")
        self.setFixedSize(SPLASH_W, SPLASH_H)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._t0 = t0 if t0 is not None else time.perf_counter()
        expected = expected_seconds if expected_seconds is not None else load_startup_seconds()
        self._expected = max(2.0, min(float(expected), 120.0))
        self._ready = False
        self._status = "Uruchamiam program…"

        from inyfinn_resizer.app.themes import display_font_family, register_fonts, theme_font_family

        register_fonts()
        self._font_title = QFont(display_font_family())
        self._font_title.setPixelSize(34)
        self._font_main = QFont(theme_font_family())
        self._font_main.setPointSizeF(12.5)
        self._font_small = QFont(theme_font_family())
        self._font_small.setPointSizeF(10.5)

        logo = QPixmap(str(_assets_dir() / "logo_white_box.png"))
        self._logo = (
            logo.scaledToWidth(190, Qt.TransformationMode.SmoothTransformation) if not logo.isNull() else None
        )
        if icon is not None:
            self.setWindowIcon(icon)

        self._anim = QTimer(self)
        self._anim.setInterval(FRAME_MS)
        self._anim.timeout.connect(self._tick)
        QTimer.singleShot(MAX_SHOW_MS, self.close)

    # —— stan ——
    def elapsed(self) -> float:
        return time.perf_counter() - self._t0

    def progress(self) -> float:
        """0..1 — jak w launcher.cs: 92% w przewidywanym czasie, potem powoli do 99%."""
        if self._ready:
            return 1.0
        t, e = self.elapsed(), self._expected
        if t <= e:
            return 0.92 * (1 - (1 - t / e) ** 2)
        return 0.92 + 0.07 * (1 - math.exp(-(t - e) / 8))

    def right_text(self) -> str:
        if self._ready:
            return ""
        rest = math.ceil(self._expected - self.elapsed())
        return f"zostało ok. {rest} s" if rest >= 1 else "jeszcze chwilkę…"

    def set_status(self, text: str) -> None:
        """Etapy ładowania — zapamiętane (diagnostyka); na planszy stały napis jak w prezentacjach."""
        self._last_step = text
        self.update()

    def _angle(self) -> float:
        # Kąt z zegara, nie z licznika klatek: po chwilowym zatrzymaniu wątku GUI kółko nie „cofa się”.
        return (self.elapsed() * 300.0) % 360.0

    def _tick(self) -> None:
        self.update()

    # —— Qt ——
    def showEvent(self, event) -> None:  # noqa: N802
        global _ACTIVE
        super().showEvent(event)
        _ACTIVE = self
        self._anim.start()

    def closeEvent(self, event) -> None:  # noqa: N802
        global _ACTIVE
        self._anim.stop()
        if _ACTIVE is self:
            _ACTIVE = None
        super().closeEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        W = self.width()
        p.fillRect(self.rect(), BRAND_GREEN)

        if self._logo is not None:
            p.drawPixmap((W - self._logo.width()) // 2, 34, self._logo)

        p.setPen(QColor("white"))
        p.setFont(self._font_title)
        p.drawText(QRectF(0, 182, W, 48), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   APP_TITLE.upper())

        bx, bw, by, bh = 56, W - 112, 296, 6
        cs, cx, cy = 22, bx, 258

        # kółko ładowania: półprzezroczysty tor + obracający się biały łuk
        ring = QPen(TRACK, 3.0)
        p.setPen(ring)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx, cy, cs, cs))
        arc = QPen(QColor("white"), 3.0)
        arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc)
        p.drawArc(QRectF(cx, cy, cs, cs), int(-self._angle() * 16), int(-100 * 16))

        # napisy
        left = "Gotowe" if self._ready else self._status
        p.setPen(QColor("white"))
        p.setFont(self._font_main)
        p.drawText(QRectF(cx + cs + 12, cy - 4, bw / 2, cs + 8),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, left)
        p.setPen(SOFT_TEXT)
        p.setFont(self._font_small)
        p.drawText(QRectF(bx + bw / 2, cy - 4, bw / 2, cs + 8),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.right_text())

        # pasek postępu
        p.setPen(Qt.PenStyle.NoPen)
        self._round(p, TRACK, bx, by, bw, bh)
        self._round(p, YELLOW, bx, by, max(bh, int(bw * self.progress())), bh)
        p.end()

    @staticmethod
    def _round(p: QPainter, color: QColor, x: float, y: float, w: float, h: float) -> None:
        path = QPainterPath()
        path.addRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
        p.fillPath(path, color)

    def center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(geo.x() + (geo.width() - self.width()) // 2, geo.y() + (geo.height() - self.height()) // 2)

    def finish(self, main_window: QWidget, on_shown=None, *, hold_ms: int = 250) -> None:
        """Pasek na 100% przez ``hold_ms``, potem zamknięcie planszy i główne okno na wierzch.

        Plansza znika w tej samej chwili, w której pojawia się okno — nigdy nie zostaje nad nim.
        """
        self._ready = True
        self.repaint()

        def _show_main() -> None:
            self.close()
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()
            if on_shown is not None:
                on_shown()

        QTimer.singleShot(max(0, hold_ms), _show_main)
