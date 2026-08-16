import pytest

from src.processing.json_parser import JSONParseError, parse_json_object, validate_ocr_payload


def test_parses_json_and_defensive_code_fence():
    assert parse_json_object('{"a": 1}') == {"a": 1}
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}


def test_rejects_malformed_json():
    with pytest.raises(JSONParseError):
        parse_json_object('{"a":')


def test_rejects_empty_response():
    with pytest.raises(JSONParseError, match="kosong"):
        parse_json_object("  ")


def test_missing_ocr_values_become_null_and_are_reported():
    fields, metadata = validate_ocr_payload({"nik": " "})
    assert fields["nik"] is None
    assert "nik" in metadata["fields_missing"]
    assert metadata["parse_status"] == "SUCCESS"


def test_explicit_null_field_is_preserved():
    fields, metadata = validate_ocr_payload({"nik": None, "ocr_metadata": {"fields_missing": ["nik"], "parse_status": "MODEL"}})
    assert fields["nik"] is None
    assert "nik" in metadata["fields_missing"]


def test_rejects_unexpected_field():
    with pytest.raises(JSONParseError, match="tidak dikenal"):
        validate_ocr_payload({"nik": "123", "unexpected": "value"})


def test_rejects_invalid_metadata_shape():
    with pytest.raises(JSONParseError):
        validate_ocr_payload({"ocr_metadata": {"fields_missing": "nik", "parse_status": "MODEL"}})
