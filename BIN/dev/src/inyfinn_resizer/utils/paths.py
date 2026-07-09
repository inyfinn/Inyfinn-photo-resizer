"""Project paths and bundled tool discovery."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _is_dev_root(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() or (path / "tools").is_dir()


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "_internal").is_dir():
            return exe_dir
        bin_dir = exe_dir.parent if exe_dir.name.upper() == "BIN" else exe_dir / "BIN"
        if (bin_dir / "_internal").is_dir():
            return bin_dir
        return exe_dir
    p = Path(__file__).resolve().parent
    for _ in range(10):
        if _is_dev_root(p):
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


def tool_env_path(tool_path: Path) -> str:
    """Katalog narzędzia + bundle tools — DLL pngquant/gifsicle na Windows."""
    parts: list[str] = []
    bundled = bundle_dir()
    if bundled is not None:
        parts.append(str(bundled))
        for sub in ("tools/pngquant", "tools/gifsicle", "tools/cwebp", "tools/oxipng", "tools/avifenc", "tools/libvips/bin", "tools"):
            p = bundled / sub.replace("/", os.sep)
            if p.is_dir():
                parts.append(str(p))
    if tool_path.is_file():
        parts.append(str(tool_path.parent))
    existing = os.environ.get("PATH", "")
    return os.pathsep.join(parts + [existing])


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


def bundled_libvips() -> bool:
    return (tools_dir() / "libvips" / "bin").is_dir()


def bootstrap_runtime_paths() -> None:
    """Ustaw PATH dla narzędzi z _internal (pngquant, gifsicle) w EXE."""
    bundled = bundle_dir()
    if bundled is None:
        return
    parts = [str(bundled)]
    for sub in ("tools/pngquant", "tools/gifsicle", "tools/cwebp", "tools/oxipng", "tools/avifenc", "tools/libvips/bin", "tools"):
        p = bundled / sub.replace("/", os.sep)
        if p.is_dir():
            parts.append(str(p))
    existing = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(parts + [existing])
    ensure_vips_lib()


def ensure_vips_lib() -> None:
    """Point pyvips at bundled libvips on Windows if present."""
    vips_bin = tools_dir() / "libvips" / "bin"
    if vips_bin.is_dir():
        os.environ["PATH"] = str(vips_bin) + os.pathsep + os.environ.get("PATH", "")
        os.environ["VIPSHOME"] = str(tools_dir() / "libvips")
