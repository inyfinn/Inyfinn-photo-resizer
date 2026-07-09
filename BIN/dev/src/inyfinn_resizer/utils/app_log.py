"""Dziennik operacji użytkownika — rotacja max 30 wpisów."""

from __future__ import annotations

import socket
from datetime import datetime
from pathlib import Path

from inyfinn_resizer.utils.paths import project_root

MAX_LOG_ENTRIES = 30


def log_path() -> Path:
    folder = project_root() / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "activity.log"


def _hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def log_event(action: str, detail: str = "", *, status: str = "OK") -> None:
    """Zapisuje wpis: data | godzina | komputer | status | akcja | szczegóły."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    host = _hostname()
    detail_part = f" | {detail}" if detail else ""
    line = f"{stamp} | {host} | {status} | {action}{detail_part}\n"
    path = log_path()
    lines: list[str] = []
    if path.is_file():
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        except OSError:
            lines = []
    lines.append(line)
    if len(lines) > MAX_LOG_ENTRIES:
        lines = lines[-MAX_LOG_ENTRIES:]
    try:
        path.write_text("".join(lines), encoding="utf-8")
    except OSError:
        pass


def read_recent(limit: int = MAX_LOG_ENTRIES) -> list[str]:
    path = log_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-limit:]
