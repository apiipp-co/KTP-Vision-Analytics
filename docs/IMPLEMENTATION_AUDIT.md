# Implementation audit

> Historical baseline. PostgreSQL, expanded privacy controls, dataset v2, advanced evaluation, and deployment checks were added later; see the 2026-08-16 reports in this directory.

## Phase 1 — Initial repository audit

The workspace was empty at the start of implementation. There were no existing files, dependencies, working features, or user changes to preserve.

## Requirement mapping

| Requirement | Initial status | Required change | Implemented file(s) |
|---|---|---|---|
| Image validation | Missing | Verify content, dimensions, format, size, EXIF | `src/processing/image_processor.py` |
| OpenRouter classification | Missing | Real multimodal request + structured output | `src/ai/openrouter_client.py`, `classifier.py` |
| Stop non-KTP OCR | Missing | Explicit pipeline branch | `src/services/pipeline.py` |
| AI Vision OCR | Missing | Separate request, null-safe schema | `src/ai/ocr.py`, `prompts.py` |
| JSON parsing | Missing | Defensive fence handling and strict failure | `src/processing/json_parser.py` |
| Normalization | Missing | Field-safe transforms + audit | `src/processing/normalizer.py` |
| NIK/business validation | Missing | Modular rules and tri-state outcomes | `src/validation/` |
| Official region validation | No dataset | Loader with fail-closed `NOT_CHECKED` | `src/validation/nik_validator.py`, `data/reference/README.md` |
| Database | Missing | Normalized SQLite schema/repository | `src/database/` |
| Privacy/security | Missing | In-memory images, hash, masking, secrets | `src/utils/security.py`, `.gitignore`, UI |
| Streamlit UI | Missing | Home, upload, result, about | `app.py`, `pages/` |
| Analytics/history/export | Missing | Live DB queries, filters, masked CSV | `pages/2_Analytics.py`, `3_Database_History.py` |
| 20-image testing set | Missing | Clearly labeled deterministic synthetic data | `scripts/generate_synthetic_dataset.py`, `data/testing/` |
| Evaluation | Missing | Actual-result-only metric runner | `scripts/evaluate.py` |
| Automated tests | Missing | Unit/integration coverage | `tests/` |
| Deployment/docs | Missing | Env, requirements, Cloud instructions | `.env.example`, `requirements.txt`, `README.md` |

## Final audit status

Implemented and locally verified: core branch logic, parsing, normalization, validation, SQLite transaction/retrieval, masking, CSV generation logic, 20 synthetic fixtures, automated tests, Streamlit startup, and page rendering.

Implemented but not verified against the external service: OpenRouter classification/OCR requests. Blocker: no `OPENROUTER_API_KEY` in the workspace environment. Therefore model predictions, accuracy, OCR exact-match metrics, external latency, token usage, and cost remain unclaimed.

Optional/not implemented: PostgreSQL/Supabase adapter, official machine-readable region CSV, real-world/consented KTP evaluation, production authentication/encryption. These are documented rather than represented as completed.
