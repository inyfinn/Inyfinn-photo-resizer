"""Testy cache aktualizacji (max 2 pakiety)."""

from __future__ import annotations

from pathlib import Path

import inyfinn_resizer.utils.update_cache as cache


def test_register_keeps_max_two_packages(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cache, "updates_dir", lambda: tmp_path)

    def _make(version: str) -> None:
        folder = tmp_path / version
        folder.mkdir(parents=True, exist_ok=True)
        z = folder / f"InyfinnPhotoResizer-v{version}.zip"
        z.write_bytes(b"x" * 10)
        cache.register_download(version, z, 10)

    _make("1.0.58")
    _make("1.0.59")
    assert len(cache.list_packages()) == 2
    assert (tmp_path / "1.0.58").is_dir()
    assert (tmp_path / "1.0.59").is_dir()

    _make("1.0.60")
    versions = {p.version for p in cache.list_packages()}
    assert versions == {"1.0.59", "1.0.60"}
    assert not (tmp_path / "1.0.58").exists()


def test_find_cached_skips_redownload(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cache, "updates_dir", lambda: tmp_path)
    folder = tmp_path / "1.0.60"
    folder.mkdir(parents=True)
    z = folder / "InyfinnPhotoResizer-v1.0.60.zip"
    z.write_bytes(b"1234567890")
    cache.register_download("1.0.60", z, 10)
    found = cache.find_cached("1.0.60", 10)
    assert found is not None
    assert found.path == z
