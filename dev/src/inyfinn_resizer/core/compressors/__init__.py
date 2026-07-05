from inyfinn_resizer.core.compressors.external import compress_avif_avifenc, compress_webp_cwebp, optimize_png_oxipng
from inyfinn_resizer.core.compressors.gif import compress_gif
from inyfinn_resizer.core.compressors.jpeg import compress_jpeg_file
from inyfinn_resizer.core.compressors.png import apply_pngquant

__all__ = [
    "apply_pngquant",
    "compress_avif_avifenc",
    "compress_gif",
    "compress_jpeg_file",
    "compress_webp_cwebp",
    "optimize_png_oxipng",
]
