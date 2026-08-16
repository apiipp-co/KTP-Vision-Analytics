# Final Project Report — KTP Vision Analytics

Document date: 17 August 2026
Project status: locally verified with completed 20-image OpenRouter evaluation; production deployment not yet published
Repository: apiipp-co/ktp-vision-analytics, private

## 1. Executive summary

KTP Vision Analytics is a Streamlit system that accepts an authorized identity-document image, verifies the image in memory, classifies it through OpenRouter Vision, calls structured OCR only for an Indonesian KTP, normalizes 18 fields, applies deterministic rules, stores auditable results, and exposes masked analytics.

The local application, automated controls, and synthetic OpenRouter evaluation are mature enough for a supervised technical demonstration. It is not yet production-ready because PostgreSQL connectivity, Streamlit deployment, authentication, encryption, and lawful representative real-world evaluation have not been verified.

## 2. Background

Manual identity-document transcription creates turnaround time, typing errors, inconsistent formats, and limited process visibility. Directly passing every image to OCR adds cost and may encourage false extraction from unrelated documents. KTP content also creates substantial privacy obligations.

The project addresses these issues through a classification gate, strict structured output, an independent rule layer, persistent audit evidence, and conservative disclosure.

## 3. Problem Definition

How can an authorized operator turn an Indonesian KTP image into structured, reviewable data while:

- avoiding OCR on non-KTP images;
- refusing to guess unreadable values;
- separating AI extraction from rule validation;
- controlling PII exposure and inference cost; and
- measuring actual quality without fabricating model results?

## 4. Objectives

The technical objectives are conditional OCR, a closed 18-field schema, auditable normalization, format-based validation, durable metadata, privacy-aware analytics, synthetic reproducibility, automated regression coverage, and a documented production path.

Completion is judged at two levels:

- local engineering readiness: code, tests, page rendering, data integrity, and security checks;
- external readiness: actual model evaluation, PostgreSQL verification, cloud deployment, and live end-to-end evidence.

The first level is verified. The second remains blocked.

## 5. System Requirements

The system covers upload, classification, OCR, parsing, normalization, validation, storage, analytics, export, data quality, evaluation tooling, and deployment checks.

It excludes official Dukcapil verification, proof of identity, biometrics, fraud detection, uploaded-image storage, and unsupervised public use. VALID is a format-consistency outcome, never government verification.

### Stakeholders and value

Potential stakeholders include authorized operations staff, data-quality analysts, AI engineers, security/privacy reviewers, and engineering managers.

The operational value is fewer irrelevant OCR calls, structured review evidence, consistent data formats, and visibility into missingness, failures, latency, and cost. Value cannot yet be quantified financially because no production volume, live model cost, or measured time saving was supplied.

### Functional requirements

The implemented workflow requires the user to:

1. acknowledge authorization and external AI processing;
2. upload a JPG or PNG;
3. process a new image hash;
4. receive KTP, OTHER, or UNCERTAIN classification;
5. receive OCR only when classified KTP;
6. inspect normalized fields and rule outcomes;
7. use history/analytics with masked sensitive fields;
8. export safe CSV by default; and
9. inspect dataset quality, evaluation, and error-analysis pages.

### Non-functional requirements

- Security: secrets outside Git, bounded image processing, prompt-injection resistance, parameterized SQL.
- Privacy: no image persistence, consent disclosure, masking, safe exports, limited logging.
- Reliability: retries only for transient external failures, transactions, migration compatibility, duplicate cost control.
- Maintainability: layered modules, prompt versions, configurable model/database, deterministic tests.
- Observability: request ID, timing, prompt/model versions, data context, usage/cost when provider-reported.
- Portability: local SQLite and PostgreSQL target; runtime and development dependencies separated.

## 6. System Architecture

~~~mermaid
flowchart TD
    UI["Streamlit UI"] --> IMG["Image security and normalization"]
    IMG --> DUP["Production duplicate gate"]
    DUP --> CLS["OpenRouter classifier"]
    CLS -->|"Not KTP"| DB["Repository transaction"]
    CLS -->|"KTP"| OCR["OpenRouter structured OCR"]
    OCR --> PARSE["Defensive parser"]
    PARSE --> NORM["Field normalization"]
    NORM --> RULES["Python rules"]
    RULES --> DB
    DB --> SQLITE["SQLite local/demo"]
    DB --> PG["PostgreSQL production target"]
    DB --> BI["Analytics, history, quality, errors"]
~~~

The architecture uses separation of concerns: UI does not contain model prompts; the model does not determine final rule status; analytics functions consume stored data; the repository hides SQL dialect differences.

## 7. AI Classification

