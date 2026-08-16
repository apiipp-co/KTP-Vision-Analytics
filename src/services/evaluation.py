from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def safe_exact(actual: str | None, expected: str | None) -> bool | None:
    """Compare only when ground truth contains a non-empty expected value."""
    if expected is None or not str(expected).strip():
        return None
    return (actual or "").strip().casefold() == str(expected).strip().casefold()


def character_error_rate(actual: str | None, expected: str | None) -> float | None:
    if expected is None or not str(expected):
        return None
    left, right = str(actual or ""), str(expected)
    previous = list(range(len(right) + 1))
    for row, char_left in enumerate(left, start=1):
        current = [row]
        for column, char_right in enumerate(right, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (char_left != char_right)))
        previous = current
    return previous[-1] / len(right)


def compute_evaluation_metrics(results: pd.DataFrame) -> dict[str, Any]:
    if results.empty:
        raise ValueError("Evaluation results kosong; metrics tidak boleh dibuat.")
    prediction_column = "predicted_class" if "predicted_class" in results else "prediction"
    correct_column = "classification_correct" if "classification_correct" in results else "correct"
    required = {"expected_class", prediction_column, correct_column}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Kolom evaluation results tidak lengkap: {sorted(missing)}")
    actual_positive = results["expected_class"] == "KTP"
    predicted_positive = results[prediction_column] == "KTP"
    errors = results[prediction_column] == "ERROR"
    tp = int((actual_positive & predicted_positive).sum())
    fp = int((~actual_positive & predicted_positive).sum())
    fn = int((actual_positive & ~predicted_positive).sum())
    tn = int((~actual_positive & ~predicted_positive & ~errors).sum())
    correct = results[correct_column].map(lambda value: value is True or str(value).lower() == "true")
    accuracy = float(correct.mean())
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None

    exact_columns = [column for column in results if column.startswith("exact_")]
    field_accuracy: dict[str, float | None] = {}
    for column in exact_columns:
        evaluated = results[column].dropna()
        field_accuracy[column.removeprefix("exact_")] = float(evaluated.astype(bool).mean()) if not evaluated.empty else None

    present_columns = [column for column in results if column.startswith("present_")]
    predicted_ktp = results[predicted_positive]
    if present_columns and not predicted_ktp.empty:
        presence = predicted_ktp[present_columns].apply(
            lambda series: series.map(lambda value: value is True or str(value).lower() == "true")
        )
        completeness = float(presence.to_numpy().mean())
        missing_rate = 1.0 - completeness
    else:
        completeness = None
        missing_rate = None

    error_counts = {
        "False Positive": fp,
        "False Negative": fn,
        "OCR Error": int(results[exact_columns].eq(False).any(axis=1).sum()) if exact_columns else 0,
        "Missing Field": int(results[present_columns].eq(False).any(axis=1).sum()) if present_columns else 0,
        "JSON Error": int((results.get("parse_status", pd.Series(index=results.index, dtype=object)) == "FAILED").sum()),
        "Validation Error": int((results.get("validation", pd.Series(index=results.index, dtype=object)) == "INVALID").sum()),
        "API Error": int(results.get("error", pd.Series(index=results.index, dtype=object)).astype(str).str.contains("OpenRouterError", regex=False).sum()),
    }
    error_analysis = [
        {"error_type": name, "count": count, "percentage": count / len(results) * 100}
        for name, count in error_counts.items()
    ]
    return {
        "total": len(results),
        "processed_successfully": int((~errors).sum()),
        "failed": int(errors.sum()),
        "accuracy": accuracy,
        "precision_ktp": precision,
        "recall_ktp": recall,
        "f1_ktp": f1,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "field_exact_match": field_accuracy,
        "ocr_data_completeness": completeness,
        "missing_field_rate": missing_rate,
        "error_analysis": error_analysis,
    }


def load_evaluation_artifacts(output_dir: Path | str = "outputs") -> tuple[pd.DataFrame | None, dict[str, Any] | None]:
    directory = Path(output_dir)
    csv_path = directory / "evaluation_results.csv"
    json_path = directory / "evaluation_summary.json"
    if not json_path.exists():
        json_path = directory / "evaluation_results.json"
    if not csv_path.exists() or not json_path.exists():
        return None, None
    try:
        results = pd.read_csv(csv_path)
        metrics = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None, None
    metric_payload = metrics.get("metrics", metrics) if isinstance(metrics, dict) else {}
    if not isinstance(metric_payload, dict) or metric_payload.get("total") != len(results) or results.empty:
        return None, None
    return results, metric_payload


def operational_error_analysis(documents: pd.DataFrame, validations: pd.DataFrame,
                               fields: pd.DataFrame, logs: pd.DataFrame | None = None,
                               evaluation: pd.DataFrame | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    document_total = len(documents)

    def add(category: str, count: int, denominator: int, scope: str) -> None:
        rows.append({
            "category": category,
            "count": count,
            "percentage": (count / denominator * 100) if denominator else None,
            "denominator": denominator,
            "scope": scope,
        })

    json_docs = validations.loc[validations.get("rule_name", pd.Series(dtype=object)) == "ocr_json_parse", "document_id"].nunique() if not validations.empty else 0
    invalid_docs = int((documents.get("validation_status", pd.Series(dtype=object)) == "INVALID").sum()) if not documents.empty else 0
    missing_docs = fields.loc[fields.get("is_missing", pd.Series(dtype=int)) == 1, "document_id"].nunique() if not fields.empty else 0
    add("JSON Error", int(json_docs), document_total, "database")
    add("Validation Error", invalid_docs, document_total, "database")
    add("Missing Field", int(missing_docs), document_total, "database")
    if logs is not None and not logs.empty:
        api_errors = int(((logs["stage"] == "openrouter") & (logs["level"] == "ERROR")).sum())
        add("API Error", api_errors, len(logs), "processing_logs")

    if evaluation is not None and not evaluation.empty:
        expected_ktp = evaluation["expected_class"] == "KTP"
        prediction_column = "predicted_class" if "predicted_class" in evaluation else "prediction"
        predicted_ktp = evaluation[prediction_column] == "KTP"
        add("False Positive", int((~expected_ktp & predicted_ktp).sum()), len(evaluation), "evaluation")
        add("False Negative", int((expected_ktp & ~predicted_ktp).sum()), len(evaluation), "evaluation")
        exact = [column for column in evaluation if column.startswith("exact_")]
        add("OCR Error", int(evaluation[exact].eq(False).any(axis=1).sum()) if exact else 0, len(evaluation), "evaluation")
        error_series = evaluation.get("error_type", evaluation.get("error", pd.Series(index=evaluation.index, dtype=object)))
        add("API Error", int(error_series.astype(str).str.contains("OpenRouterError", regex=False).sum()), len(evaluation), "evaluation")
    return pd.DataFrame(rows)
