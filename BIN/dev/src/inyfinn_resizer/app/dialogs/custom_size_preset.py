"""Dialog zapisu własnego presetu wymiarów (resize + crop jak FastStone)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from inyfinn_resizer.app.dialogs.advanced_options import AdvancedSettingsPanel
from inyfinn_resizer.app.dialogs.base_dialog import AppDialog, polish_dialog_buttons
from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions


class CustomSizePresetDialog(AppDialog):
    """Nazwa + pełne ustawienia skalowania i kadrowania."""

    def __init__(
        self,
        resize: ResizeOptions,
        transforms: TransformOptions,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Zapisz własny preset wymiarów")
        self.setMinimumSize(580, 820)
        self.resize(580, 820)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 12, 14, 12)

        intro = QLabel(
            "Podaj nazwę i ustaw skalowanie lub kadrowanie. "
            "Proporcje obrazu są zawsze zachowane przy skalowaniu według boku."
        )
        intro.setWordWrap(True)
        intro.setObjectName("helpGuideIntro")
        layout.addWidget(intro)

        name_row = QHBoxLayout()
        name_lbl = QLabel("Nazwa presetu:")
        name_lbl.setObjectName("fieldLabel")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. Sklep 1200 px długi bok")
        self.name_edit.setMinimumHeight(32)
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_edit, stretch=1)
        layout.addLayout(name_row)

        if resize.mode == ResizeMode.NONE:
            resize = ResizeOptions(
                mode=ResizeMode.ONE_SIDE,
                side="longer",
                dimension=1200,
            )

        self._panel = AdvancedSettingsPanel(resize, transforms, self, scroll=False)
        layout.addWidget(self._panel, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        polish_dialog_buttons(buttons)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        if not self._panel.resize_enable.isChecked() and not self._panel.crop_enable.isChecked():
            self._panel.resize_enable.setChecked(True)
        self.accept()

    def preset_name(self) -> str:
        return self.name_edit.text().strip()

    def get_resize(self) -> ResizeOptions:
        return self._panel.get_resize()

    def get_transforms(self) -> TransformOptions:
        return self._panel.get_transforms()
