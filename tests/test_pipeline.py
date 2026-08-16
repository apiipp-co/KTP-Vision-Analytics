import io

from PIL import Image
import pytest

from src.ai.openrouter_client import OpenRouterClient
from src.database.connection import Database
from src.database.repository import DocumentRepository
from src.models import ClassificationResult, OCRResult
from src.processing.json_parser import JSONParseError
from src.services.pipeline import DocumentPipeline, DuplicateDocumentError


def fixture_image():
    output = io.BytesIO()
    Image.new("RGB", (500, 300), "white").save(output, "JPEG")
    return output.getvalue()


def pipeline(tmp_path):
    client = object.__new__(OpenRouterClient)
    client.model = "fake/model"
    repo = DocumentRepository(Database(tmp_path / "pipeline.db"))
    return DocumentPipeline(client, repo), repo


def test_non_ktp_stops_before_ocr(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    monkeypatch.setattr("src.services.pipeline.classify_document", lambda *_: ClassificationResult(False, "OTHER", None, "other", "fake", "1", 1, {}))
    called = {"ocr": False}

    def should_not_run(*_):
        called["ocr"] = True
        raise AssertionError("OCR must not run")

    monkeypatch.setattr("src.services.pipeline.extract_ktp", should_not_run)
    result = service.process("other.jpg", fixture_image())
    assert result.stopped_after_classification is True
    assert called["ocr"] is False
    assert repo.history().iloc[0]["validation_status"] == "NOT_APPLICABLE"


def test_ktp_runs_ocr_normalizes_validates_and_saves(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    monkeypatch.setattr("src.services.pipeline.classify_document", lambda *_: ClassificationResult(True, "KTP_INDONESIA", None, "ktp", "fake", "1", 1, {}))
    fields = {"nik": "3273011505900001", "tanggal_lahir": "15/05/1990", "jenis_kelamin": "laki laki", "nama": "Data Uji"}
    monkeypatch.setattr("src.services.pipeline.extract_ktp", lambda *_: OCRResult(fields, {"model": "fake", "duration_ms": 2, "usage": {}, "parse_status": "SUCCESS"}))
    result = service.process("ktp.jpg", fixture_image())
    assert result.fields["tanggal_lahir"] == "1990-05-15"
    assert result.validation.status == "VALID"
    assert repo.history().iloc[0]["document_type"] == "KTP_INDONESIA"


def test_malformed_ocr_is_saved_for_review(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    monkeypatch.setattr("src.services.pipeline.classify_document", lambda *_: ClassificationResult(True, "KTP_INDONESIA", None, "ktp", "fake", "1", 1, {}))

    def malformed(*_):
        raise JSONParseError("malformed")

    monkeypatch.setattr("src.services.pipeline.extract_ktp", malformed)
    result = service.process("bad-json.jpg", fixture_image())
    assert result.validation.status == "REVIEW_REQUIRED"
    assert result.metadata["parse_status"] == "FAILED"
    assert repo.history().iloc[0]["validation_status"] == "REVIEW_REQUIRED"


def test_null_ocr_result_requires_review_and_does_not_crash(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    monkeypatch.setattr("src.services.pipeline.classify_document", lambda *_: ClassificationResult(True, "KTP_INDONESIA", None, "ktp", "fake", "1", 1, {}))
    monkeypatch.setattr("src.services.pipeline.extract_ktp", lambda *_: OCRResult({}, {"model": "fake", "duration_ms": 2, "usage": {}, "parse_status": "SUCCESS"}))
    result = service.process("null-ocr.jpg", fixture_image())
    assert result.validation.status == "REVIEW_REQUIRED"
    assert all(value is None for value in result.fields.values())
    assert repo.history().iloc[0]["validation_status"] == "REVIEW_REQUIRED"


def test_duplicate_production_upload_stops_before_second_api_call(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    calls = {"classification": 0}

    def classify(*_):
        calls["classification"] += 1
        return ClassificationResult(False, "OTHER", None, "other")

    monkeypatch.setattr("src.services.pipeline.classify_document", classify)
    content = fixture_image()
    service.process("first.jpg", content)
    with pytest.raises(DuplicateDocumentError, match="tidak diulang"):
        service.process("second.jpg", content)
    assert calls["classification"] == 1
    assert len(repo.history()) == 1


def test_evaluation_context_can_reprocess_same_fixture(monkeypatch, tmp_path):
    service, repo = pipeline(tmp_path)
    service.data_context = "EVALUATION"
    service.reject_duplicates = False
    monkeypatch.setattr("src.services.pipeline.classify_document",
                        lambda *_: ClassificationResult(False, "OTHER", None, "other"))
    content = fixture_image()
    service.process("one.jpg", content)
    service.process("two.jpg", content)
    assert len(repo.history()) == 2
