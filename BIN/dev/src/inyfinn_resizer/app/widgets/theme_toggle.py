"""Przełącznik jasny / ciemny motyw: zwykły przełącznik DS z napisem „Ciemny motyw” (włączony = ciemny).

2.6.10: wcześniej osobny suwak ze słońcem i księżycem na gałce (promienie słońca wychodziły poza gałkę). Teraz ten sam
przełącznik co w „Opcjach zaawansowanych” (``SwitchBox``). Styl kolorów (zieleń / krem) wybiera menu Narzędzia → Styl
kolorów; przełącznik go nie zmienia.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from inyfinn_resizer.app.widgets.switch import SwitchBox

TOGGLE_TOOLTIP = "Tryb jasny lub ciemny (styl kolorów: Narzędzia → Styl kolorów)"
TOGGLE_LABEL = "Ciemny motyw"


class ThemeToggle(SwitchBox):
    """``toggled(bool)``: True = ciemny motyw."""

    def __init__(self, *, dark: bool = False, parent: QWidget | None = None) -> None:
        super().__init__((TOGGLE_LABEL, TOGGLE_LABEL), parent)
        self.setChecked(dark)
        self.setToolTip(TOGGLE_TOOLTIP)

    def is_dark(self) -> bool:
        return self.isChecked()

    def set_dark(self, dark: bool) -> None:
        self.setChecked(dark)
