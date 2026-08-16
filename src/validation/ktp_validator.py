from __future__ import annotations

from src.models import ValidationResult, ValidationSummary
from src.utils.constants import RuleStatus
from src.validation.date_validator import parse_date
from src.validation.nik_validator import RegionReference, validate_nik


def validate_ktp(fields: dict[str, str | None], region_reference: RegionReference | None = None) -> ValidationSummary:
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
    return ValidationSummary.from_rules(rules, {
        "region_code": derived.region_code,
        "birth_date": derived.birth_date.isoformat() if derived.birth_date else None,
        "gender": derived.gender,
        "verification_scope": "FORMAT_ONLY_NOT_DUKCAPIL_VERIFICATION",
    })

