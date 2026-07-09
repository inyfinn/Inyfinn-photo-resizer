"""External tool wrappers: cwebp, avifenc, oxipng."""

from __future__ import annotations

from pathlib import Path

from inyfinn_resizer.utils.paths import find_tool
from inyfinn_resizer.utils.subprocess_win import run_hidden


def run_external(cmd: list[str]) -> tuple[bool, str]:
    try:
        r = run_hidden(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return True, "ok"
        return False, r.stderr.strip() or r.stdout.strip() or f"exit {r.returncode}"
    except OSError as e:
        return False, str(e)


def compress_webp_cwebp(src: Path, dst: Path, quality: int, lossless: bool = False) -> tuple[bool, str]:
    cwebp = find_tool("cwebp")
    if not cwebp:
        return False, "no_cwebp"
    cmd = [str(cwebp), "-quiet"]
    if lossless:
        cmd.append("-lossless")
    else:
        cmd.extend(["-q", str(max(0, min(100, quality)))])
    cmd.extend([str(src), "-o", str(dst)])
    ok, msg = run_external(cmd)
    return ok, msg if ok else f"cwebp: {msg}"


def compress_avif_avifenc(src: Path, dst: Path, quality: int, lossless: bool = False) -> tuple[bool, str]:
    avifenc = find_tool("avifenc")
    if not avifenc:
        return False, "no_avifenc"
    cmd = [str(avifenc), str(src), str(dst)]
    if lossless:
        cmd.extend(["--lossless", "-s", "0"])
    else:
        q = max(0, min(100, quality))
        cmd.extend(["-q", str(q), "-s", "4"])
    ok, msg = run_external(cmd)
    return ok, msg if ok else f"avifenc: {msg}"


def optimize_png_oxipng(path: Path) -> tuple[bool, str]:
    oxipng = find_tool("oxipng")
    if not oxipng:
        return False, "no_oxipng"
    ok, msg = run_external([str(oxipng), "-o", "2", "--strip", "safe", str(path)])
    return ok, msg if ok else f"oxipng: {msg}"


def convert_with_tool(tool_name: str, src: Path, dst: Path, quality: int) -> bool:
    """Ogólny wrapper na zewnętrzne enkodery (heif-enc, …)."""
    exe = find_tool(tool_name)
    if not exe:
        return False
    q = max(0, min(100, int(quality)))
    if tool_name in ("heif-enc", "heif_enc"):
        cmd = [str(exe), str(src), "-o", str(dst), "-q", str(q)]
    else:
        cmd = [str(exe), str(src), str(dst)]
    ok, _ = run_external(cmd)
    return ok
