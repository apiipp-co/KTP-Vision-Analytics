from __future__ import annotations

import json
from typing import Any

from src.utils.constants import IDENTITY_FIELDS


class JSONParseError(ValueError):
    pass


def parse_json_object(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise JSONParseError("Respons AI kosong.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise JSONParseError(f"Respons AI bukan JSON valid: {exc.msg}.") from exc
    if not isinstance(parsed, dict):
        raise JSONParseError("Root respons AI harus berupa object JSON.")
    return parsed


def validate_ocr_payload(data: dict[str, Any]) -> tuple[dict[str, str | None], dict[str, Any]]:
    allowed = {*IDENTITY_FIELDS, "ocr_metadata"}
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise JSONParseError(f"Field OCR tidak dikenal: {unexpected}.")
    fields: dict[str, str | None] = {}
    for name in IDENTITY_FIELDS:
        value = data.get(name)
        if value is not None and not isinstance(value, str):
            raise JSONParseError(f"Field {name} harus string atau null.")
        fields[name] = value.strip() if isinstance(value, str) and value.strip() else None
    metadata = data.get("ocr_metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise JSONParseError("ocr_metadata harus berupa object.")
    metadata_unexpected = sorted(set(metadata) - {"fields_missing", "parse_status"})
    if metadata_unexpected:
        raise JSONParseError(f"Field ocr_metadata tidak dikenal: {metadata_unexpected}.")
    if "fields_missing" in metadata and not isinstance(metadata["fields_missing"], list):
        raise JSONParseError("ocr_metadata.fields_missing harus berupa array.")
    if "parse_status" in metadata and not isinstance(metadata["parse_status"], str):
        raise JSONParseError("ocr_metadata.parse_status harus berupa string.")
    missing = [name for name, value in fields.items() if value is None]
    metadata = {**metadata, "fields_missing": missing, "parse_status": "SUCCESS"}
    return fields, metadata
