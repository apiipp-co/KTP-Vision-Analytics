from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.database.connection import Database
from src.models import ClassificationResult, ValidationSummary
from src.utils.constants import IDENTITY_FIELDS


class DocumentRepository:
    def __init__(self, database: Database):
        self.db = database
        self.db.initialize()

    def _sql(self, query: str) -> str:
        return query.replace("?", "%s") if self.db.dialect == "postgresql" else query

    def find_duplicate(self, document_hash: str) -> dict[str, Any] | None:
        with self.db.connect() as conn:
            row = conn.execute(
                self._sql("SELECT id, file_name, document_type, validation_status, processed_at FROM documents WHERE document_hash = ? ORDER BY id DESC LIMIT 1"),
                (document_hash,),
            ).fetchone()
        return dict(row) if row else None

    def save(self, file_name: str, document_hash: str, classification: ClassificationResult,
             fields: dict[str, str | None] | None, audit: dict[str, dict[str, str | None]] | None,
             validation: ValidationSummary, metadata: dict[str, Any]) -> int:
        fields = fields or {}
        now = datetime.now(timezone.utc).isoformat()
        usage = metadata.get("usage") if isinstance(metadata.get("usage"), dict) else {}
        columns = [
            "file_name", "document_hash", "document_type", "is_ktp", "classification_result",
            "classification_confidence", "classification_reason", "classification_model", *IDENTITY_FIELDS, "validation_status",
            "ocr_model", "classification_prompt_version", "ocr_prompt_version", "classification_duration_ms",
            "ocr_duration_ms", "total_duration_ms", "input_tokens", "output_tokens", "total_tokens", "api_cost",
            "uploaded_at", "processed_at",
            "request_id", "data_context",
        ]
        values = [
            file_name, document_hash, classification.document_type, int(classification.is_ktp),
            json.dumps({"is_ktp": classification.is_ktp, "document_type": classification.document_type}, ensure_ascii=False),
            classification.confidence, classification.reason, classification.model,
            *[fields.get(name) for name in IDENTITY_FIELDS], validation.status, metadata.get("ocr_model"),
            classification.prompt_version, metadata.get("ocr_prompt_version"), classification.duration_ms,
            metadata.get("ocr_duration_ms"), metadata.get("total_duration_ms"), usage.get("prompt_tokens"),
            usage.get("completion_tokens"), usage.get("total_tokens"), usage.get("cost"), now, now,
            metadata.get("request_id"), metadata.get("data_context", "PRODUCTION"),
        ]
        placeholders = ",".join("?" for _ in columns)
        with self.db.connect() as conn:
            statement = f"INSERT INTO documents ({','.join(columns)}) VALUES ({placeholders})"
            if self.db.dialect == "postgresql":
                cursor = conn.execute(self._sql(statement) + " RETURNING id", values)
                document_id = int(cursor.fetchone()["id"])
            else:
                cursor = conn.execute(statement, values)
                document_id = int(cursor.lastrowid)
            if audit:
                conn.executemany(
                    self._sql("INSERT INTO extracted_fields (document_id, field_name, raw_value, normalized_value, is_missing) VALUES (?, ?, ?, ?, ?)"),
                    [(document_id, name, values_.get("raw_value"), values_.get("normalized_value"), int(not values_.get("normalized_value")))
                     for name, values_ in audit.items()],
                )
            if validation.rules:
                conn.executemany(
                    self._sql("INSERT INTO validation_results (document_id, rule_name, status, message, actual_value, expected_value, is_critical) VALUES (?, ?, ?, ?, ?, ?, ?)"),
                    [(document_id, rule.rule, rule.status, rule.message, rule.actual_value, rule.expected_value, int(rule.critical))
                     for rule in validation.rules],
                )
        return document_id

    def history(self, limit: int | None = None) -> pd.DataFrame:
        query = "SELECT * FROM documents ORDER BY processed_at DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (max(1, int(limit)),)
        with self.db.connect() as conn:
            return pd.read_sql_query(self._sql(query), conn, params=params)

    def validations(self) -> pd.DataFrame:
        with self.db.connect() as conn:
            return pd.read_sql_query("SELECT * FROM validation_results", conn)

    def fields(self) -> pd.DataFrame:
        with self.db.connect() as conn:
            return pd.read_sql_query("SELECT * FROM extracted_fields", conn)

    def get_document(self, document_id: int) -> dict[str, Any] | None:
        with self.db.connect() as conn:
            row = conn.execute(self._sql("SELECT * FROM documents WHERE id = ?"), (document_id,)).fetchone()
        return dict(row) if row else None

    def log_event(self, stage: str, level: str, message: str, document_id: int | None = None) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        safe_stage = str(stage)[:50]
        safe_level = str(level).upper()[:20]
        safe_message = str(message)[:500]
        with self.db.connect() as conn:
            statement = "INSERT INTO processing_logs (document_id, stage, level, message, created_at) VALUES (?, ?, ?, ?, ?)"
            if self.db.dialect == "postgresql":
                cursor = conn.execute(self._sql(statement) + " RETURNING id", (document_id, safe_stage, safe_level, safe_message, created_at))
                return int(cursor.fetchone()["id"])
            cursor = conn.execute(statement, (document_id, safe_stage, safe_level, safe_message, created_at))
            return int(cursor.lastrowid)

    def logs(self) -> pd.DataFrame:
        with self.db.connect() as conn:
            return pd.read_sql_query("SELECT * FROM processing_logs ORDER BY created_at DESC", conn)
