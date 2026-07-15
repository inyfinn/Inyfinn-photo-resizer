"""Testy porównywania wersji."""

from inyfinn_resizer.utils.version_compare import is_newer, normalize_version, version_tuple


def test_normalize_version_strips_v():
    assert normalize_version("v1.0.60") == "1.0.60"


def test_is_newer():
    assert is_newer("1.0.60", "1.0.59")
    assert not is_newer("1.0.59", "1.0.60")
    assert not is_newer("1.0.59", "1.0.59")


def test_version_tuple():
    assert version_tuple("1.0.59") == (1, 0, 59)
