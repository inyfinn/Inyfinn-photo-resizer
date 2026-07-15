"""Pobieranie informacji o release z GitHub API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from inyfinn_resizer.utils.update_config import (
    ASSET_PREFIX,
    ASSET_SUFFIX,
    RELEASES_LATEST_URL,
    USER_AGENT,
)
from inyfinn_resizer.utils.version_compare import normalize_version


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    download_url: str
    asset_name: str
    size: int


def _github_request(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_latest_release() -> ReleaseInfo:
    data = _github_request(RELEASES_LATEST_URL)
    tag = str(data.get("tag_name", "")).strip()
    if not tag:
        raise ValueError("Brak tag_name w odpowiedzi GitHub")

    version = normalize_version(tag)
    assets = data.get("assets") or []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", ""))
        if not name.startswith(ASSET_PREFIX) or not name.endswith(ASSET_SUFFIX):
            continue
        url = str(asset.get("browser_download_url", ""))
        if not url:
            continue
        size = int(asset.get("size") or 0)
        return ReleaseInfo(
            version=version,
            tag=tag,
            download_url=url,
            asset_name=name,
            size=size,
        )

    expected = f"{ASSET_PREFIX}{version}{ASSET_SUFFIX}"
    raise ValueError(f"Brak assetu {expected} w najnowszym release")
