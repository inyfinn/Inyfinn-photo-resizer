"""EXIF/metadata helpers."""

from __future__ import annotations

from pathlib import Path

from inyfinn_resizer.core.job import MetadataPolicy


def strip_metadata_file(path: Path, policy: MetadataPolicy) -> None:
    if policy.strip_all or not policy.keep_exif:
        try:
            from PIL import Image

            im = Image.open(path)
            if "exif" in im.info:
                data = list(im.getdata())
                clean = Image.new(im.mode, im.size)
                clean.putdata(data)
                clean.save(path)
            else:
                im.save(path)
        except Exception:
            pass
