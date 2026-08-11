"""Test kotwicy przycięcia cover crop."""

from __future__ import annotations

from inyfinn_resizer.core.transforms.image_ops import _anchor_origin


def test_anchor_origin_center() -> None:
    left, top = _anchor_origin(2000, 1500, 1200, 1200, "center")
    assert left == 400
    assert top == 150


def test_anchor_origin_top_left() -> None:
    left, top = _anchor_origin(2000, 1500, 1200, 1200, "top-left")
    assert left == 0
    assert top == 0


def test_anchor_origin_bottom_right() -> None:
    left, top = _anchor_origin(2000, 1500, 1200, 1200, "bottom-right")
    assert left == 800
    assert top == 300
