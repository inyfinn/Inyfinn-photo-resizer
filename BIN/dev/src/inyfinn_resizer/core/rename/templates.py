"""Rename templates and preview."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from inyfinn_resizer.core.formats.registry import output_extension
from inyfinn_resizer.core.job import RenameRule


def apply_rename_rule(
    src: Path,
    counter: int,
    rule: RenameRule,
    output_format: str,
) -> str:
    stem = src.stem
    if rule.search:
        stem = stem.replace(rule.search, rule.replace)

    now = datetime.now()
    name = rule.template.format(
        name=stem,
        counter=counter,
        date=now.strftime("%Y%m%d"),
        time=now.strftime("%H%M%S"),
        ext=output_format,
    )
    ext = output_extension(output_format)
    if rule.uppercase_ext:
        ext = ext.upper()
    return name + ext


def preview_rename(paths: list[Path], rule: RenameRule, output_format: str) -> list[tuple[str, str]]:
    out = []
    for i, p in enumerate(paths, start=1):
        new_name = apply_rename_rule(p, i, rule, output_format)
        out.append((p.name, new_name))
    return out
