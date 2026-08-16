import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError


class ImageValidationError(ValueError):
    pass


@dataclass
class ProcessedImage:
    content: bytes
    mime_type: str
    width: int
    height: int
    original_size: int


def validate_and_prepare_image(content: bytes, max_size_mb: int = 10, max_dimension: int = 2400,
                               max_pixels: int = 20_000_000) -> ProcessedImage:
    if not content:
        raise ImageValidationError("File gambar kosong.")
    if len(content) > max_size_mb * 1024 * 1024:
        raise ImageValidationError(f"Ukuran file melebihi batas {max_size_mb} MB.")
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.verify()
        with Image.open(io.BytesIO(content)) as source:
            original_format = source.format
            if source.width * source.height > max_pixels:
                raise ImageValidationError(f"Resolusi gambar melebihi batas aman {max_pixels:,} piksel.")
            source = ImageOps.exif_transpose(source)
            if original_format not in {"JPEG", "PNG"}:
                raise ImageValidationError("Format gambar harus JPG, JPEG, atau PNG.")
            source = source.convert("RGB")
            if source.width < 160 or source.height < 100:
                raise ImageValidationError("Resolusi gambar terlalu kecil untuk dianalisis.")
            source.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            source.save(output, format="JPEG", quality=90, optimize=True)
            return ProcessedImage(output.getvalue(), "image/jpeg", source.width, source.height, len(content))
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise ImageValidationError("File tidak dapat dibaca sebagai gambar yang valid.") from exc
