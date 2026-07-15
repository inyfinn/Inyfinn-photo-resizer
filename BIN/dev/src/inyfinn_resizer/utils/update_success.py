"""Jednorazowy komunikat po udanej aktualizacji (po restarcie aplikacji)."""

from __future__ import annotations

import json
from pathlib import Path

from inyfinn_resizer.utils.update_cache import updates_dir


def _marker_path() -> Path:
    return updates_dir() / "pending_success.json"


def mark_pending_success(target_version: str) -> None:
    updates_dir().mkdir(parents=True, exist_ok=True)
    _marker_path().write_text(
        json.dumps({"target_version": target_version}, ensure_ascii=False),
        encoding="utf-8",
    )


def consume_pending_success(current_version: str) -> str | None:
    path = _marker_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        target = str(data.get("target_version", "")).strip()
    except (json.JSONDecodeError, OSError):
        path.unlink(missing_ok=True)
        return None
    path.unlink(missing_ok=True)
    if target and target == current_version:
        return target
    return None
