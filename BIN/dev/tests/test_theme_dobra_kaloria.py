"""Wygląd Dobra Kaloria (2.6.1): styl kolorów × tryb, migracja ustawień, czcionki i typografia."""

from __future__ import annotations

import re

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel

from inyfinn_resizer.app import themes, user_settings
from inyfinn_resizer.app.themes import typography

ZJ = "dobra-kaloria-zielen-jasny"
ZC = "dobra-kaloria-zielen-ciemny"
KJ = "dobra-kaloria-krem-jasny"
KC = "dobra-kaloria-krem-ciemny"
ALL = (ZJ, ZC, KJ, KC)
INDIGO = ("#6366F1", "#818CF8", "#4F46E5", "#7C3AED")


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


def test_two_styles_times_two_modes():
    assert themes.STYLES == ("zielen", "krem")
    assert themes.MODES == ("jasny", "ciemny")
    assert set(themes.THEMES) == set(ALL)
    assert themes.DEFAULT_THEME == ZJ
    assert themes.STYLE_LABELS == {"zielen": "Dobra Kaloria 1 · zieleń", "krem": "Dobra Kaloria 2 · krem"}
    assert themes.split_theme(KC) == ("krem", "ciemny")
    assert themes.theme_id("zielen", "ciemny") == ZC


def test_every_theme_defines_every_token_used_by_qss():
    qss = (themes.Path(themes.__file__).parent / "app.qss").read_text(encoding="utf-8")
    used = set(re.findall(r"@[A-Z_]+@", qss)) - {"@CHECK_ICON@", "@COMBO_ARROW@"}
    keys = [set(t) for t in themes._THEME_TOKENS.values()]
    assert all(k == keys[0] for k in keys)
    assert used <= keys[0], sorted(used - keys[0])


@pytest.mark.parametrize("theme", ALL)
def test_rendered_qss_is_complete_and_never_indigo(app, theme):
    qss = themes.render_qss(theme)
    assert re.findall(r"@[A-Z_]+@", qss) == []
    assert not any(c in qss.upper() for c in INDIGO)
    style, mode = themes.split_theme(theme)
    assert f"check-{style}-{mode}.png" in qss
    assert f"combo-down-{style}-{mode}.png" in qss


@pytest.mark.parametrize(
    "theme, window, accent, on_accent",
    [
        # Tło okna = poziom L0 drabiny design systemu 1.5.0 (jasne: biała kartka programu).
        (ZJ, "#FFFFFF", "#0F763E", "#FFFFFF"),
        (ZC, "#0F2315", "#A2D686", "#0F190C"),
        (KJ, "#FFFFFF", "#0F763E", "#FFFFFF"),
        (KC, "#120F0A", "#4CC46A", "#1C1812"),
    ],
)
def test_values_from_design_system(theme, window, accent, on_accent):
    t = themes._THEME_TOKENS[theme]
    assert (t["@BG_WINDOW@"], t["@ACCENT@"], t["@ON_ACCENT@"]) == (window, accent, on_accent)
    assert (t["@CTA_BG@"], t["@CTA_TEXT@"]) == ("#FFD42A", "#3B2A20")
    assert (t["@RADIUS_BTN@"], t["@RADIUS_FIELD@"], t["@RADIUS_CARD@"]) == ("4px", "8px", "12px")


@pytest.mark.parametrize(
    "value, expected",
    [("dark", ZC), ("dobra-kaloria-ciemny", ZC), ("dobra-kaloria", KJ), ("dobra-kaloria-krem", KC),
     ("light", ZJ), ("neon", ZJ), ("", ZJ), (None, ZJ), (KC, KC)],
)
def test_resolve_theme(value, expected):
    assert themes.resolve_theme(value) == expected


def test_fonts_bundled_and_applied(app):
    for name in ("Lato-Regular.ttf", "Lato-Bold.ttf", "Mindset.otf"):
        assert (themes.fonts_dir() / name).is_file()
    assert {"Lato", "Mindset"} <= themes.register_fonts()
    for theme in ALL:
        themes.apply_theme(app, theme)
        assert app.font().family() == "Lato"
        assert themes.current_theme() == theme
    assert themes.display_font_family() == "Mindset"


def test_headings_uppercase_mindset_and_eyebrows(app):
    themes.apply_theme(app, ZJ)
    title = QLabel("Lista plików")
    title.setObjectName("panelTitle")
    eyebrow = QLabel("Zmiana rozmiaru")
    eyebrow.setObjectName("sectionTitle")
    plain = QLabel("Zwykły tekst")
    for lbl in (title, eyebrow, plain):
        typography.styled_font(lbl)
    assert title.font().family() == "Mindset"
    assert title.font().capitalization() == QFont.Capitalization.AllUppercase
    assert title.text() == "Lista plików"  # napis bez zmian, tylko sposób rysowania
    assert eyebrow.font().capitalization() == QFont.Capitalization.AllUppercase
    assert eyebrow.font().letterSpacing() == pytest.approx(typography.EYEBROW_LETTER_SPACING)
    assert plain.font().capitalization() != QFont.Capitalization.AllUppercase
    # Po zmianie motywu wersaliki i krój zostają.
    themes.apply_theme(app, KC)
    app.processEvents()
    assert title.font().family() == "Mindset"
    assert title.font().capitalization() == QFont.Capitalization.AllUppercase


def test_fresh_install_is_zielen_jasny(ini_settings):
    assert user_settings.load_theme() == ZJ
    s = ini_settings()
    assert (s.value(user_settings.THEME_STYLE_KEY), s.value(user_settings.THEME_MODE_KEY)) == ("zielen", "jasny")


@pytest.mark.parametrize(
    "saved, expected",
    [("dark", ZC), ("dobra-kaloria-ciemny", ZC), ("dobra-kaloria", KJ), ("light", ZJ), ("", ZJ)],
)
def test_migration_keeps_what_user_sees(ini_settings, saved, expected):
    s = ini_settings()
    s.setValue(user_settings.LEGACY_THEME_KEY, saved)
    s.setValue("ui/theme_migrated_dobra_kaloria", True)
    s.setValue("ui/theme_migrated_dk2", True)
    s.setValue("ui/theme_last_light", "light")
    s.sync()
    assert user_settings.load_theme() == expected
    after = ini_settings()
    for key in ("ui/theme", "ui/theme_migrated_dobra_kaloria", "ui/theme_migrated_dk2", "ui/theme_last_light"):
        assert after.value(key) is None, key
    assert str(after.value(user_settings.THEME_MIGRATION_KEY)).lower() == "true"


def test_style_and_mode_are_independent(ini_settings):
    user_settings.load_theme()
    user_settings.save_theme(KC)
    assert user_settings.load_theme() == KC
    s = ini_settings()
    assert (s.value(user_settings.THEME_STYLE_KEY), s.value(user_settings.THEME_MODE_KEY)) == ("krem", "ciemny")
    user_settings.save_theme(themes.theme_id("krem", "jasny"))
    assert user_settings.load_theme() == KJ


def test_garbage_in_settings_falls_back(ini_settings):
    user_settings.load_theme()
    s = ini_settings()
    s.setValue(user_settings.THEME_STYLE_KEY, "indygo")
    s.setValue(user_settings.THEME_MODE_KEY, "dark")
    assert user_settings.load_theme() == ZJ
