# Dataset and Evaluation Report

## Dataset status

Dataset version: `synthetic-v2.0.0`

| Check | Actual result |
| --- | --- |
| Total files | 20 |
| Expected KTP | 10 |
| Expected non-KTP | 10 |
| Source | 20 `SYNTHETIC` |
| Consent status | 20 `NOT_REQUIRED_SYNTHETIC` |
| Conditions | CLEAR 4, DARK 4, ROTATED 4, LOW_RESOLUTION 4, BLUR 2, PARTIALLY_CROPPED 2 |
| File readability | PASS 20/20 |
| SHA-256 verification | PASS 20/20 |
| Ground truth required for KTP | PASS 10/10 |
| Real personal data | None intentionally included |

The fixtures are visibly marked synthetic, use fictional fields and a deliberately non-official `999999` NIK region prefix. They test orchestration and evaluation plumbing, not real-world model generalization.

## Evaluation contract

`python scripts/evaluate.py` performs these gates before any paid request:

1. Manifest schema and unique ID validation.
2. Source and consent allowlist validation.
3. File existence, readability and hash validation.
4. Ground-truth JSON validation for KTP rows.

Every attempted row is retained. A request error becomes `predicted_class=ERROR`, `classification_correct=false`, plus a sanitized error type/message. It is never silently dropped.

Artifacts:

- `evaluation_results.csv`: image-level predictions, prompt/model versions, request ID, condition, latency, validation, parse and safe error metadata.
- `ocr_evaluation_results.csv`: masked field-level truth/prediction plus exact match, normalized match, CER, missing and hallucination flags.
- `evaluation_summary.json`: experiment metadata, classification/OCR metrics, condition analysis and privacy declaration.
- `data_quality_report.csv` and `data_quality_summary.json`: pre-inference dataset checks.

## Actual model result

Status: `COMPLETED — 20/20 ROWS PROCESSED`

Model: `dots-studio/dots-3-note-preview:free`

Experiment: `eval-20260816T210432Z-7e876b03`

Prompt versions: classification `1.1.0`, OCR `1.1.0`

| Metric | Value |
| --- | --- |
| Images evaluated | 20 (10 KTP, 10 non-KTP) |
| Successfully processed / failed | 20 / 0 |
| Classification accuracy | 100% |
| Precision/recall/F1 KTP | 100% / 100% / 100% |
| Confusion matrix | TP 10, TN 10, FP 0, FN 0 |
| OCR exact match | 139/140 populated truth fields (99.29%) |
| Mean character error rate | 0.71% |
| OCR schema completeness | 77.22% across all 18 fields |
| Median classification / OCR / total latency | 5.73 s / 15.25 s / 12.77 s |
| API / JSON errors | 0 / 0 |

These measurements apply only to the controlled synthetic-v2.0.0 fixture set. They are evidence that the integration and evaluation pipeline work; they are not a production-quality claim for real photographs or Indonesia's population. Sanitized artifacts are stored under `outputs/`; uploaded image bytes and raw OCR payloads are not persisted.
