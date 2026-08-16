import io

import pandas as pd
import pytest
from PIL import Image

from src.processing.image_processor import ImageValidationError, validate_and_prepare_image
from src.services.analytics import export_columns, masked_history
from src.utils.security import mask_address, mask_date, mask_name, neutralize_csv_formula


def test_all_primary_pii_is_masked_in_history_and_default_export():
    frame = pd.DataFrame([{"id": 1, "nik": "3273011505900001", "nama": "BUDI SANTOSO",
                           "alamat": "JALAN RAHASIA", "tanggal_lahir": "1990-05-15",
                           "file_name": "=cmd.jpg", "document_type": "KTP_INDONESIA",
                           "jenis_kelamin": "LAKI-LAKI", "validation_status": "VALID", "uploaded_at": "now"}])
    masked = masked_history(frame)
    assert "nik" not in masked
    assert masked.iloc[0]["nama"] != "BUDI SANTOSO"
    assert masked.iloc[0]["alamat"] != "JALAN RAHASIA"
    assert masked.iloc[0]["tanggal_lahir"] == "**-**-1990"
    exported = export_columns(frame)
    assert exported.iloc[0]["file_name"].startswith("'")


@pytest.mark.parametrize("value", ["=1+1", "+SUM(A1:A2)", "-2+3", "@cmd"])
def test_csv_formula_prefixes_are_neutralized(value):
    assert neutralize_csv_formula(value).startswith("'")


def test_mask_helpers_do_not_return_original_values():
    assert mask_name("SITI AMINAH") != "SITI AMINAH"
    assert mask_address("JALAN CONTOH") != "JALAN CONTOH"
    assert mask_date("2001-02-03") == "**-**-2001"
    assert mask_date("03-02-2001") == "**-**-2001"


def test_excessive_pixel_count_is_rejected_before_resize():
    payload = io.BytesIO()
    Image.new("RGB", (1000, 1000), "white").save(payload, "PNG")
    with pytest.raises(ImageValidationError, match="piksel"):
        validate_and_prepare_image(payload.getvalue(), max_pixels=500_000)
