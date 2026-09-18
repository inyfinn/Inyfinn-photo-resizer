"""Modele BiRefNet do usuwania tła — pobierane przy pierwszym użyciu (od 2.4.8).

Paczka nie zawiera modeli (1,1 GB), więc instalator ma ~200 MB. Pliki trafiają do
%LOCALAPPDATA%\\Inyfinn\\PhotoResizer\\rmbg pod nazwami, których szuka rembg
(U2NET_HOME/<model>.onnx), i są sprawdzane SHA256.

Pliki BiRefNet-*.onnx z BIN/dev/tools/rmbg miały poprawny rozmiar, ale inną treść
niż oficjalne wydanie — rembg po cichu pobierał wtedy 1 GB przy pierwszym użyciu.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from inyfinn_resizer.utils.paths import rmbg_models_dir

_BASE_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0"
_USER_AGENT = "InyfinnPhotoResizer-Models/1"
_CHUNK_BYTES = 1024 * 1024
_HASH_LOCK = threading.Lock()


@dataclass(frozen=True)
class ModelSpec:
    name: str  # nazwa sesji rembg
    label: str
    url: str
    filename: str  # rembg szuka f"{name}.onnx" w U2NET_HOME
    size: int
    sha256: str

    @property
    def size_mb(self) -> int:
        return round(self.size / (1024 * 1024))


MODELS: dict[str, ModelSpec] = {
    "birefnet-general-lite": ModelSpec(
        name="birefnet-general-lite",
        label="Szybko",
        url=f"{_BASE_URL}/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
        filename="birefnet-general-lite.onnx",
        size=224_005_088,
        sha256="5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333",
    ),
    "birefnet-general": ModelSpec(
        name="birefnet-general",
        label="Najlepsza jakość",
        url=f"{_BASE_URL}/BiRefNet-general-epoch_244.onnx",
        filename="birefnet-general.onnx",
        size=972_666_916,
        sha256="58f621f00f5d756097615970a88a791584600dcf7c45b18a0a6267535a1ebd3c",
    ),
}


class ModelDownloadCancelled(Exception):
    """Użytkownik przerwał pobieranie — plik .part zostaje do wznowienia."""


def user_models_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Inyfinn" / "PhotoResizer" / "rmbg"


def _candidate_dirs() -> list[Path]:
    # Najpierw katalog użytkownika; potem paczka/dev (starsze instalacje miały modele w _internal).
    out: list[Path] = []
    for folder in (user_models_dir(), rmbg_models_dir()):
        if folder not in out:
            out.append(folder)
    return out


def _cache_path() -> Path:
    return user_models_dir() / "verified.json"


def _load_cache() -> dict:
    try:
        data = json.loads(_cache_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_cache(data: dict) -> None:
    try:
        _cache_path().parent.mkdir(parents=True, exist_ok=True)
        _cache_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stamp(path: Path) -> list:
    st = path.stat()
    return [st.st_size, st.st_mtime_ns]


def _file_ok(path: Path, spec: ModelSpec) -> bool:
    """Rozmiar zawsze; SHA256 raz na plik (wynik w verified.json)."""
    try:
        if not path.is_file() or path.stat().st_size != spec.size:
            return False
        key = str(path.resolve()).lower()
        with _HASH_LOCK:
            cache = _load_cache()
            entry = cache.get(key)
            if entry == [*_stamp(path), spec.sha256]:
                return True
            if _sha256(path) != spec.sha256:
                return False
            cache[key] = [*_stamp(path), spec.sha256]
            _save_cache(cache)
        return True
    except OSError:
        return False


def get_spec(model_name: str) -> ModelSpec:
    spec = MODELS.get(model_name)
    if spec is None:
        raise ValueError(f"Nieobsługiwany model: {model_name}")
    return spec


def find_model(model_name: str) -> Path | None:
    spec = get_spec(model_name)
    for folder in _candidate_dirs():
        candidate = folder / spec.filename
        if _file_ok(candidate, spec):
            return candidate
    return None


def is_ready(model_name: str) -> bool:
    return model_name in MODELS and find_model(model_name) is not None


def download_model(
    model_name: str,
    *,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Path:
    """Pobiera model do katalogu użytkownika (wznawia .part), weryfikuje SHA256."""
    spec = get_spec(model_name)
    folder = user_models_dir()
    folder.mkdir(parents=True, exist_ok=True)
    final_path = folder / spec.filename
    if _file_ok(final_path, spec):
        return final_path

    part_path = folder / (spec.filename + ".part")
    existing = part_path.stat().st_size if part_path.is_file() else 0
    if existing > spec.size:
        part_path.unlink(missing_ok=True)
        existing = 0

    if existing < spec.size:
        headers = {"User-Agent": _USER_AGENT}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        req = urllib.request.Request(spec.url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            if existing and getattr(resp, "status", 200) != 206:
                # Serwer zignorował Range — zaczynamy od zera.
                existing = 0
            received = existing
            if progress:
                progress(received, spec.size)
            with part_path.open("ab" if existing else "wb") as handle:
                while True:
                    if cancelled and cancelled():
                        raise ModelDownloadCancelled()
                    chunk = resp.read(_CHUNK_BYTES)
                    if not chunk:
                        break
                    handle.write(chunk)
                    received += len(chunk)
                    if progress:
                        progress(received, spec.size)

    size = part_path.stat().st_size
    if size != spec.size:
        raise OSError(
            f"Niepełny model {spec.label}: {size} B z {spec.size} B — spróbuj ponownie."
        )
    if _sha256(part_path) != spec.sha256:
        part_path.unlink(missing_ok=True)
        raise OSError(
            f"Model {spec.label} ma złą sumę kontrolną (uszkodzone pobieranie) — spróbuj ponownie."
        )
    os.replace(part_path, final_path)
    if not _file_ok(final_path, spec):
        raise OSError(f"Nie udało się zapisać modelu {spec.label} w {folder}")
    return final_path
