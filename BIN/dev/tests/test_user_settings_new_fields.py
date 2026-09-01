"""Obieg crop_anchor / wymiarów ramki przez preset — bez MainWindow.

Pola UI custom_format / custom_format_w / custom_format_h żyją tylko
w restore_to_window() i wymagają okna; ten plik ich nie rusza.
"""

from __future__ import annotations

from inyfinn_resizer.app.widgets.crop_anchor_picker import ANCHOR_KEYS
from inyfinn_resizer.core.job import (
    BatchSettings,
    FormatOptions,
    MetadataPolicy,
    RenameRule,
    ResizeMode,
    ResizeOptions,
    TransformOptions,
    job_from_dict,
    job_to_dict,
)
from inyfinn_resizer.core.presets import apply_preset, settings_to_dict


def _payload(*, crop_anchor: str = "center", box_w: int = 1200, box_h: int = 848) -> dict:
    return settings_to_dict(
        "png",
        FormatOptions(),
        ResizeOptions(
            mode=ResizeMode.FIT_BOX,
            box_w=box_w,
            box_h=box_h,
            crop_anchor=crop_anchor,
        ),
        TransformOptions(),
        MetadataPolicy(),
        RenameRule(),
        BatchSettings(),
    )


def test_crop_anchor_roundtrip_all_keys() -> None:
    for key in ANCHOR_KEYS:
        applied = apply_preset(_payload(crop_anchor=key))
        assert applied["resize"].crop_anchor == key


def test_custom_box_dimensions_roundtrip() -> None:
    applied = apply_preset(_payload(box_w=1600, box_h=900))
    assert applied["resize"].box_w == 1600
    assert applied["resize"].box_h == 900


def test_missing_crop_anchor_from_v210_defaults_to_center() -> None:
    """Sesja 2.1.0 nie ma crop_anchor w resize — start nie może wywrócić się na KeyError."""
    data = _payload()
    del data["resize"]["crop_anchor"]
    applied = apply_preset(data)
    assert applied["resize"].crop_anchor == "center"


def test_legacy_payload_without_new_ui_keys_applies() -> None:
    """Fragment sesji 2.1.0: brak ui.custom_format* i ui.crop_anchor."""
    data = _payload()
    data["ui"] = {"theme": "light", "formats": ["webp"]}
    applied = apply_preset(data)
    assert applied["resize"].crop_anchor == "center"
    assert "custom_format" not in data["ui"]
    assert "crop_anchor" not in data["ui"]


def test_unknown_crop_anchor_does_not_raise() -> None:
    applied = apply_preset(_payload(crop_anchor="north-pole"))
    assert applied["resize"].crop_anchor == "north-pole"


def test_job_dict_missing_crop_anchor_defaults() -> None:
    spec = job_from_dict(
        {
            "input_path": "in.jpg",
            "output_path": "out.jpg",
            "resize": {"mode": "fit_box", "box_w": 800, "box_h": 600},
        }
    )
    assert spec.resize.crop_anchor == "center"
    assert spec.resize.box_w == 800
    assert spec.resize.box_h == 600


def test_job_dict_crop_anchor_roundtrip() -> None:
    from pathlib import Path

    from inyfinn_resizer.core.job import JobSpec

    original = JobSpec(
        input_path=Path("in.jpg"),
        output_path=Path("out.jpg"),
        resize=ResizeOptions(
            mode=ResizeMode.FIT_BOX,
            box_w=1200,
            box_h=848,
            crop_anchor="bottom-right",
        ),
    )
    restored = job_from_dict(job_to_dict(original))
    assert restored.resize.crop_anchor == "bottom-right"
    assert restored.resize.box_w == 1200
    assert restored.resize.box_h == 848
