"""Wspólne ustawienia testów.

Testy NIE mogą czytać ani zapisywać prawdziwych ustawień programu w rejestrze (HKCU\\Software\\Inyfinn\\PhotoResizer).
Do 2.6.4 część testów budowała ``MainWindow`` na prawdziwym rejestrze; w 2.6.5 doszło zapamiętywanie rozmiaru okna
ustawionego ręcznie (``ui/window_size_<tryb>``) i test, który zmieniał rozmiar okna i tryb, zapisał tam 1280×920 —
program na tej stacji otwierałby się potem w rozmiarze z testu, a nie dopasowanym do ekranu.

Każdy test dostaje własny, pusty plik INI. Test, który sam podmienia ``_settings`` (monkeypatch), nadal to robi —
jego podmiana jest późniejsza i wygrywa.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings


@pytest.fixture(autouse=True)
def _isolated_app_settings(tmp_path_factory, monkeypatch):
    from inyfinn_resizer.app import user_settings
    from inyfinn_resizer.app.widgets import startup_splash
    from inyfinn_resizer.core import size_presets

    path = tmp_path_factory.mktemp("ustawienia") / "settings.ini"

    def _settings() -> QSettings:
        return QSettings(str(path), QSettings.Format.IniFormat)

    for module in (user_settings, startup_splash, size_presets):
        monkeypatch.setattr(module, "_settings", _settings)
    yield path
