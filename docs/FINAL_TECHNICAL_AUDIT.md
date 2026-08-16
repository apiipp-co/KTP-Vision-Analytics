# Final Technical Audit

> Superseded for the latest production-readiness state by `PRODUCTION_READINESS_REPORT.md`, `SECURITY_PRIVACY_AUDIT.md`, and `DATASET_EVALUATION_REPORT.md` (2026-08-16).

Audit date: 2026-08-16 (Asia/Jakarta)

Status vocabulary is restricted to: `IMPLEMENTED & TESTED`, `IMPLEMENTED BUT NOT TESTED`, `PARTIALLY IMPLEMENTED`, `NOT IMPLEMENTED`, `BLOCKED`.

## Requirement audit

| Requirement | Status | Evidence/File | Problem | Action |
|---|---|---|---|---|
| Repository structure and all text files | IMPLEMENTED & TESTED | Full inventory of 2,300+ lines; `app.py`, `pages/`, `src/`, `scripts/`, `tests/`, configs, docs, manifest, and all ground-truth JSON read during audit | Project is nested under a Git repository rooted at the user home directory and is not independently committed | Keep project `.gitignore`; initialize/publish a dedicated repository before deployment |
| Runtime dependencies | IMPLEMENTED & TESTED | `requirements.txt`; clean Python 3.9 virtual environment install succeeded; 42 tests passed there | `pytest` is included in deployment requirements | Kept intentionally so the documented test command works after one install |
| OpenRouter endpoint/request construction | IMPLEMENTED & TESTED | `src/ai/openrouter_client.py`; request-construction tests verify endpoint, auth header, base64 image, JSON Schema, timeout/retry settings | Successful authenticated inference cannot be proven without a key | Actual inference remains blocked |
| Successful OpenRouter Vision call | BLOCKED | `scripts/evaluate.py` exits without creating metrics when key is absent | `OPENROUTER_API_KEY` is unavailable | `BLOCKED — OPENROUTER_API_KEY REQUIRED` |
| Invalid API-key handling | IMPLEMENTED & TESTED | Unit test plus actual network request returned structured HTTP 401 | No valid-key comparison possible | No retry; safe message retained |
| Classification → conditional OCR branch | IMPLEMENTED & TESTED | `src/services/pipeline.py`; `test_non_ktp_stops_before_ocr` asserts OCR function is never called | Predictions on KTP/SIM/receipt/photo/screenshot/random were not run | Do not claim classification quality until actual inference |
| Actual classification predictions on required categories | BLOCKED | `data/test_manifest.csv` contains the categories with no prediction columns | No API key | Run `python scripts/evaluate.py` after credential setup |
| AI Vision OCR and prompt | IMPLEMENTED BUT NOT TESTED | `src/ai/ocr.py`, `src/ai/prompts.py`; prompt forbids guessing, requires null and JSON; no traditional OCR dependencies | External OCR response not observed | Requires authenticated inference |
| JSON parsing and validation | IMPLEMENTED & TESTED | `src/processing/json_parser.py`; tests cover normal JSON, fenced JSON, missing field, malformed JSON, null, unexpected field, invalid metadata, and empty response | None found after fix | Unexpected fields now fail closed; malformed OCR persists as `REVIEW_REQUIRED` |
| Normalization | IMPLEMENTED & TESTED | `src/processing/normalizer.py`; tests cover whitespace, leading-zero NIK, date, gender, RT/RW, citizenship, lifetime, and null | None found after fix | Raw-vs-normalized audit retained |
| NIK/business rules | IMPLEMENTED & TESTED | `src/validation/`; valid, length, numeric, impossible date/month, gender/date mismatch, missing NIK/gender, and null OCR tests | Century cannot always be resolved without OCR full year | Documented limitation; unclear evidence results in review |
| Official region validation | PARTIALLY IMPLEMENTED | `RegionReference`, `data/reference/README.md`; loaded-reference hit/miss behavior tested | Verified official machine-readable CSV is not bundled | Returns `NOT_CHECKED` until official data is imported |
| Format vs official identity verification | IMPLEMENTED & TESTED | `verification_scope=FORMAT_ONLY_NOT_DUKCAPIL_VERIFICATION`; UI/README notices | No Dukcapil verification API | Never claims registered identity |
| Database CREATE/INSERT/SELECT/FILTER/EXPORT | IMPLEMENTED & TESTED | SQLite schema/repository and tests; full-history query no longer capped at 1,000; classification model migration included | PostgreSQL adapter absent | SQLite remains implemented target; production adapter documented separately |
| Duplicate handling | IMPLEMENTED & TESTED | SHA-256 lookup and duplicate test | Advisory only, by design | Does not infer same person from identity fields |
| Privacy and secret handling | IMPLEMENTED & TESTED | `.gitignore`, in-memory image flow, `mask_nik`, safe logs, masked default export; scans found no `.env`, API token, real KTP, or evaluation output | Extracted PII remains in local SQLite by design | Protect DB access/storage; sensitive export requires confirmation |
| Operational analytics | IMPLEMENTED & TESTED | `pages/2_Analytics.py`, `src/services/analytics.py`; database-calculated KPI/failure/completeness/duration; six-page AppTest passed | Live charts contain no production observations yet | Values remain zero/N/A until processing occurs |
| Model metrics dashboard | IMPLEMENTED BUT NOT TESTED | Evaluation artifact loader and conditional metric UI | No actual inference artifact exists | Displays N/A, not fabricated metrics |
| Error Analysis | IMPLEMENTED & TESTED | `pages/5_Error_Analysis.py`, `operational_error_analysis`; tested denominators/scopes | FP/FN/OCR/API inference categories unavailable without evaluation | Database categories shown; inference categories explicitly N/A |
| 20-image testing framework | IMPLEMENTED & TESTED | 20 readable image files, 10 KTP-like/10 non-KTP, 10 ground-truth JSON, exact manifest schema; all source type `SYNTHETIC`; all images passed backend validation | These are not real-world quality evidence | Actual predictions intentionally absent |
| Automated evaluation | IMPLEMENTED & TESTED | `scripts/evaluate.py`, metric unit tests, manifest-integrity test | Runner not executed with valid API | No output/metric file created without inference |
| Edge-case resilience | IMPLEMENTED & TESTED | Tests for non-image, corrupt/tiny/oversized image, blur/rotate/crop fixtures, empty/invalid key, timeout, malformed response, null OCR, and database unavailable | External model behavior on visual edge cases blocked | UI fails safely; retry is bounded |
| Streamlit application | IMPLEMENTED & TESTED | `streamlit run app.py`; health endpoint returned `ok`; AppTest for home + five pages returned zero exceptions | Local Python emits a LibreSSL/urllib3 warning unrelated to app execution | Use a modern Python/OpenSSL runtime in deployment |
| Streamlit Community Cloud readiness | PARTIALLY IMPLEMENTED | Entrypoint, requirements, environment/secrets docs exist | SQLite filesystem may be non-durable; valid API key and standalone Git remote absent | Add secrets and durable DB adapter if persistence is required |

