"""Wybór paczki aktualizacji z odpowiedzi GitHub Releases (bez sieci)."""

from __future__ import annotations

import pytest

from inyfinn_resizer.utils import update_release as ur

SHA = "a" * 64


def _release(assets: list[dict], tag: str = "v2.4.9") -> dict:
    return {"tag_name": tag, "assets": assets}


def _asset(name: str, *, digest: str | None = f"sha256:{SHA}") -> dict:
    out = {
        "name": name,
        "size": 1234,
        "browser_download_url": f"https://github.com/inyfinn/Inyfinn-photo-resizer/releases/download/v2.4.9/{name}",
    }
    if digest is not None:
        out["digest"] = digest
    return out


def test_picks_zip_matching_tag_version_with_sha(monkeypatch) -> None:
    data = _release([
        _asset("InyfinnPhotoResizer-2.4.9-setup.exe"),
        _asset("InyfinnPhotoResizer-v2.4.9.zip"),
    ])
    monkeypatch.setattr(ur, "_fetch_json", lambda url: data)
    info = ur.fetch_latest_release()
    assert info.version == "2.4.9"
    assert info.download_url.endswith("InyfinnPhotoResizer-v2.4.9.zip")
    assert info.size == 1234
    assert info.sha256 == SHA


def test_ignores_zip_of_other_version(monkeypatch) -> None:
    data = _release([_asset("InyfinnPhotoResizer-v2.4.2.zip")])
    monkeypatch.setattr(ur, "_fetch_json", lambda url: data)
    with pytest.raises(ValueError):
        ur.fetch_latest_release()


def test_missing_digest_leaves_sha_empty(monkeypatch) -> None:
    data = _release([_asset("InyfinnPhotoResizer-v2.4.9.zip", digest=None)])
    monkeypatch.setattr(ur, "_fetch_json", lambda url: data)
    assert ur.fetch_latest_release().sha256 == ""
