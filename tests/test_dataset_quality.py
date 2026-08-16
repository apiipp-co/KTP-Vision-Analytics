from pathlib import Path

import pandas as pd

from src.analytics.quality import operational_quality
from src.services.dataset import validate_manifest


def test_manifest_validator_detects_hash_tampering():
    root = Path.cwd()
    manifest = pd.read_csv(root / "data/test_manifest.csv").fillna("")
    manifest.loc[0, "image_hash"] = "0" * 64
    _manifest, issues = validate_manifest(manifest, root)
    assert any(item["check"] == "hash" for item in issues)


def test_operational_quality_reports_duplicates_and_missing_fields():
    frame = pd.DataFrame([
        {"id": 1, "document_hash": "same", "document_type": "KTP_INDONESIA", "validation_status": "VALID", "processed_at": "2026-01-01", "nik": None},
        {"id": 2, "document_hash": "same", "document_type": "OTHER", "validation_status": "NOT_APPLICABLE", "processed_at": "2026-01-02", "nik": None},
    ])
    summary, report = operational_quality(frame)
    assert summary["duplicate_hashes"] == 2
    assert "duplicate_hash" in set(report["check"])
