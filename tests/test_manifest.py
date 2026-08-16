import json
from pathlib import Path

import pandas as pd


def test_manifest_has_twenty_real_files_without_prefilled_predictions():
    manifest = pd.read_csv("data/test_manifest.csv").fillna("")
    assert list(manifest.columns) == [
        "image_id", "file_name", "expected_class", "document_type", "source_type", "image_condition",
        "ground_truth_file", "consent_status", "image_hash", "notes", "dataset_version",
    ]
    assert len(manifest) == 20
    assert manifest["image_id"].is_unique
    assert set(manifest["expected_class"]) == {"KTP", "NON_KTP"}
    assert (manifest["expected_class"] == "KTP").sum() == 10
    assert (manifest["expected_class"] == "NON_KTP").sum() == 10
    assert set(manifest["source_type"]) == {"SYNTHETIC"}
    assert set(manifest["consent_status"]) == {"NOT_REQUIRED_SYNTHETIC"}
    assert manifest["image_hash"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert "prediction" not in manifest.columns
    for row in manifest.to_dict("records"):
        image_path = Path("data/testing") / row["file_name"]
        assert image_path.is_file()
        import hashlib
        assert hashlib.sha256(image_path.read_bytes()).hexdigest() == row["image_hash"]
        if row["ground_truth_file"]:
            truth = Path("data/ground_truth") / row["ground_truth_file"]
            assert truth.is_file()
            assert isinstance(json.loads(truth.read_text(encoding="utf-8")), dict)
