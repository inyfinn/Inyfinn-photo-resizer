"""Porównywanie wersji semver-lite (1.0.59, v1.0.60)."""

from __future__ import annotations

import re


def normalize_version(raw: str) -> str:
    text = raw.strip()
    if text.lower().startswith("v"):
        text = text[1:]
    return text


def version_tuple(raw: str) -> tuple[int, ...]:
    text = normalize_version(raw)
    parts = re.split(r"[.\-+]", text)
    out: list[int] = []
    for part in parts:
        if not part:
            continue
        digits = re.match(r"(\d+)", part)
        if digits:
            out.append(int(digits.group(1)))
        else:
            break
    return tuple(out or (0,))


def is_newer(remote: str, local: str) -> bool:
    return version_tuple(remote) > version_tuple(local)
