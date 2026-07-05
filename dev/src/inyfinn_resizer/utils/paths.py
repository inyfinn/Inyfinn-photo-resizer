"""Project paths and bundled tool discovery."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    p = Path(__file__).resolve().parent
    for _ in range(8):
        if (p / "pyproject.toml").is_file() or (p / "tools").is_dir():
            return p
        parent = p.parent
        if parent == p:
            break
        p = parent
    return Path(__file__).resolve().parents[3]


def bundle_dir() -> Path | None:
    """PyInstaller one-dir bundle (_internal) when frozen."""
    if not getattr(sys, "frozen", False):
        return None
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    for name in ("_internal", "lib", "app"):
        candidate = project_root() / name
        if candidate.is_dir():
            return candidate
    return None


def tools_dir() -> Path:
    bundled = bundle_dir()
    if bundled is not None:
        return bundled / "tools"
    return project_root() / "tools"


def find_tool(name: str, windows_name: str | None = None) -> Path | None:
    win = windows_name or f"{name}.exe"
    candidates = [
        tools_dir() / "pngquant" / win,
        tools_dir() / name / win,
        tools_dir() / name / name,
        tools_dir() / win,
    ]
    env_key = name.upper().replace("-", "_")
    for var in (env_key, f"{env_key}_PATH"):
        val = os.environ.get(var)
        if val and Path(val).is_file():
            return Path(val)
    found = shutil.which(name)
    if found:
        return Path(found)
    for c in candidates:
        if c.is_file():
            return c
    return None


def ensure_vips_lib() -> None:
    """Point pyvips at bundled libvips on Windows if present."""
    vips_bin = tools_dir() / "libvips" / "bin"
    if vips_bin.is_dir():
        os.environ["PATH"] = str(vips_bin) + os.pathsep + os.environ.get("PATH", "")
        os.environ["VIPSHOME"] = str(tools_dir() / "libvips")
