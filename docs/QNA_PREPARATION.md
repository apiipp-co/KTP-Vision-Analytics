# Jury Q&A Preparation

Use short answers first, then expand only when asked. Report measured synthetic results with their scope; never replace unavailable production evidence with an estimate.

## Problem and product

### 1. What problem does this solve?

It reduces manual KTP transcription and makes extraction quality auditable while controlling irrelevant OCR calls and PII exposure.

### 2. Who is the user?

An authorized operations or data-quality user. It is not designed as an anonymous public identity-checking service.

### 3. What is the one-sentence value?

It turns authorized KTP images into reviewable structured data while controlling AI cost, uncertainty, and privacy risk.

### 4. Why not use one OCR call for every image?

Classification first prevents false extraction from unrelated images, makes errors easier to diagnose, and avoids unnecessary OCR spend.

### 5. Is this an identity-verification system?

No. It validates configured format consistency and never confirms a person against Dukcapil.

### 6. What is outside scope?

Dukcapil lookup, fraud detection, liveness, biometrics, face/signature checks, and proof that the document or person is genuine.

## AI and prompts

### 7. Why OpenRouter?

It offers one configurable multimodal interface and model routing while preserving a single client abstraction. The project still records the selected model and prompt versions.

### 8. Why a multimodal model instead of traditional OCR?

The project requirement is document classification plus schema-constrained visual extraction. The architecture remains model-configurable and measures results rather than assuming superiority.

### 9. How do you prevent hallucination?

The prompt forbids guessing, unreadable fields must be null, the JSON schema is closed, and Python rules flag missing or inconsistent evidence. Hallucination cannot be eliminated, so human review remains necessary.

### 10. How do you resist prompt injection in an image?

Both prompts explicitly treat all image text as untrusted data and reject embedded instructions. Tests also assert this control exists.

### 11. Why is confidence optional?

The provider may not produce a meaningful calibrated probability. The application stores confidence only when numeric and within zero to one, and labels it self-reported.

### 12. What happens when classification is uncertain?

UNCERTAIN is treated as not KTP for routing, so OCR stops and the classification record is stored for review.

### 13. What happens when JSON is malformed?

The defensive parser attempts bounded extraction of a JSON object and validates required shape. Failure becomes an explicit processing error, not a partial silent success.

### 14. What happens when OpenRouter times out?

Timeouts, network faults, rate limits, and server failures receive bounded exponential retries. Authentication and bad-request failures are not retried.

### 15. Can the model be changed?

Yes, through OPENROUTER_MODEL, provided it supports image input and the requested structured-output behavior. A new model requires a new versioned evaluation.

### 16. Why two prompt versions?

Classification and OCR have different responsibilities and can evolve independently. Their versions are stored for reproducibility.

## Data and rules

### 17. Why is NIK stored as text?

It is an identifier, not a number for arithmetic. Text preserves leading zeros and prevents spreadsheet/scientific-notation damage.

### 18. Which fields are extracted?

Eighteen fields covering identity, birth, gender, address, civil status, citizenship, validity, region, and blood type.

### 19. Why keep raw and normalized values?

It supports auditability: reviewers can see exactly how whitespace, dates, categories, or RT/RW were transformed.

### 20. How is the NIK validated?

The rules check availability, 16 numeric characters, encoded birth date, female day offset, and consistency with OCR birth date and gender.

### 21. Why can region be NOT_CHECKED?

The project refuses to fabricate a region map. It only checks a current official reference imported with provenance.

### 22. What does VALID mean?

Only that configured critical format rules are consistent. It does not mean the NIK exists or that Dukcapil verified it.

### 23. When is REVIEW_REQUIRED returned?

When critical evidence is missing or a critical rule cannot be checked safely.

### 24. Why not auto-fill missing fields?

Imputation would hide uncertainty in sensitive identity data. Missing evidence must remain visible.

## Database and analytics

### 25. Why support both SQLite and PostgreSQL?

SQLite gives a zero-service local/demo setup. PostgreSQL is the durable concurrent production target.

### 26. Is SQLite safe on Streamlit Cloud?

Not as durable storage. Local cloud files may be ephemeral, so production history requires PostgreSQL.

### 27. How are duplicate uploads handled?

Production checks SHA-256 after image validation and rejects an existing hash before any classification call. Evaluation allows repeats intentionally.

### 28. How is idempotency handled?

Each request has a request ID with a unique partial index. The hash gate also prevents duplicate production inference.

### 29. What data is stored?

Classification, normalized fields, field audit, rule results, timing, model/prompt versions, usage/cost when returned, timestamps, request ID, and data context. Image bytes and raw AI responses are not stored.

### 30. Can a record be deleted?

Yes, repository deletion removes the document and cascades to field and validation rows. Backup deletion still needs an operational policy.

