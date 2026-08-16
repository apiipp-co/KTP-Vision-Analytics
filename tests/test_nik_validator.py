from datetime import date

from src.validation.ktp_validator import validate_ktp
from src.validation.nik_validator import RegionReference, derive_nik, validate_nik


def by_name(rules):
    return {rule.rule: rule for rule in rules}


def test_valid_16_digit_male_structure_and_consistency():
    nik = "3273011505900001"
    rules, derived = validate_nik(nik, "1990-05-15", "LAKI-LAKI")
    indexed = by_name(rules)
    assert indexed["nik_length"].status == "VALID"
    assert indexed["nik_numeric"].status == "VALID"
    assert indexed["nik_birth_date"].status == "VALID"
    assert indexed["birth_date_consistency"].status == "VALID"
    assert indexed["gender_consistency"].status == "VALID"
    assert derived.birth_date.isoformat() == "1990-05-15"


def test_female_day_plus_40_and_gender_mismatch():
    nik = "3273015505900001"
    assert derive_nik(nik, "1990-05-15").gender == "PEREMPUAN"
    rules, _ = validate_nik(nik, "1990-05-15", "LAKI-LAKI")
    assert by_name(rules)["gender_consistency"].status == "INVALID"


def test_short_long_alpha_and_impossible_date():
    for nik in ("123", "1" * 17, "32730115059000AB"):
        rules, _ = validate_nik(nik, None, None)
        assert by_name(rules)["nik_length"].status == "INVALID" or by_name(rules)["nik_numeric"].status == "INVALID"
    rules, _ = validate_nik("3273013102900001", "1990-02-28", "LAKI-LAKI")
    assert by_name(rules)["nik_birth_date"].status == "INVALID"


def test_overall_review_when_critical_field_missing_and_invalid_on_clear_failure():
    review = validate_ktp({"nik": "3273011505900001", "tanggal_lahir": None, "jenis_kelamin": None})
    assert review.status == "REVIEW_REQUIRED"
    invalid = validate_ktp({"nik": "123", "tanggal_lahir": "bad", "jenis_kelamin": "X"})
    assert invalid.status == "INVALID"


def test_missing_nik_requires_review_instead_of_false_invalid():
    result = validate_ktp({"nik": None, "tanggal_lahir": None, "jenis_kelamin": None})
    assert result.status == "REVIEW_REQUIRED"
    assert by_name(result.rules)["nik_required"].status == "NOT_CHECKED"


def test_invalid_month_is_rejected():
    rules, _ = validate_nik("3273011513900001", "1990-05-15", "LAKI-LAKI")
    assert by_name(rules)["nik_birth_date"].status == "INVALID"


def test_date_mismatch_is_invalid():
    rules, _ = validate_nik("3273011505900001", "1990-05-16", "LAKI-LAKI")
    assert by_name(rules)["birth_date_consistency"].status == "INVALID"


def test_missing_gender_requires_review():
    result = validate_ktp({"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": None})
    assert result.status == "REVIEW_REQUIRED"
    assert by_name(result.rules)["gender_consistency"].status == "NOT_CHECKED"


def test_official_reference_miss_is_critical_when_reference_is_loaded(tmp_path):
    reference_file = tmp_path / "regions.csv"
    reference_file.write_text("code,province,regency,subdistrict\n327302,JAWA BARAT,KOTA CONTOH,KECAMATAN CONTOH\n", encoding="utf-8")
    result = validate_ktp(
        {"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": "LAKI-LAKI"},
        RegionReference(reference_file),
    )
    assert result.status == "INVALID"
    assert by_name(result.rules)["region_code"].critical is True


def test_lifetime_validity_is_valid():
    result = validate_ktp(
        {"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": "LAKI-LAKI",
         "berlaku_hingga": "SEUMUR HIDUP"},
        reference_date=date(2026, 8, 17),
    )
    assert by_name(result.rules)["validity_status"].status == "VALID"
    assert result.status == "VALID"


def test_future_and_current_expiry_are_valid():
    for value in ("2026-08-17", "31-12-2030"):
        result = validate_ktp(
            {"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": "LAKI-LAKI",
             "berlaku_hingga": value},
            reference_date=date(2026, 8, 17),
        )
        assert by_name(result.rules)["validity_status"].status == "VALID"


def test_expired_or_malformed_validity_is_invalid():
    for value in ("2020-01-01", "TIDAK JELAS"):
        result = validate_ktp(
            {"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": "LAKI-LAKI",
             "berlaku_hingga": value},
            reference_date=date(2026, 8, 17),
        )
        assert by_name(result.rules)["validity_status"].status == "INVALID"
        assert result.status == "INVALID"


def test_missing_validity_requires_review():
    result = validate_ktp(
        {"nik": "3273011505900001", "tanggal_lahir": "1990-05-15", "jenis_kelamin": "LAKI-LAKI"},
        reference_date=date(2026, 8, 17),
    )
    assert by_name(result.rules)["validity_status"].status == "NOT_CHECKED"
    assert result.status == "REVIEW_REQUIRED"
