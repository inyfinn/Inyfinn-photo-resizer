"""Tests for wiz sequence helpers."""

from __future__ import annotations

from pathlib import Path

from inyfinn_resizer.core.wiz_sequence import (
    discover_wiz_folders,
    profile_for_name,
    stem_base,
    ui_quality_to_wiz_slider,
)


def test_stem_base():
    assert stem_base("DK-BAT-FRONT-L.png") == "DK-BAT-FRONT"
    assert stem_base("DK-BAT-FRONT-S-SKLEP.png") == "DK-BAT-FRONT"


def test_profile_for_name():
    assert profile_for_name("x-XL.png") == "xl"
    assert profile_for_name("x-S-SKLEP.jpg") == "sklep"
    assert profile_for_name("x-L.png") == "standard"


def test_ui_quality_to_wiz_slider():
    assert ui_quality_to_wiz_slider(85) == 8
    assert ui_quality_to_wiz_slider(50) == 5


def test_discover_wiz_folders(tmp_path: Path):
    folder = tmp_path / "wiz"
    folder.mkdir()
    img = folder / "test.png"
    img.write_bytes(b"x")
    found = discover_wiz_folders([folder])
    assert folder.resolve() in found
    found2 = discover_wiz_folders([img])
    assert folder.resolve() in found2