### 31. Where do dashboard metrics come from?

From persisted database rows after filters. No metric is hard-coded.

### 32. How do you avoid misleading cost metrics?

Token and cost values appear only when the provider returns them; absent values remain absent.

## Evaluation and testing

### 33. What is the dataset?

Twenty project-generated synthetic images: ten KTP-like and ten non-KTP, with six conditions, hashes, consent metadata, and ground truth.

### 34. Why only synthetic data?

It avoids exposing real PII and makes the repository reproducible. It is deliberately not claimed as representative of production.

### 35. What is the current classification accuracy?

100% on the 20-image balanced synthetic-v2.0.0 set: TP 10, TN 10, FP 0, FN 0. This is controlled integration evidence, not an estimate of real-world KTP accuracy.

### 36. Why should we trust a project with no model score?

Trust the demonstrated controls, reproducibility, and versioned synthetic run. Production trust still requires a lawful representative dataset, human review, and live operational evidence.

### 37. Which metrics will you report?

Accuracy, KTP precision/recall/F1, confusion matrix, per-field exact match, character error rate, completeness, missing/hallucination indicators, latency, tokens, and cost.

### 38. Why exclude empty truth from exact match?

An unavailable expected value contains no correctness evidence. Counting it as correct would inflate accuracy.

### 39. What do the automated tests prove?

They prove deterministic application behavior with mocked AI responses: routing, parsing, rules, persistence, security, and metrics. They do not prove external model accuracy.

### 40. What was the latest test result?

Before final packaging, 59 tests passed. The final jury report records the final clean-environment count.

### 41. What red-team defects did you find?

Legacy SQLite index ordering, paid duplicate calls, CSV string-booleans, an OCR denominator issue, an analytics filter mismatch, and a Streamlit rendering leak.

### 42. What is the most important fix?

The evaluation fix: string “False” values are no longer truthy and OCR completeness is restricted to actual-and-predicted KTP rows, preventing optimistic metrics.

## Security and privacy

### 43. Is PII sent outside the application?

Yes, an authorized uploaded image is sent to the configured OpenRouter provider. The UI discloses this and requires acknowledgment.

### 44. Do you store the image?

No. It is processed in memory and discarded after the request.

### 45. How is PII protected in the UI?

NIK, name, address, birthplace, and birth date are masked on public/history/export surfaces by default.

### 46. Is the database encrypted?

Not at the application-field layer. Production requires platform/storage encryption, controlled keys, and preferably field-level protection for sensitive values.

### 47. Does the app have login or RBAC?

No. That is a production blocker; any current demonstration must use synthetic data in a controlled environment.

### 48. How do you prevent secrets from leaking?

Environment/platform secrets, Git exclusions, bounded logs, no raw responses, a repository scanner, and CI pre-deploy checks.

### 49. What about CSV formula injection?

Dangerous leading characters are neutralized, sensitive columns are masked by default, and files use UTF-8 BOM for spreadsheet compatibility.

### 50. What is the retention policy?

The code supports record deletion, but the organization must define and enforce retention, backup deletion, and legal-hold procedures before production.

## Deployment and readiness

### 51. Is there a live URL?

No. The local app and OpenRouter evaluation work, but Streamlit Cloud publication and production PostgreSQL are not yet configured.

### 52. Why not make the repository public immediately?

Visibility is an owner/security decision. The correct action is to grant scoped app access or approve a public portfolio strategy, not change it silently.

### 53. What remains before deployment?

Repository authorization, a rotated OpenRouter key, PostgreSQL URL, successful cloud build, persistence/restart, concurrency, privacy, and rollback verification. The local strict pre-deploy check and synthetic inference already pass.

### 54. Is the project production-ready?

No. It is locally verified and portfolio-ready with synthetic model evidence, but still needs deployment proof, lawful representative evaluation, RBAC, encryption, and retention controls.

### 55. What would you do first with one more day?

Rotate the exposed key, unblock scoped repository access, deploy with PostgreSQL, and collect dated live evidence.

### 56. What would you do with one more sprint?

Add authentication/RBAC, encryption, retention jobs, human-review correction flows, observability, budgets/rate limits, and a lawful representative evaluation set.

### 57. What is the final jury verdict?

NEEDS REVISION for production approval, with strong value as an engineering portfolio and supervised local demo.

### 58. What is the biggest architectural strength?

Uncertainty and responsibility are separated: classification gates OCR, extraction remains schema-bound, validation is deterministic, and evidence is persisted.

### 59. What is the biggest weakness?

The largest gap is external validity and production infrastructure: the model was measured only on synthetic fixtures, and there is no live PostgreSQL-backed deployment.

### 60. What decision are you asking the jury to make?

Approve a controlled verification phase and the remaining security work, not an unrestricted production release.
