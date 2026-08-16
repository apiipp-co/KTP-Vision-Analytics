from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Any

from src.utils.constants import IDENTITY_FIELDS


NULL_LIKE = {"", "-", "null", "none", "n/a", "tidak terbaca"}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return None if text.lower() in NULL_LIKE else text


def normalize_date(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    normalized = text.replace("/", "-").replace(".", "-")
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y"):
        try:
            return datetime.strptime(normalized, fmt).date().isoformat()
        except ValueError:
            pass
    return text


def normalize_category(value: Any, aliases: dict[str, str]) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    key = unicodedata.normalize("NFKC", text).upper().replace("_", " ")
    key = " ".join(key.split())
    return aliases.get(key, key)


def normalize_fields(fields: dict[str, Any]) -> tuple[dict[str, str | None], dict[str, dict[str, str | None]]]:
    normalized = {name: clean_text(fields.get(name)) for name in IDENTITY_FIELDS}
    if normalized["nik"]:
        normalized["nik"] = "".join(normalized["nik"].split())
    normalized["tanggal_lahir"] = normalize_date(normalized["tanggal_lahir"])
    normalized["jenis_kelamin"] = normalize_category(normalized["jenis_kelamin"], {
        "LAKI LAKI": "LAKI-LAKI", "LAKI-LAKI": "LAKI-LAKI", "L": "LAKI-LAKI",
        "PRIA": "LAKI-LAKI", "PEREMPUAN": "PEREMPUAN", "P": "PEREMPUAN", "WANITA": "PEREMPUAN",
    })
    normalized["kewarganegaraan"] = normalize_category(normalized["kewarganegaraan"], {
        "WARGA NEGARA INDONESIA": "WNI", "WNI": "WNI", "WARGA NEGARA ASING": "WNA", "WNA": "WNA",
    })
    normalized["berlaku_hingga"] = normalize_category(normalized["berlaku_hingga"], {
        "SEUMURHIDUP": "SEUMUR HIDUP", "SEUMUR HIDUP": "SEUMUR HIDUP",
    })
    for part in ("rt", "rw"):
        value = normalized[part]
        if value and value.isdigit():
            normalized[part] = value.zfill(3)
    audit = {
        name: {"raw_value": clean_text(fields.get(name)), "normalized_value": normalized[name]}
        for name in IDENTITY_FIELDS
    }
    return normalized, audit
