import sqlite3

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


def test_delete_document_cascades_related_rows(tmp_path):
    repo = DocumentRepository(Database(tmp_path / "delete.db"))
    classification = ClassificationResult(True, "KTP_INDONESIA", None, "visual")
    validation = ValidationSummary("VALID", [ValidationResult("nik_length", "VALID", "ok")])
    document_id = repo.save("delete.jpg", "delete-hash", classification, {"nik": "0012345678901234"},
                            {"nik": {"raw_value": "0012345678901234", "normalized_value": "0012345678901234"}},
                            validation, {"total_duration_ms": 1})
    assert repo.delete_document(document_id) is True
    assert repo.get_document(document_id) is None
    assert repo.fields().empty
    assert repo.validations().empty
    assert repo.delete_document(document_id) is False


def test_legacy_sqlite_schema_migrates_before_new_indexes(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE documents (
            id INTEGER PRIMARY KEY, file_name TEXT, document_hash TEXT, document_type TEXT,
            is_ktp INTEGER, classification_result TEXT, validation_status TEXT,
            uploaded_at TEXT, processed_at TEXT
        )""")
    Database(path).initialize()
    with sqlite3.connect(path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(documents)")}
    assert {"classification_model", "request_id", "data_context"}.issubset(columns)
    assert {"idx_documents_request_id", "idx_documents_context"}.issubset(indexes)
