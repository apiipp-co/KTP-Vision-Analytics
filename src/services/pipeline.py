from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from src.ai.classifier import classify_document
from src.ai.ocr import extract_ktp
from src.ai.openrouter_client import OpenRouterClient
from src.ai.prompts import OCR_PROMPT_VERSION
from src.database.repository import DocumentRepository
from src.models import ClassificationResult, ValidationResult, ValidationSummary
from src.processing.image_processor import ProcessedImage, validate_and_prepare_image
from src.processing.json_parser import JSONParseError
from src.processing.normalizer import normalize_fields
from src.utils.constants import DocumentType, IDENTITY_FIELDS, RuleStatus
from src.utils.security import safe_filename, sha256_bytes
from src.validation.ktp_validator import validate_ktp


ProgressCallback = Callable[[str, float], None]


@dataclass
class PipelineResult:
    request_id: str
    document_id: int | None
    document_hash: str
    duplicate: dict[str, Any] | None
    image: ProcessedImage
    classification: ClassificationResult
    fields: dict[str, str | None] = field(default_factory=dict)
    audit: dict[str, dict[str, str | None]] = field(default_factory=dict)
    validation: ValidationSummary = field(default_factory=ValidationSummary)
    metadata: dict[str, Any] = field(default_factory=dict)
    stopped_after_classification: bool = False


class DocumentPipeline:
    def __init__(self, client: OpenRouterClient, repository: DocumentRepository, max_image_size_mb: int = 10,
                 max_image_pixels: int = 20_000_000, data_context: str = "PRODUCTION"):
        self.client = client
        self.repository = repository
        self.max_image_size_mb = max_image_size_mb
        self.max_image_pixels = max_image_pixels
        self.data_context = data_context if data_context in {"PRODUCTION", "EVALUATION"} else "PRODUCTION"

    def process(self, file_name: str, content: bytes, progress: ProgressCallback | None = None) -> PipelineResult:
        notify = progress or (lambda _message, _value: None)
        started = time.monotonic()
        request_id = str(uuid.uuid4())
        notify("Memvalidasi gambar", 0.08)
        image = validate_and_prepare_image(content, self.max_image_size_mb, max_pixels=self.max_image_pixels)
        document_hash = sha256_bytes(content)
        duplicate = self.repository.find_duplicate(document_hash)

        notify("Mengklasifikasikan dokumen", 0.25)
        classification = classify_document(self.client, image.content, image.mime_type)
        if not classification.is_ktp:
            if classification.document_type == DocumentType.UNCERTAIN.value:
                validation = ValidationSummary(
                    status="REVIEW_REQUIRED",
                    rules=[ValidationResult("classification_uncertain", RuleStatus.NOT_CHECKED.value,
                                            "Model tidak memiliki bukti cukup untuk klasifikasi.", critical=True)],
                )
            else:
                validation = ValidationSummary(status="NOT_APPLICABLE", rules=[], derived={})
            total_ms = round((time.monotonic() - started) * 1000)
            metadata = {
                "request_id": request_id, "data_context": self.data_context,
                "total_duration_ms": total_ms,
                "usage": classification.usage,
                "ocr_model": None,
                "ocr_prompt_version": None,
                "ocr_duration_ms": None,
            }
            notify("Menyimpan hasil klasifikasi", 0.9)
            document_id = self.repository.save(
                safe_filename(file_name), document_hash, classification, None, None, validation, metadata,
            )
            notify("Selesai — OCR dihentikan", 1.0)
            return PipelineResult(request_id, document_id, document_hash, duplicate, image, classification,
                                  validation=validation, metadata=metadata, stopped_after_classification=True)

        notify("Mengekstrak informasi KTP", 0.48)
        try:
            ocr = extract_ktp(self.client, image.content, image.mime_type)
        except JSONParseError as exc:
            fields = {name: None for name in IDENTITY_FIELDS}
            audit = {name: {"raw_value": None, "normalized_value": None} for name in IDENTITY_FIELDS}
            validation = ValidationSummary(
                status="REVIEW_REQUIRED",
                rules=[ValidationResult("ocr_json_parse", RuleStatus.NOT_CHECKED.value,
                                        "Respons OCR tidak dapat diparsing; perlu review.", critical=True)],
                derived={"verification_scope": "FORMAT_ONLY_NOT_DUKCAPIL_VERIFICATION"},
            )
            metadata = {
                "request_id": request_id, "data_context": self.data_context,
                "ocr_model": self.client.model,
                "ocr_prompt_version": OCR_PROMPT_VERSION,
                "ocr_duration_ms": None,
                "total_duration_ms": round((time.monotonic() - started) * 1000),
                "usage": classification.usage,
                "fields_missing": list(IDENTITY_FIELDS),
                "parse_status": "FAILED",
                "safe_error": type(exc).__name__,
            }
            notify("Menyimpan hasil untuk review", 0.9)
            document_id = self.repository.save(
                safe_filename(file_name), document_hash, classification, fields, audit, validation, metadata,
            )
            notify("Selesai — perlu review", 1.0)
            return PipelineResult(request_id, document_id, document_hash, duplicate, image, classification, fields, audit, validation, metadata)
        notify("Menormalisasi data", 0.67)
        fields, audit = normalize_fields(ocr.fields)
        notify("Menjalankan business rules", 0.78)
        validation = validate_ktp(fields)
        ocr_usage = ocr.metadata.get("usage") or {}
        classification_usage = classification.usage or {}
        usage = {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost"):
            values = [item.get(key) for item in (classification_usage, ocr_usage) if isinstance(item.get(key), (int, float))]
            usage[key] = sum(values) if values else None
        metadata = {
            "request_id": request_id, "data_context": self.data_context,
            "ocr_model": ocr.metadata.get("model"),
            "ocr_prompt_version": OCR_PROMPT_VERSION,
            "ocr_duration_ms": ocr.metadata.get("duration_ms"),
            "total_duration_ms": round((time.monotonic() - started) * 1000),
            "usage": usage,
            "fields_missing": ocr.metadata.get("fields_missing", []),
            "parse_status": ocr.metadata.get("parse_status"),
        }
        notify("Menyimpan hasil", 0.9)
        document_id = self.repository.save(
            safe_filename(file_name), document_hash, classification, fields, audit, validation, metadata,
        )
        notify("Selesai", 1.0)
        return PipelineResult(request_id, document_id, document_hash, duplicate, image, classification, fields, audit, validation, metadata)
