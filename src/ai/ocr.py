from __future__ import annotations

from datetime import datetime, timezone

from src.ai.openrouter_client import OpenRouterClient
from src.ai.prompts import OCR_PROMPT_VERSION, OCR_SYSTEM_PROMPT, ocr_schema
from src.models import OCRResult
from src.processing.json_parser import parse_json_object, validate_ocr_payload


def extract_ktp(client: OpenRouterClient, image_bytes: bytes, mime_type: str) -> OCRResult:
    response = client.vision_json(
        image_bytes=image_bytes,
        mime_type=mime_type,
        system_prompt=OCR_SYSTEM_PROMPT,
        schema_name="ktp_ocr_extraction",
        schema=ocr_schema(),
    )
    data = parse_json_object(response.content)
    fields, metadata = validate_ocr_payload(data)
    metadata.update({
        "model": response.model,
        "prompt_version": OCR_PROMPT_VERSION,
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": response.duration_ms,
        "usage": response.usage,
        "request_id": response.request_id,
    })
    return OCRResult(fields=fields, metadata=metadata, raw_response=response.content)

