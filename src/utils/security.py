from __future__ import annotations

import hashlib
import re
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def mask_nik(nik: str | None) -> str:
    digits = "".join(ch for ch in (nik or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) <= 6:
        return "*" * len(digits)
    return f"{digits[:4]}{'*' * max(len(digits) - 8, 4)}{digits[-4:]}"


def mask_name(value: str | None) -> str:
    parts = str(value or "").strip().split()
    return " ".join(part[:1] + "*" * max(len(part) - 1, 2) for part in parts)


def mask_address(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return f"{text[:6]}… [masked]" if len(text) > 6 else "[masked]"


def mask_date(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    iso = re.fullmatch(r"(\d{4})[-/]\d{1,2}[-/]\d{1,2}", text)
    local = re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/](\d{4})", text)
    year = iso.group(1) if iso else local.group(1) if local else "****"
    return f"**-**-{year}"


def mask_identity_field(field_name: str, value: str | None) -> str:
    if field_name == "nik":
        return mask_nik(value)
    if field_name == "nama":
        return mask_name(value)
    if field_name in {"alamat", "tempat_lahir", "kelurahan_desa", "kecamatan", "kabupaten_kota"}:
        return mask_address(value)
    if field_name in {"tanggal_lahir", "berlaku_hingga"}:
        return mask_date(value)
    return str(value or "")


def neutralize_csv_formula(value: object) -> object:
    """Prevent spreadsheet applications from evaluating untrusted text as a formula."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def safe_csv_frame(frame):
    return frame.map(neutralize_csv_formula) if hasattr(frame, "map") else frame.applymap(neutralize_csv_formula)


def safe_filename(filename: str) -> str:
    base = Path(filename or "upload").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return cleaned[:120] or "upload"
