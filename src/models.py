from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from src.utils.constants import DocumentType, OverallStatus, RuleStatus


@dataclass
class ClassificationResult:
    is_ktp: bool
    document_type: str
    confidence: Optional[float]
    reason: str
    model: str = ""
    prompt_version: str = ""
    duration_ms: Optional[int] = None
    usage: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], **metadata: Any) -> "ClassificationResult":
        document_type = str(data.get("document_type", DocumentType.UNCERTAIN.value))
        if document_type not in {item.value for item in DocumentType}:
            document_type = DocumentType.UNCERTAIN.value
        confidence = data.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
                if not 0 <= confidence <= 1:
                    confidence = None
            except (TypeError, ValueError):
                confidence = None
        is_ktp = bool(data.get("is_ktp")) and document_type == DocumentType.KTP_INDONESIA.value
        return cls(
            is_ktp=is_ktp,
            document_type=document_type,
            confidence=confidence,
            reason=str(data.get("reason") or "Tidak ada alasan yang diberikan model.")[:500],
            **metadata,
        )


@dataclass
class OCRResult:
    fields: dict[str, Optional[str]]
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""


@dataclass
class ValidationResult:
    rule: str
    status: str
    message: str
    actual_value: Optional[str] = None
    expected_value: Optional[str] = None
    critical: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationSummary:
    status: str = OverallStatus.REVIEW_REQUIRED.value
    rules: list[ValidationResult] = field(default_factory=list)
    derived: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_rules(cls, rules: list[ValidationResult], derived: dict[str, Any] | None = None) -> "ValidationSummary":
        critical = [rule for rule in rules if rule.critical]
        if any(rule.status == RuleStatus.INVALID.value for rule in critical):
            overall = OverallStatus.INVALID.value
        elif not critical or any(rule.status == RuleStatus.NOT_CHECKED.value for rule in critical):
            overall = OverallStatus.REVIEW_REQUIRED.value
        else:
            overall = OverallStatus.VALID.value
        return cls(status=overall, rules=rules, derived=derived or {})
