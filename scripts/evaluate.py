"""Run reproducible paid OpenRouter evaluation; never invent or prefill predictions."""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ai.openrouter_client import OpenRouterClient
from src.ai.prompts import CLASSIFICATION_PROMPT_VERSION, OCR_PROMPT_VERSION
from src.database.connection import Database
from src.database.repository import DocumentRepository
from src.processing.normalizer import normalize_fields
from src.services.dataset import manifest_summary, validate_manifest
from src.services.evaluation import character_error_rate, compute_evaluation_metrics, safe_exact
from src.services.pipeline import DocumentPipeline
from src.utils.config import Settings
from src.utils.constants import IDENTITY_FIELDS
from src.utils.security import mask_identity_field, safe_csv_frame


def safe_error(exc: Exception) -> tuple[str, str]:
    error_type = type(exc).__name__
    categories = {
        "OpenRouterError": "External AI request failed.",
        "ImageValidationError": "Input image validation failed.",
        "JSONParseError": "Structured model response could not be parsed.",
    }
    return error_type, categories.get(error_type, "Evaluation row failed safely.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--manifest", default="data/test_manifest.csv")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    cfg = Settings.from_env()
    manifest = pd.read_csv(ROOT / args.manifest).fillna("")
    manifest, issues = validate_manifest(manifest, ROOT)
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(issues, columns=["image_id", "severity", "check", "message"]).to_csv(
        output_dir / "data_quality_report.csv", index=False
    )
    quality = manifest_summary(manifest, issues)
    (output_dir / "data_quality_summary.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    if issues:
        raise SystemExit(f"Dataset quality FAILED ({len(issues)} issue); API tidak dipanggil.")
    if not cfg.openrouter_api_key:
        raise SystemExit("OPENROUTER_API_KEY tidak tersedia; data quality selesai, inferensi/metrics aktual tidak dibuat.")
    if args.limit:
        manifest = manifest.head(max(1, args.limit))

    started_at = datetime.now(timezone.utc)
    experiment_id = f"eval-{started_at:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    repo = DocumentRepository(Database(output_dir / "evaluation.db"))
    client = OpenRouterClient(cfg.openrouter_api_key, cfg.openrouter_model, cfg.timeout_seconds, cfg.max_retries)
    pipeline = DocumentPipeline(client, repo, cfg.max_image_size_mb, cfg.max_image_pixels, data_context="EVALUATION")
    rows: list[dict] = []
    ocr_rows: list[dict] = []

    for item in manifest.to_dict("records"):
        path = ROOT / "data" / "testing" / item["file_name"]
        row = {
            **item, "experiment_id": experiment_id, "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "model": cfg.openrouter_model, "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
            "ocr_prompt_version": OCR_PROMPT_VERSION, "predicted_class": "ERROR",
            "classification_correct": False, "classification_confidence": None, "validation_status": "",
            "parse_status": "", "classification_duration_ms": None, "ocr_duration_ms": None,
            "total_duration_ms": None, "request_id": "", "error_type": "", "error_message": "",
        }
        try:
            result = pipeline.process(path.name, path.read_bytes())
            prediction = "KTP" if result.classification.is_ktp else "NON_KTP"
            row.update({
                "predicted_class": prediction, "classification_correct": prediction == item["expected_class"],
                "classification_confidence": result.classification.confidence,
                "validation_status": result.validation.status, "parse_status": result.metadata.get("parse_status", ""),
                "classification_duration_ms": result.classification.duration_ms,
                "ocr_duration_ms": result.metadata.get("ocr_duration_ms"),
                "total_duration_ms": result.metadata.get("total_duration_ms"), "request_id": result.request_id,
            })
            for field in IDENTITY_FIELDS:
                row[f"present_{field}"] = bool(result.fields.get(field)) if result.classification.is_ktp else None
            if item["ground_truth_file"]:
                truth_raw = json.loads((ROOT / "data" / "ground_truth" / item["ground_truth_file"]).read_text(encoding="utf-8"))
                truth, _audit = normalize_fields(truth_raw)
                for field in IDENTITY_FIELDS:
                    expected, actual = truth.get(field), result.fields.get(field)
                    exact = safe_exact(actual, expected)
                    row[f"exact_{field}"] = exact
                    ocr_rows.append({
                        "experiment_id": experiment_id, "image_id": item["image_id"],
                        "image_condition": item["image_condition"], "field_name": field,
                        "ground_truth": mask_identity_field(field, expected), "prediction": mask_identity_field(field, actual),
                        "values_masked": True, "exact_match": exact, "normalized_match": exact,
                        "character_error_rate": character_error_rate(actual, expected), "is_missing": not bool(actual),
                        "is_hallucinated": bool(actual) and not bool(expected),
                    })
        except Exception as exc:
            row["error_type"], row["error_message"] = safe_error(exc)
        rows.append(row)

    results = pd.DataFrame(rows)
    results.to_csv(output_dir / "evaluation_results.csv", index=False)
    safe_csv_frame(pd.DataFrame(ocr_rows)).to_csv(output_dir / "ocr_evaluation_results.csv", index=False)
    metrics = compute_evaluation_metrics(results)
    condition_metrics = [
        {"image_condition": condition, "sample_count": len(group),
         "classification_accuracy": float(group["classification_correct"].astype(bool).mean())}
        for condition, group in results.groupby("image_condition", dropna=False)
    ]
    summary = {
        "experiment": {
            "experiment_id": experiment_id, "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(), "model": cfg.openrouter_model,
            "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION, "ocr_prompt_version": OCR_PROMPT_VERSION,
            "dataset_versions": sorted(manifest["dataset_version"].astype(str).unique()),
            "manifest": args.manifest, "data_context": "EVALUATION",
        },
        "metrics": metrics, "condition_analysis": condition_metrics,
        "privacy": {"ocr_values_masked_in_export": True, "raw_images_persisted": False},
    }
    (output_dir / "evaluation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Actual predictions saved under {output_dir}")


if __name__ == "__main__":
    main()
