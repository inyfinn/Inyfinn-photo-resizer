"""Test jednorazowego komunikatu po aktualizacji."""

from __future__ import annotations

from pathlib import Path

import inyfinn_resizer.utils.update_success as success


def test_consume_pending_success_once(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(success, "updates_dir", lambda: tmp_path)
    success.mark_pending_success("1.0.61")
    assert success.consume_pending_success("1.0.61") == "1.0.61"
    assert success.consume_pending_success("1.0.61") is None


def test_consume_mismatch_version(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(success, "updates_dir", lambda: tmp_path)
    success.mark_pending_success("1.0.62")
    assert success.consume_pending_success("1.0.61") is None
