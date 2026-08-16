from __future__ import annotations

from datetime import date

from src.models import ValidationResult, ValidationSummary
from src.utils.constants import RuleStatus
from src.validation.date_validator import parse_date
from src.validation.nik_validator import RegionReference, validate_nik


def validate_ktp(
    fields: dict[str, str | None],
    region_reference: RegionReference | None = None,
    reference_date: date | None = None,
) -> ValidationSummary:
    rules, derived = validate_nik(fields.get("nik"), fields.get("tanggal_lahir"), fields.get("jenis_kelamin"), region_reference)
    birth = fields.get("tanggal_lahir")
    if not birth:
        rules.append(ValidationResult("birth_date_format", RuleStatus.NOT_CHECKED.value, "Tanggal lahir tidak terbaca."))
    else:
        valid = parse_date(birth) is not None
        rules.append(ValidationResult("birth_date_format", RuleStatus.VALID.value if valid else RuleStatus.INVALID.value,
                                      "Tanggal lahir valid." if valid else "Format/nilai tanggal lahir tidak valid."))
    for name, label in (("nama", "Nama"), ("alamat", "Alamat")):
        value = fields.get(name)
        rules.append(ValidationResult(f"{name}_available", RuleStatus.VALID.value if value else RuleStatus.NOT_CHECKED.value,
                                      f"{label} tersedia." if value else f"{label} tidak terbaca."))
    gender = fields.get("jenis_kelamin")
    if not gender:
        status, message = RuleStatus.NOT_CHECKED.value, "Jenis kelamin tidak terbaca."
    elif gender in {"LAKI-LAKI", "PEREMPUAN"}:
        status, message = RuleStatus.VALID.value, "Kategori jenis kelamin didukung."
    else:
        status, message = RuleStatus.INVALID.value, "Kategori jenis kelamin tidak didukung."
    rules.append(ValidationResult("gender_category", status, message))
    citizenship = fields.get("kewarganegaraan")
    if not citizenship:
        rules.append(ValidationResult("citizenship_category", RuleStatus.NOT_CHECKED.value, "Kewarganegaraan tidak terbaca."))
    else:
        supported = citizenship in {"WNI", "WNA"}
        rules.append(ValidationResult("citizenship_category", RuleStatus.VALID.value if supported else RuleStatus.INVALID.value,
                                      "Kategori kewarganegaraan didukung." if supported else "Kategori kewarganegaraan tidak dikenali."))
    validity = fields.get("berlaku_hingga")
    today = reference_date or date.today()
    if not validity:
        rules.append(ValidationResult(
            "validity_status", RuleStatus.NOT_CHECKED.value,
            "Masa berlaku tidak terbaca; perlu review.", critical=True,
        ))
    elif validity == "SEUMUR HIDUP":
        rules.append(ValidationResult(
            "validity_status", RuleStatus.VALID.value,
            "KTP berlaku seumur hidup.", actual_value=validity, critical=True,
        ))
    else:
        expiry_date = parse_date(validity)
        if expiry_date is None:
            rules.append(ValidationResult(
                "validity_status", RuleStatus.INVALID.value,
                "Format masa berlaku tidak valid.", actual_value=validity,
                expected_value="SEUMUR HIDUP atau tanggal valid", critical=True,
            ))
        elif expiry_date < today:
            rules.append(ValidationResult(
                "validity_status", RuleStatus.INVALID.value,
                "Masa berlaku KTP telah berakhir.", actual_value=expiry_date.isoformat(),
                expected_value=f">= {today.isoformat()}", critical=True,
            ))
        else:
            rules.append(ValidationResult(
                "validity_status", RuleStatus.VALID.value,
                "Masa berlaku KTP masih aktif.", actual_value=expiry_date.isoformat(),
                expected_value=f">= {today.isoformat()}", critical=True,
            ))
    return ValidationSummary.from_rules(rules, {
        "region_code": derived.region_code,
        "birth_date": derived.birth_date.isoformat() if derived.birth_date else None,
        "gender": derived.gender,
        "valid_until": validity,
        "verification_scope": "FORMAT_ONLY_NOT_DUKCAPIL_VERIFICATION",
    })
