from __future__ import annotations

from src.ai.openrouter_client import OpenRouterClient
from src.ai.prompts import CLASSIFICATION_PROMPT_VERSION, CLASSIFICATION_SYSTEM_PROMPT, classification_schema
from src.models import ClassificationResult
from src.processing.json_parser import JSONParseError, parse_json_object


def classify_document(client: OpenRouterClient, image_bytes: bytes, mime_type: str) -> ClassificationResult:
    response = client.vision_json(
        image_bytes=image_bytes,
        mime_type=mime_type,
        system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
        schema_name="ktp_classification",
        schema=classification_schema(),
    )
    data = parse_json_object(response.content)
    required = {"is_ktp", "document_type", "confidence", "reason"}
    if not required.issubset(data):
        raise JSONParseError(f"Respons klasifikasi tidak lengkap: {sorted(required - set(data))}.")
    if not isinstance(data["is_ktp"], bool):
        raise JSONParseError("is_ktp harus boolean.")
    unexpected = sorted(set(data) - required)
    if unexpected:
        raise JSONParseError(f"Field klasifikasi tidak dikenal: {unexpected}.")
    result = ClassificationResult.from_dict(
        data,
        model=response.model,
        prompt_version=CLASSIFICATION_PROMPT_VERSION,
        duration_ms=response.duration_ms,
        usage=response.usage,
    )
    return result
