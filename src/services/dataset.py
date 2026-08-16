from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, UnidentifiedImageError


MANIFEST_COLUMNS = [
    "image_id", "file_name", "expected_class", "document_type", "source_type",
    "image_condition", "ground_truth_file", "consent_status", "image_hash", "notes", "dataset_version",
]
ALLOWED_SOURCES = {"REAL_ANONYMIZED", "LICENSED", "SYNTHETIC"}
ALLOWED_CONSENT = {"CONSENTED", "LICENSED", "NOT_REQUIRED_SYNTHETIC"}


def validate_manifest(manifest: pd.DataFrame, root: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    missing = [name for name in MANIFEST_COLUMNS if name not in manifest.columns]
    if missing:
        return pd.DataFrame(), [{"image_id": "", "severity": "ERROR", "check": "schema", "message": f"Missing columns: {missing}"}]
    if manifest.empty:
        errors.append({"image_id": "", "severity": "ERROR", "check": "row_count", "message": "Manifest is empty"})
    for image_id in manifest.loc[manifest["image_id"].duplicated(keep=False), "image_id"].astype(str).unique():
        errors.append({"image_id": image_id, "severity": "ERROR", "check": "unique_id", "message": "Duplicate image_id"})
    for row in manifest.fillna("").to_dict("records"):
        image_id = str(row["image_id"])
        image_path = root / "data" / "testing" / str(row["file_name"])
        if str(row["expected_class"]) not in {"KTP", "NON_KTP"}:
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "class", "message": "Unsupported expected_class"})
        if str(row["source_type"]) not in ALLOWED_SOURCES:
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "source", "message": "Unsupported source_type"})
        if str(row["consent_status"]) not in ALLOWED_CONSENT:
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "consent", "message": "Missing/unsupported consent_status"})
        if not image_path.is_file():
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "file", "message": "Image file missing"})
            continue
        actual_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if actual_hash != str(row["image_hash"]):
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "hash", "message": "SHA-256 mismatch"})
        try:
            with Image.open(image_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "image", "message": "Unreadable image"})
        truth_name = str(row["ground_truth_file"])
        if row["expected_class"] == "KTP" and not truth_name:
            errors.append({"image_id": image_id, "severity": "ERROR", "check": "ground_truth", "message": "KTP ground truth missing"})
        if truth_name:
            truth_path = root / "data" / "ground_truth" / truth_name
            try:
                payload = json.loads(truth_path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError
            except (OSError, ValueError, json.JSONDecodeError):
                errors.append({"image_id": image_id, "severity": "ERROR", "check": "ground_truth", "message": "Invalid ground-truth JSON"})
    report = pd.DataFrame(errors, columns=["image_id", "severity", "check", "message"])
    return manifest, errors


def manifest_summary(manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_images": int(len(manifest)),
        "class_distribution": manifest.get("expected_class", pd.Series(dtype=str)).value_counts().to_dict(),
        "condition_distribution": manifest.get("image_condition", pd.Series(dtype=str)).value_counts().to_dict(),
        "source_distribution": manifest.get("source_type", pd.Series(dtype=str)).value_counts().to_dict(),
        "dataset_versions": sorted(manifest.get("dataset_version", pd.Series(dtype=str)).dropna().astype(str).unique()),
        "issue_count": len(issues),
        "status": "PASS" if not issues else "FAIL",
    }