## Final gap analysis

| Requirement | Implementation | Testing | Status | Remaining Problem |
|---|---|---|---|---|
| Real classification | OpenRouter Vision adapter complete | Request construction, branching, errors tested; no successful inference | BLOCKED | Valid `OPENROUTER_API_KEY` required |
| Real OCR | Separate conditional AI Vision request complete | Parser/pipeline mocked integration tested; no successful inference | BLOCKED | Valid key and lawful input images required |
| Classification metrics | Accuracy/precision/recall/F1/confusion code complete | Deterministic metric unit tests passed | BLOCKED | No actual prediction rows |
| OCR metrics | Field accuracy/completeness/missing-rate code complete | Empty-ground-truth exclusion tested | BLOCKED | No actual OCR inference rows |
| Official region lookup | CSV loader and provenance contract complete | Loaded fixture behavior tested | PARTIALLY IMPLEMENTED | Current official CSV not imported |
| Production persistence | Repository abstraction and SQLite complete | Transaction/retrieval/error paths tested | PARTIALLY IMPLEMENTED | Cloud-durable PostgreSQL/Supabase adapter absent |
| Deployment | Local application starts and all pages render | Health/AppTest passed | PARTIALLY IMPLEMENTED | API secret, durable DB choice, and dedicated Git repository required |

## Commands and actual outcomes

```text
python3 -m pytest
43 passed

Clean virtual environment:
pip install -r requirements.txt
43 passed

Streamlit AppTest:
6 files, 0 exceptions

Streamlit server health:
ok

Invalid-key network test:
HTTP 401, structured error code 401

Actual evaluation:
BLOCKED — OPENROUTER_API_KEY REQUIRED
No evaluation_results.csv exists
```

The test totals above are execution outputs. Mocked AI responses validate control flow only and are not reported as actual model predictions.
