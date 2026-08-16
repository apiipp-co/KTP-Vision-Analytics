import io

import pytest
from PIL import Image

from src.processing.image_processor import ImageValidationError, validate_and_prepare_image


def image_bytes(size=(400, 240)):
    output = io.BytesIO()
    Image.new("RGB", size, "white").save(output, "PNG")
    return output.getvalue()


def test_valid_image_is_prepared_as_jpeg():
    result = validate_and_prepare_image(image_bytes())
    assert result.mime_type == "image/jpeg"
    assert result.width == 400


def test_invalid_and_tiny_images_are_rejected():
    with pytest.raises(ImageValidationError):
        validate_and_prepare_image(b"not an image")
    with pytest.raises(ImageValidationError):
        validate_and_prepare_image(image_bytes((50, 50)))


def test_oversized_file_is_rejected_before_decode():
    with pytest.raises(ImageValidationError, match="melebihi"):
        validate_and_prepare_image(b"x" * (1024 * 1024 + 1), max_size_mb=1)


def test_all_twenty_synthetic_fixtures_are_valid_images():
    from pathlib import Path

    fixtures = sorted(Path("data/testing/ktp").glob("*.jpg")) + sorted(Path("data/testing/non_ktp").glob("*.jpg"))
    assert len(fixtures) == 20
    for fixture in fixtures:
        result = validate_and_prepare_image(fixture.read_bytes())
        assert result.width >= 160 and result.height >= 100
