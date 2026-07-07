"""Sekwencja wizek — bootstrap + kompresja in-place (port batch_compress_wizek.py)."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from inyfinn_resizer.core.compressors.jpeg import compress_jpeg_file
from inyfinn_resizer.core.compressors.png import apply_pngquant, cleanup_pngquant_artifacts_in_folder
from inyfinn_resizer.core.job import JobStatus

SIZE_SUFFIX_RE = re.compile(r"-(XL|L|S(?:-SKLEP)?)$", re.I)
SHOP_W, SHOP_H = 848, 1200
S_SHORT_EDGE = 1200
S_JPG_CANVAS = 1200
SHOP_PNG_KB_AT_50 = 200
SHOP_JPG_KB_AT_50 = 90
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


@dataclass
class WizFileResult:
    name: str
    profile: str
    old_bytes: int
    new_bytes: int
    status: JobStatus
    message: str = ""


@dataclass
class WizFolderResult:
    folder: Path
    status: JobStatus
    message: str = ""
    files: list[WizFileResult] = field(default_factory=list)
    created: list[str] = field(default_factory=list)

    @property
    def old_bytes(self) -> int:
        return sum(f.old_bytes for f in self.files)

    @property
    def new_bytes(self) -> int:
        return sum(f.new_bytes for f in self.files)


def quality_pct_from_slider(slider_val: int) -> int:
    s = max(1, min(10, int(slider_val)))
    return s * 10


def ui_quality_to_wiz_slider(quality_0_100: int) -> int:
    return max(1, min(10, round(max(1, quality_0_100) / 10)))


def stem_base(name: str) -> str:
    stem = Path(name).stem
    return SIZE_SUFFIX_RE.sub("", stem)


def profile_for_name(name: str) -> str:
    stem = Path(name).stem
    if re.search(r"-XL(?:$|-)", stem, re.I):
        return "xl"
    if re.search(r"SKLEP", stem, re.I):
        return "sklep"
    return "standard"


def shop_target_kb(slider_val: int, is_png: bool) -> float:
    pct = quality_pct_from_slider(slider_val)
    base = SHOP_PNG_KB_AT_50 if is_png else SHOP_JPG_KB_AT_50
    return max(10.0, round(base * (pct / 50.0), 1))


def shop_jpg_cap(slider_val: int) -> int:
    return min(100, quality_pct_from_slider(slider_val) + 35)


def _resample():
    return Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS


def list_images(folder: Path) -> list[str]:
    return sorted(
        f.name
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS and ".pq." not in f.name
    )


def find_masters_by_base(folder: Path) -> dict[str, str]:
    pngs = [f.name for f in folder.iterdir() if f.suffix.lower() == ".png" and ".pq." not in f.name]
    if pngs:
        by_base: dict[str, str] = {}
        for f in pngs:
            base = stem_base(f) or Path(f).stem
            path = folder / f
            is_l = bool(re.search(r"-L\.png$", f, re.I))
            if base not in by_base:
                by_base[base] = f
                continue
            cur = by_base[base]
            cur_l = bool(re.search(r"-L\.png$", cur, re.I))
            if is_l and not cur_l:
                by_base[base] = f
            elif is_l == cur_l and path.stat().st_size > (folder / cur).stat().st_size:
                by_base[base] = f
        return by_base

    images = [
        f.name
        for f in folder.iterdir()
        if f.suffix.lower() in IMAGE_EXTS and ".pq." not in f.name
    ]
    if not images:
        return {}
    by_base: dict[str, str] = {}
    for f in images:
        base = stem_base(f) or Path(f).stem
        path = folder / f
        if base not in by_base or path.stat().st_size > (folder / by_base[base]).stat().st_size:
            by_base[base] = f
    return by_base


def package_incomplete(folder: Path, base: str) -> tuple[bool, list[str]]:
    names = [
        f"{base}-XL.png", f"{base}-L.png", f"{base}-S.png", f"{base}-S-SKLEP.png",
        f"{base}-XL.jpg", f"{base}-L.jpg", f"{base}-S.jpg", f"{base}-S-SKLEP.jpg",
    ]
    missing = [n for n in names if not (folder / n).is_file()]
    return len(missing) > 0, missing


def resize_short_edge(im: Image.Image, target: int) -> Image.Image:
    w, h = im.size
    short = min(w, h)
    if short <= 0 or short == target:
        return im.copy()
    scale = float(target) / short
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    return im.resize((nw, nh), _resample())


def make_shop_canvas(im: Image.Image) -> Image.Image:
    tw, th = SHOP_W, SHOP_H
    w, h = im.size
    if w <= 0 or h <= 0:
        return im.copy()
    scale = min(float(tw) / w, float(th) / h)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    im2 = im.resize((nw, nh), _resample())
    if im2.mode != "RGBA":
        im2 = im2.convert("RGBA")
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(im2, ((tw - nw) // 2, (th - nh) // 2), im2)
    return canvas


def make_jpg_canvas_square(im: Image.Image, size: int = S_JPG_CANVAS) -> Image.Image:
    w, h = im.size
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    long_side = max(w, h)
    if long_side > 0 and long_side != size:
        scale = float(size) / long_side
        im = im.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))), _resample())
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
    return canvas


def save_png(im: Image.Image, path: Path) -> None:
    if im.mode not in ("RGBA", "RGB", "P"):
        im = im.convert("RGBA")
    im.save(path, format="PNG", optimize=True)


def save_jpg_from_rgba(im: Image.Image, path: Path, quality: int) -> None:
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[-1])
    bg.save(path, format="JPEG", quality=int(quality), optimize=True, progressive=True)


def bootstrap_package_from_masters(folder: Path, slider_val: int) -> list[str]:
    masters = find_masters_by_base(folder)
    if not masters:
        return []

    pct = quality_pct_from_slider(slider_val)
    created: list[str] = []

    for base, master_name in masters.items():
        incomplete, _ = package_incomplete(folder, base)
        if not incomplete:
            continue

        master_path = folder / master_name
        im_master = Image.open(master_path)
        im_master.load()

        def write_png_only(suffix: str, im: Image.Image) -> None:
            png_name = f"{base}{suffix}.png"
            png_path = folder / png_name
            if not png_path.is_file():
                save_png(im, png_path)
                created.append(png_name)

        def write_png_jpg_pair(suffix: str, im: Image.Image, jpg_q: int) -> None:
            png_name = f"{base}{suffix}.png"
            jpg_name = f"{base}{suffix}.jpg"
            if not (folder / png_name).is_file():
                save_png(im, folder / png_name)
                created.append(png_name)
            if not (folder / jpg_name).is_file():
                save_jpg_from_rgba(im, folder / jpg_name, jpg_q)
                created.append(jpg_name)

        xl_path = folder / f"{base}-XL.png"
        if not xl_path.is_file():
            save_png(im_master, xl_path)
            created.append(xl_path.name)

        l_path = folder / f"{base}-L.png"
        if not l_path.is_file():
            save_png(im_master, l_path)
            created.append(l_path.name)

        write_png_only("-S", resize_short_edge(im_master, S_SHORT_EDGE))
        write_png_jpg_pair("-S-SKLEP", make_shop_canvas(im_master), pct)

        xl_jpg = folder / f"{base}-XL.jpg"
        if not xl_jpg.is_file():
            save_jpg_from_rgba(im_master, xl_jpg, 90)
            created.append(xl_jpg.name)

        l_jpg = folder / f"{base}-L.jpg"
        if not l_jpg.is_file():
            save_jpg_from_rgba(im_master, l_jpg, pct)
            created.append(l_jpg.name)

        s_jpg = folder / f"{base}-S.jpg"
        if not s_jpg.is_file():
            save_jpg_from_rgba(make_jpg_canvas_square(im_master), s_jpg, pct)
            created.append(s_jpg.name)

        im_master.close()

    return created


def ensure_xl_masters(folder: Path, files: list[str]) -> list[str]:
    created: list[str] = []
    for name in files:
        base, ext = Path(name).stem, Path(name).suffix
        if ext.lower() != ".png" or not re.search(r"-L$", base, re.I):
            continue
        xl_name = re.sub(r"-L$", "-XL", base, flags=re.I) + ext
        src_f, xl_f = folder / name, folder / xl_name
        if src_f.is_file() and not xl_f.is_file():
            shutil.copy2(src_f, xl_f)
            created.append(xl_name)
    for name in files:
        base, ext = Path(name).stem, Path(name).suffix
        if ext.lower() not in (".jpg", ".jpeg") or not re.search(r"-L$", base, re.I):
            continue
        xl_name = re.sub(r"-L$", "-XL", base, flags=re.I) + ext
        src_f, xl_f = folder / name, folder / xl_name
        if src_f.is_file() and not xl_f.is_file() and xl_name not in created:
            shutil.copy2(src_f, xl_f)
            created.append(xl_name)
    return created


def compress_wiz_file(path: Path, slider_val: int) -> tuple[bool, str]:
    profile = profile_for_name(path.name)
    ext = path.suffix.lower()

    if profile == "xl" and ext == ".png":
        return True, "master bez kompresji"

    if not path.is_file():
        return False, "brak pliku"

    pct = quality_pct_from_slider(slider_val)

    if ext in (".jpg", ".jpeg"):
        if profile == "xl":
            ok, msg = compress_jpeg_file(path, quality=90)
        elif profile == "sklep":
            ok, msg = compress_jpeg_file(
                path,
                quality=shop_jpg_cap(slider_val),
                target_kb=shop_target_kb(slider_val, False),
                target_tolerance=0.2,
            )
        else:
            ok, msg = compress_jpeg_file(path, quality=pct)
        return ok, msg

    if ext == ".png":
        if profile == "sklep":
            ok, msg = apply_pngquant(
                path,
                target_kb=shop_target_kb(slider_val, True),
                target_tolerance=0.2,
                quality_pct=pct,
            )
        else:
            ok, msg = apply_pngquant(path, quality_pct=pct)
        return ok, msg

    return False, "nieobsługiwany format"


def discover_wiz_folders(paths: list[Path]) -> list[Path]:
    """Foldery z grafiką — bezpośrednio wskazane lub liście z jednym obrazem."""
    folders: set[Path] = set()
    for p in paths:
        if p.is_dir():
            if list_images(p) or find_masters_by_base(p):
                folders.add(p.resolve())
            continue
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            folders.add(p.parent.resolve())
    return sorted(folders)


def process_wiz_folder(folder: Path, slider_val: int) -> WizFolderResult:
    folder = folder.resolve()
    if not folder.is_dir():
        return WizFolderResult(folder, JobStatus.ERROR, "Nie istnieje")

    files = list_images(folder)
    if not files and not find_masters_by_base(folder):
        return WizFolderResult(folder, JobStatus.SKIPPED, "Brak PNG/JPG")

    created = bootstrap_package_from_masters(folder, slider_val)
    files = list_images(folder)
    xl_created = ensure_xl_masters(folder, files)
    all_names = sorted(set(files + xl_created))

    file_results: list[WizFileResult] = []
    errors = 0

    for name in all_names:
        path = folder / name
        profile = profile_for_name(name)
        old_bytes = path.stat().st_size if path.is_file() else 0

        if profile == "xl" and name.lower().endswith(".png"):
            file_results.append(WizFileResult(
                name, profile, old_bytes, old_bytes, JobStatus.OK, "master bez kompresji",
            ))
            continue

        ok, msg = compress_wiz_file(path, slider_val)
        new_bytes = path.stat().st_size if path.is_file() else 0
        status = JobStatus.OK if ok else JobStatus.ERROR
        if not ok:
            errors += 1
        file_results.append(WizFileResult(name, profile, old_bytes, new_bytes, status, msg))

    status = JobStatus.OK if errors == 0 else JobStatus.ERROR
    msg = f"Przetworzono {len(file_results)} plików"
    if created:
        msg += f", utworzono {len(created)}"
    if errors:
        msg += f", błędy: {errors}"

    cleanup_pngquant_artifacts_in_folder(folder)

    return WizFolderResult(folder, status, msg, file_results, created)
