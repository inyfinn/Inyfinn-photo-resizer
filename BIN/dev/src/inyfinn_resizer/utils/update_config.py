"""Stałe auto-update (GitHub Releases — repo publiczne)."""

from __future__ import annotations

GITHUB_OWNER = "inyfinn"
GITHUB_REPO = "Inyfinn-photo-resizer"
RELEASES_LATEST_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
USER_AGENT = "InyfinnPhotoResizer-Updater/1"
ASSET_FILENAME_PREFIX = "InyfinnPhotoResizer-v"
ASSET_FILENAME_SUFFIX = ".zip"
MAX_CACHED_PACKAGES = 2
CHECK_INTERVAL_SEC = 6 * 3600
DOWNLOAD_CHUNK_BYTES = 1024 * 256
