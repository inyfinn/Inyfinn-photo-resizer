"""Usuwanie tła — rembg + BiRefNet (ONNX, DirectML na Windows)."""

from __future__ import annotations

import os
import shutil
import threading
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import TYPE_CHECKING

from inyfinn_resizer.utils.paths import bootstrap_runtime_paths, rmbg_models_dir

if TYPE_CHECKING:
    from PIL import Image

_SESSIONS: dict[str, object] = {}
_SESSION_PROVIDERS: dict[str, list[str]] = {}
_SESSION_LOCK = threading.Lock()
_ALPHA_MATTING_READY: bool | None = None

SUPPORTED_MODELS = ("birefnet-general-lite", "birefnet-general")

_MODEL_FILES = {
    "birefnet-general-lite": "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
    "birefnet-general": "BiRefNet-general-epoch_244.onnx",
}

_REMBG_SESSION_ALIASES = {
    "birefnet-general-lite": "birefnet-general-lite.onnx",
    "birefnet-general": "birefnet-general.onnx",
}


def _ensure_model_home() -> Path:
    models = rmbg_models_dir()
    models.mkdir(parents=True, exist_ok=True)
    os.environ["U2NET_HOME"] = str(models)
    for model_name, source_name in _MODEL_FILES.items():
        source = models / source_name
        alias = models / _REMBG_SESSION_ALIASES[model_name]
        if source.is_file() and not alias.is_file():
            try:
                os.link(source, alias)
            except OSError:
                shutil.copy2(source, alias)
    return models


def _onnx_providers(*, prefer_gpu: bool = True) -> list[str]:
    try:
        import onnxruntime as ort

        available = set(ort.get_available_providers())
        if prefer_gpu and "DmlExecutionProvider" in available:
            return ["DmlExecutionProvider", "CPUExecutionProvider"]
        if prefer_gpu and "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]
    except Exception:
        return ["CPUExecutionProvider"]


def _is_onnx_provider_error(exc: BaseException) -> bool:
    if isinstance(exc, UnicodeDecodeError):
        return True
    msg = str(exc).lower()
    return any(
        token in msg
        for token in ("onnxruntime", "dmlfused", "dmlexecution", "runtime_exception")
    )


def _clear_session(model_name: str) -> None:
    _SESSIONS.pop(model_name, None)
    _SESSION_PROVIDERS.pop(model_name, None)


def alpha_matting_available() -> bool:
    """Alpha matting wymaga pymatting + metadanych pakietu (PyInstaller)."""
    global _ALPHA_MATTING_READY
    if _ALPHA_MATTING_READY is not None:
        return _ALPHA_MATTING_READY
    try:
        importlib_metadata.version("pymatting")
        import pymatting  # noqa: F401
        _ALPHA_MATTING_READY = True
    except (UnicodeDecodeError, Exception):
        _ALPHA_MATTING_READY = False
    return _ALPHA_MATTING_READY


def model_is_ready(model_name: str) -> bool:
    if model_name not in SUPPORTED_MODELS:
        return False
    models = _ensure_model_home()
    return (models / _MODEL_FILES[model_name]).is_file()


def missing_model_message(model_name: str) -> str:
    fname = _MODEL_FILES.get(model_name, model_name)
    return (
        f"Brak modelu {fname}. "
        "Uruchom: BIN\\dev\\scripts\\setup_rmbg_models.ps1"
    )


def get_session(model_name: str, *, force_cpu: bool = False):
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Nieobsługiwany model: {model_name}")
    if not model_is_ready(model_name):
        raise FileNotFoundError(missing_model_message(model_name))

    providers = _onnx_providers(prefer_gpu=not force_cpu)
    with _SESSION_LOCK:
        cached = _SESSIONS.get(model_name)
        if cached is not None and _SESSION_PROVIDERS.get(model_name) == providers:
            return cached

    bootstrap_runtime_paths()
    from inyfinn_resizer.utils.frozen_stdio import ensure_stdio

    ensure_stdio()
    _ensure_model_home()

    from rembg import new_session

    try:
        session = new_session(model_name, providers=providers)
    except TypeError:
        session = new_session(model_name)
    except Exception as exc:
        if not force_cpu and _is_onnx_provider_error(exc):
            return get_session(model_name, force_cpu=True)
        raise RuntimeError(f"Nie można załadować modelu {model_name}: {exc}") from exc

    with _SESSION_LOCK:
        _SESSIONS[model_name] = session
        _SESSION_PROVIDERS[model_name] = providers
    return session


def remove_background(
    image: Image.Image,
    *,
    model_name: str = "birefnet-general",
    alpha_matting: bool = True,
    post_process_mask: bool = True,
) -> Image.Image:
    """Zwraca obraz RGBA z przezroczystym tłem."""
    from rembg import remove

    use_alpha_matting = alpha_matting and alpha_matting_available()
    src = image.convert("RGB") if image.mode not in ("RGB", "RGBA") else image

    for force_cpu in (False, True):
        try:
            session = get_session(model_name, force_cpu=force_cpu)
            result = remove(
                src,
                session=session,
                alpha_matting=use_alpha_matting,
                post_process_mask=post_process_mask,
            )
            if result.mode != "RGBA":
                result = result.convert("RGBA")
            return result
        except UnicodeDecodeError as exc:
            _clear_session(model_name)
            if force_cpu:
                raise RuntimeError(
                    "Usuwanie tła: błąd DirectML/ONNX (kodowanie komunikatu). "
                    "Spróbuj ponownie lub wybierz „Najlepsza Jakość”."
                ) from exc
        except Exception as exc:
            if force_cpu or not _is_onnx_provider_error(exc):
                raise
            _clear_session(model_name)
