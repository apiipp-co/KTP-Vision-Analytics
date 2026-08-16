import pandas as pd

from src.services.evaluation import character_error_rate, compute_evaluation_metrics, operational_error_analysis, safe_exact


def test_empty_ground_truth_is_not_false_success():
    assert safe_exact(None, None) is None
    assert safe_exact("", "") is None
    assert safe_exact("BUDI", "budi") is True
    assert character_error_rate("BUDI", "BUDI") == 0
    assert character_error_rate("BUDI", "BUD") == 1 / 3
    assert character_error_rate("", None) is None


def test_new_evaluation_column_contract_is_supported():
    rows = pd.DataFrame([{"expected_class": "KTP", "predicted_class": "ERROR", "classification_correct": False,
                          "error_type": "OpenRouterError"}])
    metrics = compute_evaluation_metrics(rows)
    assert metrics["failed"] == 1
    assert metrics["processed_successfully"] == 0


def test_csv_boolean_strings_and_current_error_columns_are_handled_correctly():
    rows = pd.DataFrame([
        {"expected_class": "KTP", "predicted_class": "KTP", "classification_correct": "True",
         "exact_nik": "False", "present_nik": "True", "validation_status": "INVALID", "error_type": ""},
        {"expected_class": "NON_KTP", "predicted_class": "KTP", "classification_correct": "False",
         "exact_nik": None, "present_nik": "False", "validation_status": "NOT_APPLICABLE", "error_type": "OpenRouterError"},
    ])
    metrics = compute_evaluation_metrics(rows)
    assert metrics["accuracy"] == 0.5
    assert metrics["field_exact_match"]["nik"] == 0.0
    assert metrics["ocr_data_completeness"] == 1.0
    errors = {item["error_type"]: item["count"] for item in metrics["error_analysis"]}
    assert errors["Validation Error"] == 1
    assert errors["API Error"] == 1


def test_actual_result_metrics_and_missing_rates_are_computed():
    results = pd.DataFrame([
        {"expected_class": "KTP", "prediction": "KTP", "correct": True,
         "exact_nik": True, "exact_nama": False, "present_nik": True, "present_nama": True,
         "parse_status": "SUCCESS", "validation": "INVALID", "error": ""},
        {"expected_class": "NON_KTP", "prediction": "NON_KTP", "correct": True,
         "exact_nik": None, "exact_nama": None, "present_nik": None, "present_nama": None,
         "parse_status": "", "validation": "NOT_APPLICABLE", "error": ""},
    ])
    metrics = compute_evaluation_metrics(results)
    assert metrics["accuracy"] == 1.0
    assert metrics["precision_ktp"] == 1.0
    assert metrics["field_exact_match"]["nik"] == 1.0
    assert metrics["field_exact_match"]["nama"] == 0.0
    assert metrics["ocr_data_completeness"] == 1.0
    assert metrics["missing_field_rate"] == 0.0


def test_operational_error_analysis_uses_real_denominators():
    documents = pd.DataFrame([{"id": 1, "validation_status": "INVALID"}, {"id": 2, "validation_status": "VALID"}])
    validations = pd.DataFrame([{"document_id": 1, "rule_name": "ocr_json_parse"}])
    fields = pd.DataFrame([{"document_id": 1, "is_missing": 1}, {"document_id": 2, "is_missing": 0}])
    logs = pd.DataFrame([{"stage": "openrouter", "level": "ERROR"}])
    analysis = operational_error_analysis(documents, validations, fields, logs)
    row = analysis[analysis["category"] == "Validation Error"].iloc[0]
    assert row["count"] == 1
    assert row["percentage"] == 50.0
    assert analysis[analysis["category"] == "API Error"].iloc[0]["count"] == 1
