"""Image transforms: resize, rotate, crop, adjustments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from inyfinn_resizer.core.job import ResizeMode, ResizeOptions, TransformOptions

if TYPE_CHECKING:
    import pyvips


def _kernel(name: str):
    import pyvips
    mapping = {
        "lanczos3": pyvips.Kernel.LANCZOS3,
        "lanczos2": pyvips.Kernel.LANCZOS2,
        "cubic": pyvips.Kernel.CUBIC,
        "linear": pyvips.Kernel.LINEAR,
        "nearest": pyvips.Kernel.NEAREST,
    }
    return mapping.get(name.lower(), pyvips.Kernel.LANCZOS3)


def apply_resize(image: "pyvips.Image", opts: ResizeOptions) -> "pyvips.Image":
    if opts.mode == ResizeMode.CROP_SMART:
        return _crop_smart(image, opts.box_w, opts.box_h, opts.smart_margin)
    if opts.mode == ResizeMode.FIT_BOX:
        return _fit_box_cover(image, opts.box_w, opts.box_h)

    if opts.mode == ResizeMode.NONE:
        return image

    w, h = image.width, image.height
    if opts.skip_if_smaller and opts.mode == ResizeMode.ONE_SIDE:
        if opts.side == "width" and w <= opts.dimension:
            return image
        if opts.side == "height" and h <= opts.dimension:
            return image
        if opts.side == "longer" and max(w, h) <= opts.dimension:
            return image
        if opts.side == "shorter" and min(w, h) <= opts.dimension:
            return image

    kernel = _kernel(opts.filter_name)

    if opts.mode == ResizeMode.PERCENT:
        scale = max(1, opts.percent) / 100.0
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))
        return image.resize(nw / w, vscale=nh / h, kernel=kernel)

    if opts.mode == ResizeMode.PIXELS:
        nw = opts.width or w
        nh = opts.height or h
        if opts.preserve_aspect:
            scale = min(nw / w, nh / h)
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return image.resize(nw / w, vscale=nh / h, kernel=kernel)

    if opts.mode == ResizeMode.MAX_DIMENSION:
        dim = opts.dimension
        if max(w, h) <= dim:
            return image
        scale = dim / max(w, h)
        return image.resize(scale, kernel=kernel)

    if opts.mode == ResizeMode.ONE_SIDE:
        dim = opts.dimension
        if opts.side == "width":
            if w == dim:
                return image
            scale = dim / w
        elif opts.side == "height":
            if h == dim:
                return image
            scale = dim / h
        elif opts.side == "longer":
            scale = dim / max(w, h)
        else:  # shorter
            scale = dim / min(w, h)
        return image.resize(scale, kernel=kernel)

    return image


def apply_scale_postprocess(image: "pyvips.Image", opts: ResizeOptions) -> "pyvips.Image":
    """Skala procentowa i opcjonalne minimum najdłuższej krawędzi (po presecie wymiarów)."""
    kernel = _kernel(opts.filter_name)
    pct = max(1.0, min(100.0, float(opts.scale_percent)))
    if pct != 100.0:
        scale = pct / 100.0
        image = image.resize(scale, kernel=kernel)
    if opts.min_longest_enabled and opts.min_longest_px > 0:
        w, h = image.width, image.height
        longest = max(w, h)
        if longest < opts.min_longest_px:
            scale = opts.min_longest_px / longest
            image = image.resize(scale, kernel=kernel)
    return image


def _content_bbox(image: "pyvips.Image", margin: int = 0) -> tuple[int, int, int, int]:
    w, h = image.width, image.height
    if not image.hasalpha():
        return 0, 0, w, h

    scale = min(1.0, 640 / max(w, h))
    probe = image.resize(scale) if scale < 1.0 else image
    pw, ph = probe.width, probe.height
    bands = probe.bands
    mem = probe.write_to_memory()
    left, top, right, bottom = pw, ph, -1, -1
    for y in range(ph):
        row_base = y * pw * bands
        for x in range(pw):
            a = mem[row_base + x * bands + 3] if bands >= 4 else 255
            if a > 12:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    if right < left or bottom < top:
        return 0, 0, w, h

    inv = (1.0 / scale) if scale < 1.0 else 1.0
    x0 = max(0, int(left * inv) - margin)
    y0 = max(0, int(top * inv) - margin)
    x1 = min(w, int((right + 1) * inv) + margin)
    y1 = min(h, int((bottom + 1) * inv) + margin)
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def _fit_cover_crop(image: "pyvips.Image", target_w: int, target_h: int) -> "pyvips.Image":
    kernel = _kernel("lanczos3")
    w, h = image.width, image.height
    if w <= 0 or h <= 0:
        return image
    scale = max(target_w / w, target_h / h)
    scaled = image.resize(scale, kernel=kernel)
    sw, sh = scaled.width, scaled.height
    left = max(0, (sw - target_w) // 2)
    top = max(0, (sh - target_h) // 2)
    crop_w = min(target_w, sw - left)
    crop_h = min(target_h, sh - top)
    cropped = scaled.crop(left, top, crop_w, crop_h)
    if crop_w != target_w or crop_h != target_h:
        cropped = cropped.resize(target_w / crop_w, vscale=target_h / crop_h, kernel=kernel)
    return cropped


def _crop_smart(image: "pyvips.Image", target_w: int, target_h: int, margin: int) -> "pyvips.Image":
    if target_w <= 0 or target_h <= 0:
        return image
    x, y, cw, ch = _content_bbox(image, margin)
    has_transparency = image.hasalpha() and (x > 0 or y > 0 or cw < image.width or ch < image.height)
    if has_transparency:
        work = image.crop(x, y, cw, ch)
    else:
        work = image
    return _fit_cover_crop(work, target_w, target_h)


def _fit_box_cover(image: "pyvips.Image", box_w: int, box_h: int) -> "pyvips.Image":
    return _fit_cover_crop(image, box_w, box_h)


def apply_transforms(image: "pyvips.Image", opts: TransformOptions) -> "pyvips.Image":
    if opts.trim_transparent and image.hasalpha():
        try:
            left, top, w, h = image.find_trim(threshold=10, background=[0, 0, 0, 0])
            margin = max(0, opts.trim_margin)
            left = max(0, left - margin)
            top = max(0, top - margin)
            w = min(image.width - left, w + 2 * margin)
            h = min(image.height - top, h + 2 * margin)
            image = image.crop(left, top, w, h)
        except Exception:
            pass

    if opts.flip_h:
        image = image.fliphor()
    if opts.flip_v:
        image = image.flipver()

    angle = opts.rotate % 360
    if angle == 90:
        image = image.rot90()
    elif angle == 180:
        image = image.rot180()
    elif angle == 270:
        image = image.rot270()

    if opts.crop_w > 0 and opts.crop_h > 0:
        image = image.crop(opts.crop_x, opts.crop_y, opts.crop_w, opts.crop_h)

    if opts.grayscale:
        image = image.colourspace("b-w")
    elif opts.sepia:
        image = image.colourspace("srgb")
        matrix = [
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131],
        ]
        image = image.recomb(matrix)

    if abs(opts.brightness - 1.0) > 0.01 or abs(opts.contrast - 1.0) > 0.01:
        image = (image * opts.contrast) + int((opts.brightness - 1.0) * 128)

    if abs(opts.saturation - 1.0) > 0.01:
        image = image.colourspace("srgb")
        image = image.linear([opts.saturation, opts.saturation, opts.saturation], [0, 0, 0])

    return image