Classification and OCR are distinct multimodal calls. This improves control, cost visibility, and error attribution. Classification requests a closed KTP_INDONESIA, OTHER, or UNCERTAIN contract. OTHER and UNCERTAIN stop before OCR.

The configured model is not hard-coded as a performance claim. Model, prompt version, request duration, usage, and provider-reported cost are stored when available. Self-reported confidence is accepted only within zero to one and is labeled as uncalibrated.

## 8. OCR Extraction

OCR runs only after a KTP classification. It requests strict JSON Schema, treats image text as untrusted, forbids guessing, and requires null for unreadable values. Raw model responses are not persisted.

The OCR contract contains NIK, name, birthplace/date, gender, address components, religion, marital status, occupation, citizenship, validity, province, city/regency, and blood type.

## 9. Data Processing

Normalization standardizes whitespace, dates, NIK characters, gender, citizenship, lifetime validity, and RT/RW while retaining raw and normalized values in extracted_fields. Empty evidence stays empty rather than being imputed.

## 10. Business Rule Validation

Rules check NIK presence, numeric content, length, encoded birth date, gender offset, OCR/NIK date consistency, OCR/NIK gender consistency, supported categories, and field availability. Region validation runs only when an official reference CSV with provenance is supplied.

Critical INVALID rules cause overall INVALID. Missing critical evidence causes REVIEW_REQUIRED. A complete consistent rule set may return VALID, with the explicit disclaimer that it is format-only.

## 11. Database Design

The documents table holds classification, normalized KTP fields, status, model/prompt metadata, duration, tokens/cost, timestamps, request ID, and PRODUCTION/EVALUATION context. extracted_fields stores field-level raw/normalized audit. validation_results stores rule evidence. processing_logs stores bounded operational messages.

Foreign-key cascades support document deletion. A partial unique request_id index supports idempotency. Production duplicates are rejected before an external call; evaluation duplicates are permitted.

SQLite migration order was corrected so legacy databases receive new columns before indexes referencing those columns are created.

## 12. Analytics Dashboard

The application calculates database-backed KPIs, distributions, time trends, field completeness, processing times, usage/cost, and operational insights. Filters are propagated to validation rows to avoid mismatched denominators.

Data-quality checks cover required columns, duplicate hashes, KTP missingness, and timestamps. Error analysis distinguishes classification, OCR, JSON, validation, and API failures and records denominator and scope.

## 13. Dataset & Testing

synthetic-v2.0.0 has 20 generated fixtures: ten KTP-like and ten non-KTP. Every image has a manifest row, source type, consent flag, condition, SHA-256, dataset version, and ground-truth reference where relevant.

Condition counts are clear 4, dark 4, rotated 4, low resolution 4, blur 2, and partially cropped 2. The set contains no real PII and is explicitly marked synthetic. It is suitable for pipeline tests but not for production generalization claims.

## 14. Evaluation Methodology

The evaluation runner verifies manifest schema, consent, file readability, and hash integrity. It processes every row in EVALUATION context and records failures rather than silently dropping them.

Classification metrics include accuracy, KTP precision, recall, F1, and confusion matrix. OCR metrics include per-field exact match on populated truth, character error rate, completeness, missing fields, and hallucination signals. Runtime metrics include latency and provider-reported usage/cost.

The versioned synthetic evaluation completed all 20 rows with the configured `dots-studio/dots-3-note-preview:free` model. Classification accuracy, precision, recall, and F1 were 100% on this controlled fixture set. OCR exact match was 139/140 populated ground-truth fields (99.29%), with 0.71% mean CER and 77.22% all-schema-field completeness. These results do not establish performance on real KTP photographs.

## 15. Results

The latest regression result is 64 passed. Tests cover model contracts, output/reasoning bounds, conditional orchestration, retries, malformed responses, image defenses, normalization, expiry and NIK/date/gender validation, persistence, migration, deletion, duplicate semantics, evaluation math, data integrity, masking, safe CSV, injection text, and missing-secret handling.

The Streamlit home plus seven page entry points were smoke-tested without exceptions. A real local server returned a healthy endpoint, and three actual non-PII screenshots were retained after visual QA.

Mocks verify application behavior but do not verify model quality. PostgreSQL and cloud execution remain unverified.

| Test category | Executed | Passed | Failed | Status |
|---|---:|---:|---:|---|
| Automated unit/integration tests | 64 | 64 | 0 | PASS |
| Streamlit entry-point smoke tests | 8 | 8 | 0 | PASS |
| OpenRouter AI evaluation rows | 20 | 20 | 0 | PASS (synthetic fixtures) |
| Live deployment matrix | 0 | 0 | 0 | BLOCKED / N/A |

## 16. Error Analysis

