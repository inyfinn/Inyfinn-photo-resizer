"""Pillow fallback — resize i transformacje gdy brak libvips."""

from __future__ import annotations

from PIL import Image, ImageOps

from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions

_RESAMPLE = Image.Resampling.LANCZOS


def apply_resize_pil(image: Image.Image, opts: ResizeOptions) -> Image.Image:
    if opts.mode in (ResizeMode.NONE, ResizeMode.CROP_SMART, ResizeMode.FIT_BOX):
        if opts.mode == ResizeMode.FIT_BOX and opts.box_w > 0 and opts.box_h > 0:
            return ImageOps.fit(image, (opts.box_w, opts.box_h), method=_RESAMPLE)
        return image

    w, h = image.size
    if opts.mode == ResizeMode.PERCENT:
        scale = max(1, opts.percent) / 100.0
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return image.resize((nw, nh), _RESAMPLE)

    if opts.mode == ResizeMode.PIXELS:
        nw = opts.width or w
        nh = opts.height or h
        if opts.preserve_aspect:
            scale = min(nw / w, nh / h)
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return image.resize((nw, nh), _RESAMPLE)

    if opts.mode == ResizeMode.MAX_DIMENSION:
        dim = opts.dimension
        if max(w, h) <= dim:
            return image
        scale = dim / max(w, h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return image.resize((nw, nh), _RESAMPLE)

    if opts.mode == ResizeMode.ONE_SIDE:
        dim = opts.dimension
        if opts.skip_if_smaller:
            if opts.side == "width" and w <= dim:
                return image
            if opts.side == "height" and h <= dim:
                return image
            if opts.side == "longer" and max(w, h) <= dim:
                return image
            if opts.side == "shorter" and min(w, h) <= dim:
                return image
        if opts.side == "width":
            scale = dim / w
        elif opts.side == "height":
            scale = dim / h
        elif opts.side == "longer":
            scale = dim / max(w, h)
        else:
            scale = dim / min(w, h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return image.resize((nw, nh), _RESAMPLE)

    return image


def apply_scale_postprocess_pil(image: Image.Image, opts: ResizeOptions) -> Image.Image:
    pct = max(1.0, min(100.0, float(opts.scale_percent)))
    if pct != 100.0:
        w, h = image.size
        nw = max(1, int(round(w * pct / 100.0)))
        nh = max(1, int(round(h * pct / 100.0)))
        image = image.resize((nw, nh), _RESAMPLE)
    if opts.min_longest_enabled and opts.min_longest_px > 0:
        w, h = image.size
        longest = max(w, h)
        if longest < opts.min_longest_px:
            scale = opts.min_longest_px / longest
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            image = image.resize((nw, nh), _RESAMPLE)
    return image


def trim_transparent_pil(image: Image.Image, margin: int = 0) -> Image.Image:
    """Przycina przezroczyste marginesy z opcjonalnym marginesem."""
    if image.mode not in ("RGBA", "LA"):
        return image
    bbox = image.getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    if margin:
        left = max(0, left - margin)
        top = max(0, top - margin)
        right = min(image.width, right + margin)
        bottom = min(image.height, bottom + margin)
    return image.crop((left, top, right, bottom))


def apply_transforms_pil(image: Image.Image, opts: TransformOptions) -> Image.Image:
    if opts.trim_transparent:
        image = trim_transparent_pil(image, opts.trim_margin)
    if opts.auto_rotate_exif:
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass
    if opts.flip_h:
        image = ImageOps.mirror(image)
    if opts.flip_v:
        image = ImageOps.flip(image)
    angle = opts.rotate % 360
    if angle:
        image = image.rotate(-angle, expand=True, resample=_RESAMPLE)
    if opts.crop_w > 0 and opts.crop_h > 0:
        image = image.crop((
            opts.crop_x,
            opts.crop_y,
            opts.crop_x + opts.crop_w,
            opts.crop_y + opts.crop_h,
        ))
    if opts.grayscale:
        image = ImageOps.grayscale(image).convert("RGB")
    return image
