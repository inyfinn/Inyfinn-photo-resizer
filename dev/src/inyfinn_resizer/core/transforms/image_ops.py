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
    if opts.mode == ResizeMode.NONE:
        return image

    w, h = image.width, image.height
    if opts.skip_if_smaller and opts.mode == ResizeMode.ONE_SIDE:
        if opts.side == "width" and w <= opts.dimension:
            return image
        if opts.side == "height" and h <= opts.dimension:
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


def apply_transforms(image: "pyvips.Image", opts: TransformOptions) -> "pyvips.Image":
    import pyvips

    if opts.auto_rotate_exif:
        try:
            image = pyvips.Image.new_from_file  # noqa: B018 — placeholder
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
