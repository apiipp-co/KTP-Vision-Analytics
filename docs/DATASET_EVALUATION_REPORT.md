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

Status: `NOT TESTED — OPENROUTER_API_KEY MISSING`

| Metric | Value |
| --- | --- |
| Images submitted to OpenRouter | 0 |
| Classification accuracy | N/A |
| Precision/recall/F1 | N/A |
| OCR exact match/CER | N/A |
| Latency/cost | N/A |

No evaluation artifact or model-quality claim is generated without actual inference.
