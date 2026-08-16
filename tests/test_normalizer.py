from src.processing.normalizer import clean_text, normalize_date, normalize_fields


def test_whitespace_null_and_date_normalization():
    assert clean_text("  Budi   Uji ") == "Budi Uji"
    assert clean_text("null") is None
    assert normalize_date("01/02/2000") == "2000-02-01"


def test_categories_nik_and_rt_normalization():
    fields, audit = normalize_fields({
        "nik": " 1234 5678 ", "jenis_kelamin": "laki laki", "kewarganegaraan": "warga negara indonesia",
        "berlaku_hingga": "seumurhidup", "rt": "1", "rw": "02",
    })
    assert fields["nik"] == "12345678"
    assert fields["jenis_kelamin"] == "LAKI-LAKI"
    assert fields["kewarganegaraan"] == "WNI"
    assert fields["berlaku_hingga"] == "SEUMUR HIDUP"
    assert fields["rt"] == "001" and fields["rw"] == "002"
    assert audit["nik"]["raw_value"] == "1234 5678"


def test_nik_leading_zero_and_meaning_are_preserved():
    fields, _ = normalize_fields({"nik": "0012 3456 7890 1234", "nama": "Mc Donald"})
    assert fields["nik"] == "0012345678901234"
    assert isinstance(fields["nik"], str)
    assert fields["nama"] == "Mc Donald"


def test_null_ocr_result_remains_null():
    fields, audit = normalize_fields({})
    assert all(value is None for value in fields.values())
    assert all(item["raw_value"] is None for item in audit.values())
