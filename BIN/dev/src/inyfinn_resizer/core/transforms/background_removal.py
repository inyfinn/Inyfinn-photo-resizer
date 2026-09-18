"""Usuwanie tła — rembg + BiRefNet (ONNX, DirectML na Windows)."""

from __future__ import annotations

import os
import threading
from importlib import metadata as importlib_metadata
from typing import TYPE_CHECKING

from inyfinn_resizer.core.transforms import rmbg_models
from inyfinn_resizer.utils.paths import bootstrap_runtime_paths

if TYPE_CHECKING:
    from PIL import Image

_SESSIONS: dict[str, object] = {}
_SESSION_PROVIDERS: dict[str, list[str]] = {}
_SESSION_LOCK = threading.Lock()
# U2NET_HOME jest globalny — tworzenie sesji rembg po jednej naraz (RLock: fallback na CPU).
_CREATE_LOCK = threading.RLock()
_INFER_LOCK = threading.Lock()
_ALPHA_MATTING_READY: bool | None = None

# rembg na pełnym 20 MP + alpha matting wiesza partię (51 plików, 2026-09-14).
REMBG_MAX_EDGE = 2560
ALPHA_MATTING_MAX_EDGE = 1600

SUPPORTED_MODELS = tuple(rmbg_models.MODELS)


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


def rembg_max_edge(
    *,
    box_w: int = 0,
    box_h: int = 0,
    width: int = 0,
    height: int = 0,
    dimension: int = 0,
) -> int:
    """Najdłuższy bok, na którym puszczamy sieć — nie większy niż wyjście i 2560 px."""
    target = max(int(box_w or 0), int(box_h or 0), int(width or 0), int(height or 0), int(dimension or 0))
    if target > 0:
        return max(64, min(REMBG_MAX_EDGE, target))
    return REMBG_MAX_EDGE


def downscale_for_rembg(image: "Image.Image", max_edge: int) -> "Image.Image":
    from PIL import Image as PILImage

    w, h = image.size
    longest = max(w, h)
    if longest <= max_edge or max_edge <= 0:
        return image
    scale = max_edge / longest
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return image.resize((nw, nh), PILImage.Resampling.LANCZOS)


def model_is_ready(model_name: str) -> bool:
    return rmbg_models.is_ready(model_name)


def missing_model_message(model_name: str) -> str:
    spec = rmbg_models.MODELS.get(model_name)
    if spec is None:
        return f"Nieobsługiwany model usuwania tła: {model_name}"
    return (
        f"Model usuwania tła „{spec.label}” ({spec.size_mb} MB) nie jest jeszcze pobrany. "
        "Uruchom konwersję z zaznaczonym „Usuń tło” w aplikacji — zaproponuje pobranie."
    )


def _new_rembg_session(model_name: str, providers: list[str]):
    model_path = rmbg_models.find_model(model_name)
    if model_path is None:
        raise FileNotFoundError(missing_model_message(model_name))
    from rembg import new_session

    with _CREATE_LOCK:
        os.environ["U2NET_HOME"] = str(model_path.parent)
        # SHA256 sprawdzamy sami — bez tego rembg przy innym MD5 po cichu pobiera 1 GB.
        os.environ["MODEL_CHECKSUM_DISABLED"] = "1"
        try:
            return new_session(model_name, providers=providers)
        except TypeError:
            return new_session(model_name)


def get_session(model_name: str, *, force_cpu: bool = False):
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Nieobsługiwany model: {model_name}")

    providers = _onnx_providers(prefer_gpu=not force_cpu)
    with _SESSION_LOCK:
        cached = _SESSIONS.get(model_name)
        if cached is not None and _SESSION_PROVIDERS.get(model_name) == providers:
            return cached

    bootstrap_runtime_paths()
    from inyfinn_resizer.utils.frozen_stdio import ensure_stdio

    ensure_stdio()

    try:
        session = _new_rembg_session(model_name, providers)
    except FileNotFoundError:
        raise
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

    src = image.convert("RGB") if image.mode not in ("RGB", "RGBA") else image
    use_alpha_matting = (
        alpha_matting
        and alpha_matting_available()
        and max(src.size) <= ALPHA_MATTING_MAX_EDGE
    )

    for force_cpu in (False, True):
        try:
            session = get_session(model_name, force_cpu=force_cpu)
            with _INFER_LOCK:
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
