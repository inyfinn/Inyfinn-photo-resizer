"""Cache pobranych pakietów aktualizacji (max 2 wersje na dysku)."""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from inyfinn_resizer.utils.update_config import MAX_CACHED_PACKAGES


@dataclass
class CachedPackage:
    version: str
    zip_path: str
    size: int
    downloaded_at: float

    @property
    def path(self) -> Path:
        return Path(self.zip_path)


def updates_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    folder = Path(base) / "updates"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def manifest_path() -> Path:
    return updates_dir() / "manifest.json"


def _load_manifest() -> dict:
    path = manifest_path()
    if not path.is_file():
        return {"packages": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"packages": []}
    if not isinstance(data, dict):
        return {"packages": []}
    data.setdefault("packages", [])
    return data


def _save_manifest(data: dict) -> None:
    manifest_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_packages() -> list[CachedPackage]:
    raw = _load_manifest().get("packages", [])
    out: list[CachedPackage] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            pkg = CachedPackage(
                version=str(item["version"]),
                zip_path=str(item["zip_path"]),
                size=int(item["size"]),
                downloaded_at=float(item.get("downloaded_at", 0)),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if pkg.path.is_file() and pkg.path.stat().st_size == pkg.size:
            out.append(pkg)
    return out


def package_dir(version: str) -> Path:
    safe = version.replace("/", "_").replace("\\", "_")
    return updates_dir() / safe


def zip_path_for(version: str) -> Path:
    return package_dir(version) / f"InyfinnPhotoResizer-v{version}.zip"


def part_path_for(version: str) -> Path:
    return zip_path_for(version).with_suffix(zip_path_for(version).suffix + ".part")


def find_cached(version: str, expected_size: int | None = None) -> CachedPackage | None:
    for pkg in list_packages():
        if pkg.version != version:
            continue
        if expected_size is not None and pkg.size != expected_size:
            continue
        return pkg
    return None


def _write_manifest_packages(packages: list[CachedPackage]) -> None:
    data = _load_manifest()
    data["packages"] = [asdict(p) for p in packages]
    _save_manifest(data)


def _remove_package_folder(path: Path) -> None:
    folder = path.parent
    if folder.is_dir() and folder.parent == updates_dir():
        shutil.rmtree(folder, ignore_errors=True)


def _enforce_limit(before_add_version: str | None = None) -> None:
    packages = list_packages()
    if before_add_version:
        packages = [p for p in packages if p.version != before_add_version]
    while len(packages) >= MAX_CACHED_PACKAGES:
        oldest = min(packages, key=lambda p: p.downloaded_at)
        _remove_package_folder(oldest.path)
        packages.remove(oldest)
    _write_manifest_packages(packages)


def register_download(version: str, final_zip: Path, size: int) -> CachedPackage:
    _enforce_limit(before_add_version=version)
    folder = package_dir(version)
    folder.mkdir(parents=True, exist_ok=True)
    target = zip_path_for(version)
    if final_zip.resolve() != target.resolve():
        if target.is_file():
            target.unlink()
        final_zip.replace(target)
    part = part_path_for(version)
    if part.is_file():
        part.unlink(missing_ok=True)

    pkg = CachedPackage(
        version=version,
        zip_path=str(target),
        size=size,
        downloaded_at=time.time(),
    )
    packages = [p for p in list_packages() if p.version != version]
    packages.append(pkg)
    packages.sort(key=lambda p: p.downloaded_at)
    while len(packages) > MAX_CACHED_PACKAGES:
        drop = packages.pop(0)
        _remove_package_folder(drop.path)
    _write_manifest_packages(packages)
    return pkg


def remove_package(version: str) -> None:
    packages = list_packages()
    kept: list[CachedPackage] = []
    for pkg in packages:
        if pkg.version == version:
            _remove_package_folder(pkg.path)
        else:
            kept.append(pkg)
    _write_manifest_packages(kept)


def cleanup_orphans() -> None:
    """Usuwa foldery w updates/ spoza manifestu i wpisy z brakującymi plikami."""
    packages = list_packages()
    _write_manifest_packages(packages)
    root = updates_dir()
    known = {package_dir(p.version) for p in packages}
    for child in root.iterdir():
        if child.name == "manifest.json":
            continue
        if child.is_dir() and child not in known:
            shutil.rmtree(child, ignore_errors=True)
