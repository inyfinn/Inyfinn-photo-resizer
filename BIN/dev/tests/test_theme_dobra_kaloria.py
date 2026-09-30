"""Motyw Dobra Kaloria (2.6.0): domyślny, migracja z „light”, komplet znaczników, czcionka w paczce."""

from __future__ import annotations

import re

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from inyfinn_resizer.app import themes, user_settings


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def ini_settings(tmp_path, monkeypatch):
    """Ustawienia w pliku tymczasowym — test nie dotyka rejestru użytkownika."""
    path = tmp_path / "settings.ini"
    monkeypatch.setattr(
        user_settings, "_settings", lambda: QSettings(str(path), QSettings.Format.IniFormat)
    )
    return lambda: QSettings(str(path), QSettings.Format.IniFormat)


def test_default_theme_is_dobra_kaloria():
    assert themes.DEFAULT_THEME == "dobra-kaloria"
    assert set(themes.THEMES) == {"dobra-kaloria", "light", "dark"}
    assert set(themes.THEME_LABELS) == set(themes.THEMES)


def test_every_theme_defines_every_token():
    keys = [set(t) for t in themes._THEME_TOKENS.values()]
    assert all(k == keys[0] for k in keys)


@pytest.mark.parametrize("theme", ["dobra-kaloria", "light", "dark"])
def test_rendered_qss_has_no_placeholders(app, theme):
    qss = themes.render_qss(theme)
    assert re.findall(r"@[A-Z_]+@", qss) == []


def test_light_and_dark_keep_indigo_cta_and_classic_shape():
    for theme in ("light", "dark"):
        t = themes._THEME_TOKENS[theme]
        assert t["@CTA_BG@"] == t["@ACCENT@"]
        assert t["@CTA_TEXT@"].lower() == "#ffffff"
        assert t["@RADIUS_BTN@"] == "10px"
        assert "Segoe UI" in t["@FONT_FAMILY@"]


def test_dobra_kaloria_values():
    t = themes._THEME_TOKENS["dobra-kaloria"]
    assert t["@CTA_BG@"] == "#FFD42A"
    assert t["@CTA_TEXT@"] == "#3B2A20"
    assert t["@FG_TEXT@"] == "#3B2A20"
    assert (t["@RADIUS_BTN@"], t["@RADIUS_FIELD@"], t["@RADIUS_CARD@"]) == ("4px", "8px", "12px")


def test_icons_for_light_family_are_not_dark(app):
    for theme in ("dobra-kaloria", "light"):
        qss = themes.render_qss(theme)
        assert "check-dark.png" not in qss
        assert "combo-down-dark.png" not in qss
    assert "check-dk.png" in themes.render_qss("dobra-kaloria")


def test_lato_is_bundled_and_applied(app):
    assert (themes.fonts_dir() / "Lato-Regular.ttf").is_file()
    assert (themes.fonts_dir() / "Lato-Bold.ttf").is_file()
    assert "Lato" in themes.register_fonts()
    themes.apply_theme(app, "dobra-kaloria")
    assert app.font().family() == "Lato"
    themes.apply_theme(app, "light")
    assert app.font().family() == "Segoe UI"


def test_fresh_install_gets_dobra_kaloria(ini_settings):
    assert user_settings.load_theme() == "dobra-kaloria"
    assert ini_settings().value(user_settings.THEME_KEY) == "dobra-kaloria"


def test_old_default_light_migrates_once(ini_settings):
    ini_settings().setValue(user_settings.THEME_KEY, "light")
    assert user_settings.load_theme() == "dobra-kaloria"
    # Świadomy wybór jasnego po migracji zostaje.
    user_settings.save_theme("light")
    assert user_settings.load_theme() == "light"
    assert user_settings.load_theme() == "light"


def test_saved_dark_stays_dark(ini_settings):
    ini_settings().setValue(user_settings.THEME_KEY, "dark")
    assert user_settings.load_theme() == "dark"


def test_unknown_value_falls_back_to_default(ini_settings):
    s = ini_settings()
    s.setValue(user_settings.THEME_MIGRATION_KEY, True)
    s.setValue(user_settings.THEME_KEY, "neon")
    assert user_settings.load_theme() == "dobra-kaloria"


def test_toggle_returns_to_last_light_theme(ini_settings):
    assert user_settings.load_last_light_theme() == "dobra-kaloria"
    user_settings.save_theme("light")
    user_settings.save_theme("dark")
    assert user_settings.load_last_light_theme() == "light"
    user_settings.save_theme("dobra-kaloria")
    assert user_settings.load_last_light_theme() == "dobra-kaloria"
