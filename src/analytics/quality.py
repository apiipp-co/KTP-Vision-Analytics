from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils.constants import IDENTITY_FIELDS


def operational_quality(documents: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    issues: list[dict[str, Any]] = []
    if documents.empty:
        return {"status": "NO_DATA", "row_count": 0, "issue_count": 0, "duplicate_hashes": 0}, pd.DataFrame()
    required = {"id", "document_hash", "document_type", "validation_status", "processed_at"}
    for column in sorted(required - set(documents.columns)):
        issues.append({"severity": "ERROR", "check": "schema", "field": column, "count": len(documents),
                       "message": "Required database column missing"})
    duplicate_hashes = int(documents["document_hash"].duplicated(keep=False).sum()) if "document_hash" in documents else 0
    if duplicate_hashes:
        issues.append({"severity": "WARNING", "check": "duplicate_hash", "field": "document_hash",
                       "count": duplicate_hashes, "message": "Repeated file hashes detected"})
    ktp = documents[documents.get("document_type", pd.Series(index=documents.index, dtype=str)) == "KTP_INDONESIA"]
    for field in IDENTITY_FIELDS:
        if field not in ktp:
            continue
        missing = int((ktp[field].isna() | ktp[field].astype(str).str.strip().eq("")).sum())
        if missing:
            issues.append({"severity": "INFO", "check": "missing_value", "field": field, "count": missing,
                           "message": "Missing OCR values among classified KTP rows"})
    invalid_time = int(pd.to_datetime(documents.get("processed_at"), errors="coerce", utc=True).isna().sum())
    if invalid_time:
        issues.append({"severity": "ERROR", "check": "timestamp", "field": "processed_at", "count": invalid_time,
                       "message": "Invalid processing timestamp"})
    report = pd.DataFrame(issues, columns=["severity", "check", "field", "count", "message"])
    error_count = int((report.get("severity", pd.Series(dtype=str)) == "ERROR").sum()) if not report.empty else 0
    return {
        "status": "FAIL" if error_count else "PASS_WITH_WARNINGS" if not report.empty else "PASS",
        "row_count": len(documents), "issue_count": len(report), "duplicate_hashes": duplicate_hashes,
    }, report
