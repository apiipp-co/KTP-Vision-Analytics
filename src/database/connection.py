from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    document_hash TEXT NOT NULL,
    document_type TEXT NOT NULL,
    is_ktp INTEGER NOT NULL DEFAULT 0,
    classification_result TEXT NOT NULL,
    classification_confidence REAL,
    classification_reason TEXT,
    classification_model TEXT,
    nik TEXT,
    nama TEXT,
    tempat_lahir TEXT,
    tanggal_lahir TEXT,
    jenis_kelamin TEXT,
    alamat TEXT,
    rt TEXT,
    rw TEXT,
    kelurahan_desa TEXT,
    kecamatan TEXT,
    agama TEXT,
    status_perkawinan TEXT,
    pekerjaan TEXT,
    kewarganegaraan TEXT,
    berlaku_hingga TEXT,
    provinsi TEXT,
    kabupaten_kota TEXT,
    golongan_darah TEXT,
    validation_status TEXT NOT NULL,
    ocr_model TEXT,
    classification_prompt_version TEXT,
    ocr_prompt_version TEXT,
    classification_duration_ms INTEGER,
    ocr_duration_ms INTEGER,
    total_duration_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    api_cost REAL,
    uploaded_at TEXT NOT NULL,
    processed_at TEXT NOT NULL
    ,request_id TEXT
    ,data_context TEXT NOT NULL DEFAULT 'PRODUCTION'
);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed_at);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(validation_status);

CREATE TABLE IF NOT EXISTS extracted_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    is_missing INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_fields_document ON extracted_fields(document_id);

CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    rule_name TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    actual_value TEXT,
    expected_value TEXT,
    is_critical INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_validation_document ON validation_results(document_id);

CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    stage TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Database:
    dialect = "sqlite"
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)").fetchall()}
            if "classification_model" not in columns:
                conn.execute("ALTER TABLE documents ADD COLUMN classification_model TEXT")
            if "request_id" not in columns:
                conn.execute("ALTER TABLE documents ADD COLUMN request_id TEXT")
            if "data_context" not in columns:
                conn.execute("ALTER TABLE documents ADD COLUMN data_context TEXT NOT NULL DEFAULT 'PRODUCTION'")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_request_id ON documents(request_id) WHERE request_id IS NOT NULL")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_context ON documents(data_context)")


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    file_name TEXT NOT NULL, document_hash TEXT NOT NULL, document_type TEXT NOT NULL,
    is_ktp INTEGER NOT NULL DEFAULT 0, classification_result TEXT NOT NULL,
    classification_confidence DOUBLE PRECISION, classification_reason TEXT, classification_model TEXT,
    nik TEXT, nama TEXT, tempat_lahir TEXT, tanggal_lahir TEXT, jenis_kelamin TEXT, alamat TEXT,
    rt TEXT, rw TEXT, kelurahan_desa TEXT, kecamatan TEXT, agama TEXT, status_perkawinan TEXT,
    pekerjaan TEXT, kewarganegaraan TEXT, berlaku_hingga TEXT, provinsi TEXT, kabupaten_kota TEXT,
    golongan_darah TEXT, validation_status TEXT NOT NULL, ocr_model TEXT,
    classification_prompt_version TEXT, ocr_prompt_version TEXT, classification_duration_ms INTEGER,
    ocr_duration_ms INTEGER, total_duration_ms INTEGER, input_tokens INTEGER, output_tokens INTEGER,
    total_tokens INTEGER, api_cost DOUBLE PRECISION, uploaded_at TEXT NOT NULL, processed_at TEXT NOT NULL,
    request_id TEXT, data_context TEXT NOT NULL DEFAULT 'PRODUCTION'
);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed_at);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(validation_status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_request_id ON documents(request_id) WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_context ON documents(data_context);
CREATE TABLE IF NOT EXISTS extracted_fields (
    id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL, raw_value TEXT, normalized_value TEXT, is_missing INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_fields_document ON extracted_fields(document_id);
CREATE TABLE IF NOT EXISTS validation_results (
    id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    rule_name TEXT NOT NULL, status TEXT NOT NULL, message TEXT NOT NULL, actual_value TEXT,
    expected_value TEXT, is_critical INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_validation_document ON validation_results(document_id);
CREATE TABLE IF NOT EXISTS processing_logs (
    id BIGSERIAL PRIMARY KEY, document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    stage TEXT NOT NULL, level TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class PostgresDatabase:
    dialect = "postgresql"

    def __init__(self, url: str):
        self.url = url

    @contextmanager
    def connect(self) -> Iterator[Any]:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Driver PostgreSQL belum terpasang.") from exc
        conn = psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            for statement in (part.strip() for part in POSTGRES_SCHEMA.split(";") if part.strip()):
                conn.execute(statement)
            conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS request_id TEXT")
            conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS data_context TEXT NOT NULL DEFAULT 'PRODUCTION'")


def database_from_url(database_url: str, project_root: Path) -> Database | PostgresDatabase:
    if database_url.startswith("sqlite:///"):
        value = database_url[len("sqlite:///"):]
        path = Path(value)
        return Database(path if path.is_absolute() else project_root / path)
    if database_url.startswith(("postgresql://", "postgres://")):
        return PostgresDatabase(database_url)
    raise ValueError("DATABASE_URL harus menggunakan sqlite:/// atau postgresql://.")
