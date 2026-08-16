from src.database.connection import Database
from src.database.repository import DocumentRepository
from src.models import ClassificationResult, ValidationResult, ValidationSummary
from src.services.analytics import export_columns


def test_insert_retrieve_duplicate_and_related_rows(tmp_path):
    repo = DocumentRepository(Database(tmp_path / "test.db"))
    classification = ClassificationResult(True, "KTP_INDONESIA", None, "visual", "model", "1.0", 10, {})
    fields = {"nik": "3273011505900001", "nama": "DATA UJI"}
    audit = {"nik": {"raw_value": fields["nik"], "normalized_value": fields["nik"]}}
    validation = ValidationSummary("VALID", [ValidationResult("nik_length", "VALID", "ok", critical=True)])
    document_id = repo.save("test.jpg", "abc", classification, fields, audit, validation, {"total_duration_ms": 20})
    assert repo.get_document(document_id)["nama"] == "DATA UJI"
    assert repo.find_duplicate("abc")["id"] == document_id
    assert len(repo.history()) == 1
    assert len(repo.validations()) == 1
    assert len(repo.fields()) == 1
    assert repo.get_document(document_id)["classification_model"] == "model"


def test_select_filter_limit_and_masked_export(tmp_path):
    repo = DocumentRepository(Database(tmp_path / "filter.db"))
    for index, doc_type in enumerate(("KTP_INDONESIA", "OTHER"), start=1):
        classification = ClassificationResult(doc_type == "KTP_INDONESIA", doc_type, None, "visual", "model", "1.0", 10, {})
        fields = {"nik": "0012345678901234", "nama": f"DATA {index}"} if doc_type == "KTP_INDONESIA" else None
        repo.save(f"test-{index}.jpg", f"hash-{index}", classification, fields, None,
                  ValidationSummary("VALID" if fields else "NOT_APPLICABLE", []), {"total_duration_ms": 20})
    history = repo.history()
    assert len(history) == 2
    assert len(repo.history(limit=1)) == 1
    filtered = history[history["document_type"] == "KTP_INDONESIA"]
    exported = export_columns(filtered)
    assert len(exported) == 1
    assert "nik" not in exported.columns
    assert exported.iloc[0]["nik_masked"] == "0012********1234"
    log_id = repo.log_event("openrouter", "error", "safe error")
    assert log_id > 0
    assert repo.logs().iloc[0]["message"] == "safe error"