The Error Analysis page separates false positives, false negatives, OCR mismatches, missing fields, JSON errors, validation failures, and API failures. Every category includes a count, denominator, percentage, and scope where evidence exists. It does not assign blur, glare, rotation, or other causes unless the manifest or inspected evidence supports that conclusion.

The final red team found and fixed evaluation string-boolean parsing, the OCR completeness population, current error-column selection, analytics filter propagation, duplicate inference, legacy database migration, expiry validation, and unbounded model reasoning. The actual synthetic run contained zero classification/API/JSON failures and one OCR exact-field mismatch.

## 17. Data Analyst Findings

1. Data: 20 synthetic fixtures with balanced 10/10 classes and verified hashes. Analysis: class balance avoids a majority-class accuracy shortcut. Finding: the harness is reproducible. Decision: keep precision, recall, F1, and confusion matrix in addition to accuracy.
2. Data: six controlled image conditions. Analysis: condition metadata supports slices. Finding: the set exercises pipeline behavior but not population validity. Decision: do not generalize to real KTP performance.
3. Data: 20 prediction rows, balanced by class. Analysis: TP=10, TN=10, FP=0, FN=0; 139/140 populated OCR fields matched. Finding: the integration performs strongly on controlled synthetic fixtures. Decision: report these metrics with an explicit no-generalization warning.
4. Data: local persistence and page tests pass. Analysis: engineering controls work with deterministic inputs. Finding: local readiness is stronger than cloud readiness. Decision: require PostgreSQL and live restart/concurrency testing.
5. Data: sensitive extracted fields remain in the database. Analysis: UI masking does not protect storage. Finding: production privacy risk remains material. Decision: require RBAC, encryption, retention, and incident controls.

## 18. Security & Privacy

Strengths include in-memory images, secret isolation, PII masking, demo-safe exports, no raw response persistence, input limits, prompt-injection language, parameterized SQL, transactions, pre-deployment scanning, and explicit consent/disclosure.

Residual high-impact gaps are application authentication/RBAC, database/backup encryption, automated retention, key rotation, rate limits, audit-log governance, incident response, and a documented lawful production basis. Until implemented, any public deployment must remain synthetic/demo-only.

## 19. Deployment

The intended deployment is Streamlit Community Cloud with Python 3.12 and PostgreSQL. The repository is private and account-side publication still requires Streamlit GitHub access plus platform secrets. A local OpenRouter secret is configured but must be rotated because it was previously exposed; a production PostgreSQL URL is not configured.

No live URL is claimed. Deployment completion requires repository authorization, platform secrets, strict pre-deploy checks, build-log inspection, external inference, persistence/restart testing, concurrency checks, safe export checks, and a documented rollback.

## 20. Limitations

1. OpenRouter behavior is measured only on 20 controlled synthetic fixtures, not a lawful representative real-world dataset.
2. PostgreSQL and the Streamlit target are not live-tested.
3. Twenty synthetic fixtures do not represent real camera, demographic, print, damage, or fraud diversity.
4. Self-reported confidence is uncalibrated.
5. Region validation is unavailable until a current official reference is imported.
6. Authentication/RBAC, field encryption, automatic retention, and backup deletion are not implemented.
7. There is no reviewer correction workflow or production feedback loop.

## 21. Recommendations

| Risk | Impact | Current mitigation | Required next action |
|---|---|---|---|
| Model error or hallucination | Wrong identity data | synthetic evaluation, null policy, strict schema, rule layer, review status | Lawful representative evaluation and human review |
| PII exposure | Legal/security harm | no image persistence, masking, safe export | RBAC, encryption, retention, incident plan |
| Cost abuse/duplicates | Unplanned spend | hash rejection, bounded retries | Rate limit, quota, budget alerts |
| Synthetic-only evidence | Misleading performance | explicit N/A metrics and limitations | Lawful representative evaluation |
| Local database in cloud | Data loss | PostgreSQL adapter | Provision/test durable PostgreSQL |
| Private repo inaccessible | No deployment | documented blocker | Grant Streamlit app repository access |

Priorities are: first rotate the key and verify PostgreSQL/cloud deployment; second add production identity/access/privacy controls; third evaluate on a lawful representative dataset; finally add correction feedback, drift monitoring, rate limits, quotas, and cost alerts.

## 22. Conclusion

The project is a credible engineering portfolio artifact and a strong supervised local demonstration. It shows careful boundaries between AI, deterministic validation, storage, analytics, and privacy.

Final recommendation: READY FOR SUPERVISED DEMONSTRATION, but NEEDS REVISION before production approval. Rotate the exposed key, deploy with PostgreSQL, add production identity/access/privacy controls, and collect lawful representative evidence. Present the current metrics only as synthetic-fixture results and any local screenshot as local evidence.
