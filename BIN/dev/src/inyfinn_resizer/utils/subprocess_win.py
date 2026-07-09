"""Uruchamianie procesów zewnętrznych bez migania okna CMD (Windows)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

CREATE_NO_WINDOW = 0x08000000


def _env_for_tool(cmd: list[str], env: dict[str, str] | None) -> dict[str, str] | None:
    if not cmd:
        return env
    tool = Path(cmd[0])
    if not tool.suffix.lower() == ".exe" or not tool.is_file():
        return env
    merged = dict(os.environ if env is None else env)
    tool_dir = str(tool.parent)
    merged["PATH"] = tool_dir + os.pathsep + merged.get("PATH", "")
    return merged


def run_hidden(
    cmd: list[str],
    *,
    capture_output: bool = False,
    text: bool = False,
    timeout: float | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """Uruchamia subprocess.run; przy timeout podnosi subprocess.TimeoutExpired."""
    kwargs: dict[str, Any] = {"check": check, "env": _env_for_tool(cmd, env)}
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
        if text:
            kwargs["text"] = True
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    if timeout is not None:
        kwargs["timeout"] = timeout

    if sys.platform == "win32":
        kwargs["creationflags"] = CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo

    return subprocess.run(cmd, **kwargs)
