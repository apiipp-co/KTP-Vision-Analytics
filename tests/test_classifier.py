import json

import pytest

from src.ai.classifier import classify_document
from src.ai.openrouter_client import AIResponse
from src.processing.json_parser import JSONParseError


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def vision_json(self, **kwargs):
        return AIResponse(self.payload, "fake/model", 12, {})


def test_classifier_uses_actual_structured_response():
    payload = json.dumps({"is_ktp": False, "document_type": "OTHER", "confidence": None, "reason": "Bentuk berbeda"})
    result = classify_document(FakeClient(payload), b"image", "image/jpeg")
    assert result.is_ktp is False
    assert result.confidence is None
    assert result.model == "fake/model"


def test_classifier_rejects_malformed_response():
    with pytest.raises(JSONParseError):
        classify_document(FakeClient("not-json"), b"image", "image/jpeg")


def test_classifier_rejects_additional_field():
    payload = json.dumps({"is_ktp": False, "document_type": "OTHER", "confidence": None,
                          "reason": "Bentuk berbeda", "unexpected": True})
    with pytest.raises(JSONParseError, match="tidak dikenal"):
        classify_document(FakeClient(payload), b"image", "image/jpeg")
