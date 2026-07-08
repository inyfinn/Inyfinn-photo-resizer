"""Przewodnik użytkownika — Pomoc w menu aplikacji."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from inyfinn_resizer import __version__
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons


def _help_html() -> str:
    return f"""
<p><b>Inyfinn Photo Resizer {__version__}</b> — wsadowa konwersja i kompresja zdjęć.<br>
Przeciągnij pliki na listę, ustaw format, kliknij <b>Konwertuj</b>.</p>

<h3>Lista plików</h3>
<ul>
<li><b>Dodaj pliki / folder</b> — kolejka po lewej</li>
<li><b>Przeciągnij i upuść</b> na listę</li>
<li><b>Sortuj</b> — nazwa lub rozmiar</li>
<li><b>Podgląd</b> — w sekcji „Więcej”</li>
</ul>

<h3>Format</h3>
<ul>
<li>WebP, JPG, PNG, AVIF, GIF — jeden lub wiele naraz</li>
<li><b>Ustawienia…</b> — metadane, progresywny JPG</li>
<li><b>Segreguj</b> — podfoldery webp/, jpg/ przy wielu formatach</li>
<li><b>Sekwencja wizek</b> — XL/L/S/SKLEP in-place</li>
</ul>

<h3>Kompresja</h3>
<ul>
<li><b>Jakość</b> — JPG, WebP, AVIF</li>
<li><b>Kolory PNG</b> — paleta 32–256; <b>Z jakości</b> = auto</li>
<li>Program wykrywa rzadkie akcenty (np. zieleń) i zwiększa paletę</li>
</ul>

<h3>Rozmiar i zapis</h3>
<ul>
<li><b>Preset rozmiaru</b> — szybkie skalowanie</li>
<li><b>Wyjście</b> — folder docelowy (pomijany przy wizek)</li>
</ul>

<h3>Zaawansowane</h3>
<ul>
<li>Skalowanie według boku, filtr Lanczos</li>
<li>Obrót, odbicia, autoobrót EXIF</li>
<li>Czarno-biały, sepia</li>
</ul>

<h3>Zmiana nazw</h3>
<p>Szablon <code>{{name}}_{{counter:04d}}</code> — zakładka <b>Zmiana nazw</b>.</p>

<h3>Menu</h3>
<ul>
<li><b>Plik</b> — preset JSON, wyjście</li>
<li><b>Narzędzia</b> — motyw, ustawienia</li>
<li><b>Pomoc</b> — ten przewodnik</li>
</ul>

<p><i>pngquant, gifsicle, libvips działają w tle podczas konwersji.</i></p>
"""


class HelpGuideDialog(AppDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pomoc — Inyfinn Photo Resizer")
        self.setMinimumSize(520, 480)
        self.resize(560, 520)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Przewodnik użytkownika")
        title.setObjectName("helpGuideTitle")
        header.addWidget(title)
        header.addStretch()
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("helpGuideVersion")
        header.addWidget(ver)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setObjectName("helpGuideScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("helpGuideBody")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(4, 0, 8, 8)

        content = QLabel(_help_html())
        content.setObjectName("helpGuideContent")
        content.setWordWrap(True)
        content.setTextFormat(Qt.RichText)
        content.setOpenExternalLinks(True)
        body_lay.addWidget(content)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        polish_dialog_buttons(buttons)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)
        root.addWidget(buttons)


def show_help_guide(parent=None) -> None:
    HelpGuideDialog(parent).exec()
