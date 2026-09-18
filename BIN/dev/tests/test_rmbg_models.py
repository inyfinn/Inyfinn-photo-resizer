"""Modele usuwania tła pobierane przy pierwszym użyciu (od 2.4.8) — bez sieci."""

from __future__ import annotations

import hashlib
import io
import shutil
from pathlib import Path

import pytest

from inyfinn_resizer.core.transforms import background_removal as br
from inyfinn_resizer.core.transforms import rmbg_models as rm

WORK = Path(__file__).parent / "output" / "rmbg_models_test"
PAYLOAD = b"onnx-model-" * 1000


class _FakeResponse(io.BytesIO):
    def __init__(self, data: bytes, status: int = 200) -> None:
        super().__init__(data)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


@pytest.fixture
def fake_model(monkeypatch):
    if WORK.exists():
        assert WORK.name == "rmbg_models_test" and WORK.parent.name == "output"
        shutil.rmtree(WORK)
    user = WORK / "user"
    bundle = WORK / "bundle"
    bundle.mkdir(parents=True)
    spec = rm.ModelSpec(
        name="birefnet-general-lite",
        label="Szybko",
        url="https://example.invalid/model.onnx",
        filename="birefnet-general-lite.onnx",
        size=len(PAYLOAD),
        sha256=hashlib.sha256(PAYLOAD).hexdigest(),
    )
    monkeypatch.setitem(rm.MODELS, spec.name, spec)
    monkeypatch.setattr(rm, "user_models_dir", lambda: user)
    monkeypatch.setattr(rm, "rmbg_models_dir", lambda: bundle)
    requests: list = []

    def _urlopen(req, timeout=0):
        requests.append(req)
        start = 0
        rng = req.headers.get("Range")
        if rng:
            start = int(rng.split("=")[1].rstrip("-"))
            return _FakeResponse(PAYLOAD[start:], status=206)
        return _FakeResponse(PAYLOAD)

    monkeypatch.setattr(rm.urllib.request, "urlopen", _urlopen)
    yield spec, user, bundle, requests
    shutil.rmtree(WORK, ignore_errors=True)


def test_missing_model_is_not_ready(fake_model) -> None:
    assert not rm.is_ready("birefnet-general-lite")
    assert "nie jest jeszcze pobrany" in br.missing_model_message("birefnet-general-lite")


def test_download_verifies_and_makes_model_ready(fake_model) -> None:
    spec, user, _bundle, _requests = fake_model
    seen: list[int] = []
    path = rm.download_model(spec.name, progress=lambda r, t: seen.append(r))
    assert path == user / spec.filename
    assert path.read_bytes() == PAYLOAD
    assert not (user / (spec.filename + ".part")).exists()
    assert seen[-1] == spec.size
    assert rm.find_model(spec.name) == path
    assert br.model_is_ready(spec.name)


def test_download_resumes_partial_file(fake_model) -> None:
    spec, user, _bundle, requests = fake_model
    user.mkdir(parents=True)
    (user / (spec.filename + ".part")).write_bytes(PAYLOAD[:4000])
    rm.download_model(spec.name)
    assert requests[-1].headers.get("Range") == "bytes=4000-"
    assert (user / spec.filename).read_bytes() == PAYLOAD


def test_corrupt_download_is_rejected(fake_model, monkeypatch) -> None:
    spec, user, _bundle, _requests = fake_model
    bad = b"X" * len(PAYLOAD)
    monkeypatch.setattr(rm.urllib.request, "urlopen", lambda req, timeout=0: _FakeResponse(bad))
    with pytest.raises(OSError, match="sumę kontrolną"):
        rm.download_model(spec.name)
    assert not (user / spec.filename).exists()
    assert not (user / (spec.filename + ".part")).exists()


def test_cancel_keeps_part_for_resume(fake_model) -> None:
    spec, user, _bundle, _requests = fake_model
    with pytest.raises(rm.ModelDownloadCancelled):
        rm.download_model(spec.name, cancelled=lambda: True)
    assert not (user / spec.filename).exists()


def test_bundled_model_with_same_size_but_wrong_content_is_ignored(fake_model) -> None:
    """Tak wyglądały uszkodzone BiRefNet-*.onnx w paczce ≤ 2.4.7."""
    spec, _user, bundle, _requests = fake_model
    (bundle / spec.filename).write_bytes(b"Y" * len(PAYLOAD))
    assert rm.find_model(spec.name) is None


def test_valid_bundled_model_from_older_install_is_used(fake_model) -> None:
    spec, _user, bundle, _requests = fake_model
    (bundle / spec.filename).write_bytes(PAYLOAD)
    assert rm.find_model(spec.name) == bundle / spec.filename


def test_real_model_specs_are_consistent() -> None:
    assert set(rm.MODELS) == set(br.SUPPORTED_MODELS) == {"birefnet-general", "birefnet-general-lite"}
    for name, spec in rm.MODELS.items():
        assert spec.filename == f"{name}.onnx"  # rembg szuka tej nazwy w U2NET_HOME
        assert spec.url.startswith("https://github.com/danielgatis/rembg/releases/")
        assert len(spec.sha256) == 64
