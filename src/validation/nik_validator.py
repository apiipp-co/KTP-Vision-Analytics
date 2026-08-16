from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.models import ValidationResult
from src.utils.constants import RuleStatus
from src.validation.date_validator import parse_date, resolve_two_digit_year


@dataclass
class NIKDerived:
    region_code: str | None = None
    birth_date: date | None = None
    gender: str | None = None


class RegionReference:
    """Loads an optional official Kemendagri CSV; no fabricated fallback mapping."""

    def __init__(self, csv_path: Path | str = "data/reference/kemendagri_regions.csv"):
        self.path = Path(csv_path)
        self.rows: dict[str, dict[str, str]] = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    code = "".join(ch for ch in str(row.get("code", "")) if ch.isdigit())
                    if len(code) == 6:
                        self.rows[code] = row

    @property
    def available(self) -> bool:
        return bool(self.rows)

    def get(self, code: str) -> dict[str, str] | None:
        return self.rows.get(code)


def derive_nik(nik: str | None, ocr_birth_date: str | None = None) -> NIKDerived:
    if not nik or len(nik) != 16 or not nik.isdigit():
        return NIKDerived()
    raw_day = int(nik[6:8])
    gender = "PEREMPUAN" if raw_day > 40 else "LAKI-LAKI"
    day = raw_day - 40 if raw_day > 40 else raw_day
    month = int(nik[8:10])
    year = int(nik[10:12])
    parsed_ocr = parse_date(ocr_birth_date)
    derived_date = None
    if parsed_ocr and parsed_ocr.year % 100 == year:
        try:
            candidate = date(parsed_ocr.year, month, day)
            if candidate <= date.today():
                derived_date = candidate
        except ValueError:
            pass
    if derived_date is None:
        derived_date = resolve_two_digit_year(year, month, day)
    return NIKDerived(region_code=nik[:6], birth_date=derived_date, gender=gender)


def validate_nik(nik: str | None, tanggal_lahir: str | None, jenis_kelamin: str | None, region_reference: RegionReference | None = None) -> tuple[list[ValidationResult], NIKDerived]:
    nik = nik or ""
    if nik:
        rules = [
            ValidationResult("nik_required", RuleStatus.VALID.value, "NIK tersedia.", critical=True),
            ValidationResult("nik_numeric", RuleStatus.VALID.value if nik.isdigit() else RuleStatus.INVALID.value,
                             "NIK hanya terdiri dari digit." if nik.isdigit() else "NIK harus hanya terdiri dari digit.", critical=True),
            ValidationResult("nik_length", RuleStatus.VALID.value if len(nik) == 16 else RuleStatus.INVALID.value,
                             "NIK memiliki 16 digit." if len(nik) == 16 else f"Panjang NIK {len(nik)}; seharusnya 16 digit.", critical=True),
        ]
    else:
        rules = [
            ValidationResult("nik_required", RuleStatus.NOT_CHECKED.value, "NIK tidak terbaca; perlu review.", critical=True),
            ValidationResult("nik_numeric", RuleStatus.NOT_CHECKED.value, "NIK tidak tersedia untuk pemeriksaan numeric.", critical=True),
            ValidationResult("nik_length", RuleStatus.NOT_CHECKED.value, "NIK tidak tersedia untuk pemeriksaan panjang.", critical=True),
        ]
    derived = derive_nik(nik, tanggal_lahir)
    structurally_ready = len(nik) == 16 and nik.isdigit()
    if not structurally_ready:
        rules.extend([
            ValidationResult("nik_birth_date", RuleStatus.NOT_CHECKED.value, "Struktur tanggal NIK tidak dapat diperiksa.", critical=True),
            ValidationResult("birth_date_consistency", RuleStatus.NOT_CHECKED.value, "Konsistensi tanggal belum dapat diperiksa.", critical=True),
            ValidationResult("gender_consistency", RuleStatus.NOT_CHECKED.value, "Konsistensi gender belum dapat diperiksa.", critical=True),
            ValidationResult("region_code", RuleStatus.NOT_CHECKED.value, "Kode wilayah belum dapat diperiksa.", critical=False),
        ])
        return rules, derived

    if derived.birth_date:
        rules.append(ValidationResult("nik_birth_date", RuleStatus.VALID.value, "Bagian tanggal lahir NIK membentuk tanggal kalender valid.",
                                      actual_value=derived.birth_date.isoformat(), critical=True))
    else:
        rules.append(ValidationResult("nik_birth_date", RuleStatus.INVALID.value, "Bagian tanggal lahir NIK bukan tanggal kalender valid.", critical=True))

    ocr_date = parse_date(tanggal_lahir)
    if not tanggal_lahir or not ocr_date or not derived.birth_date:
        rules.append(ValidationResult("birth_date_consistency", RuleStatus.NOT_CHECKED.value,
                                      "Tanggal lahir OCR tidak tersedia/valid untuk dibandingkan.", critical=True))
    else:
        matched = ocr_date == derived.birth_date
        rules.append(ValidationResult("birth_date_consistency", RuleStatus.VALID.value if matched else RuleStatus.INVALID.value,
                                      "Tanggal lahir konsisten dengan struktur NIK." if matched else "Tanggal lahir pada KTP tidak konsisten dengan struktur NIK.",
                                      actual_value=ocr_date.isoformat(), expected_value=derived.birth_date.isoformat(), critical=True))

    if not jenis_kelamin or not derived.gender:
        rules.append(ValidationResult("gender_consistency", RuleStatus.NOT_CHECKED.value, "Jenis kelamin OCR tidak tersedia.", critical=True))
    else:
        matched = jenis_kelamin == derived.gender
        rules.append(ValidationResult("gender_consistency", RuleStatus.VALID.value if matched else RuleStatus.INVALID.value,
                                      "Jenis kelamin konsisten dengan struktur NIK." if matched else "Jenis kelamin tidak konsisten dengan struktur NIK.",
                                      actual_value=jenis_kelamin, expected_value=derived.gender, critical=True))

    reference = region_reference or RegionReference()
    if not reference.available:
        rules.append(ValidationResult("region_code", RuleStatus.NOT_CHECKED.value,
                                      "Dataset kode wilayah resmi belum diimpor; tidak menggunakan mapping buatan.", critical=False))
    else:
        found = reference.get(nik[:6])
        rules.append(ValidationResult("region_code", RuleStatus.VALID.value if found else RuleStatus.INVALID.value,
                                      "Kode kecamatan ditemukan pada referensi resmi." if found else "Kode kecamatan tidak ditemukan pada referensi resmi.",
                                      actual_value=nik[:6], critical=True))
    return rules, derived
