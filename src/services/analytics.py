from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils.constants import IDENTITY_FIELDS
from src.utils.security import mask_address, mask_date, mask_name, mask_nik, safe_csv_frame


def masked_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    result["nik_masked"] = result["nik"].apply(mask_nik)
    if "nama" in result:
        result["nama"] = result["nama"].apply(mask_name)
    if "alamat" in result:
        result["alamat"] = result["alamat"].apply(mask_address)
    if "tanggal_lahir" in result:
        result["tanggal_lahir"] = result["tanggal_lahir"].apply(mask_date)
    return result.drop(columns=["nik"], errors="ignore")


def dashboard_metrics(documents: pd.DataFrame) -> dict[str, Any]:
    if documents.empty:
        return {
            "total": 0, "ktp": 0, "non_ktp": 0, "valid": 0,
            "invalid": 0, "review": 0, "avg_ms": None, "median_ms": None,
            "min_ms": None, "max_ms": None,
        }
    durations = pd.to_numeric(documents["total_duration_ms"], errors="coerce").dropna()
    return {
        "total": len(documents),
        "ktp": int((documents["document_type"] == "KTP_INDONESIA").sum()),
        "non_ktp": int((documents["document_type"] == "OTHER").sum()),
        "valid": int((documents["validation_status"] == "VALID").sum()),
        "invalid": int((documents["validation_status"] == "INVALID").sum()),
        "review": int((documents["validation_status"] == "REVIEW_REQUIRED").sum()),
        "avg_ms": float(durations.mean()) if not durations.empty else None,
        "median_ms": float(durations.median()) if not durations.empty else None,
        "min_ms": float(durations.min()) if not durations.empty else None,
        "max_ms": float(durations.max()) if not durations.empty else None,
    }


def completeness(documents: pd.DataFrame) -> pd.DataFrame:
    ktp = documents[documents["document_type"] == "KTP_INDONESIA"] if not documents.empty else documents
    if ktp.empty:
        return pd.DataFrame(columns=["field", "completeness_pct"])
    rows = []
    for name in IDENTITY_FIELDS:
        present = ktp[name].notna() & ktp[name].astype(str).str.strip().ne("")
        rows.append({"field": name, "completeness_pct": round(float(present.mean() * 100), 2)})
    return pd.DataFrame(rows).sort_values("completeness_pct", ascending=True)


def failure_analysis(validations: pd.DataFrame) -> pd.DataFrame:
    if validations.empty:
        return pd.DataFrame(columns=["rule_name", "failure_count"])
    failed = validations[validations["status"] == "INVALID"]
    return failed.groupby("rule_name").size().reset_index(name="failure_count").sort_values("failure_count", ascending=False)


def export_columns(documents: pd.DataFrame) -> pd.DataFrame:
    masked = masked_history(documents)
    wanted = ["id", "file_name", "document_type", "nik_masked", "nama", "tanggal_lahir",
              "jenis_kelamin", "validation_status", "uploaded_at"]
    return safe_csv_frame(masked[[column for column in wanted if column in masked.columns]])
