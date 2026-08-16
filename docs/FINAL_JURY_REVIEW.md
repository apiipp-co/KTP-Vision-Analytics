# Final Jury Review

Project: KTP Vision Analytics
Review date: 16 August 2026
Review mode: repository-wide jury audit, red team, direct remediation, regression, documentation and presentation readiness
Reviewer score type: internal readiness score, not an official academic grade

## Final verdict

NOT FINAL — NEEDS IMPROVEMENT.

Final weighted score: 79/100 after applying the core-verification cap.

The unadjusted weighted score is 82.45/100. It is capped at 79 because AI classification/OCR have not been exercised with a valid OpenRouter credential and there is no verified live deployment. The project is a strong local engineering and portfolio artifact, but core external behavior cannot be approved from mocked tests alone.

Production decision: do not release. Approve only a controlled verification phase using synthetic/authorized data.

## Executive judgment

The project demonstrates professional engineering judgment in four areas:

1. AI is constrained by a classification gate, strict contracts, and null preservation.
2. Business validation is deterministic and explicitly separated from identity verification.
3. Data quality, errors, timing, usage, and cost are designed around observed evidence.
4. Privacy and truthfulness are treated as first-class requirements.

The decisive weaknesses are external evidence and production governance:

- no actual model prediction artifact;
- no actual classification/OCR quality, external latency, or cost result;
- private-repository access blocks Streamlit deployment;
- no production PostgreSQL connection test;
- no application authentication/RBAC, field encryption, or automated retention.

## Audit scope and method

The audit read application entry points, all pages, AI client/prompts/schemas, processing, validation, analytics, database adapters/repository, scripts, tests, configs, environment template, Git exclusions, dataset manifest, 20 image fixtures, ten ground-truth files, and previous reports.

The process was:

~~~text
Repository inventory
→ Requirement traceability
→ AI/OCR/rule/data/security review
→ Adversarial scenarios
→ Direct high-impact fixes
→ Regression and UI smoke tests
→ Documentation consistency
→ Weighted scoring and hard-gate decision
~~~

No real OpenRouter call, production database mutation, repository-visibility change, or fake deployment was performed without the missing credentials/authorization.

## Requirement traceability matrix

| Requirement | Implementation | Evidence | Test/evidence | Status |
|---|---|---|---|---|
| Image Upload | JPG/PNG content validation, limits, EXIF and resize | src/processing/image_processor.py; pages/1_Upload_KTP.py | image/security tests; local page capture | VERIFIED |
| KTP Classification | Closed KTP/OTHER/UNCERTAIN contract | src/ai/classifier.py; src/ai/prompts.py | mocked classifier and pipeline tests | IMPLEMENTED NOT VERIFIED |
| Non-KTP Rejection | OCR called only when is_ktp is true | src/services/pipeline.py | integration test asserts no OCR call | VERIFIED |
| OpenRouter Vision | Base64 image request, schema, retries | src/ai/openrouter_client.py | mocked retry/error tests | IMPLEMENTED NOT VERIFIED |
| AI OCR | Separate strict 18-field request | src/ai/ocr.py; src/ai/prompts.py | mocked pipeline/schema tests | IMPLEMENTED NOT VERIFIED |
| Structured JSON | strict schema plus defensive parser | src/ai/prompts.py; src/processing/json_parser.py | malformed/valid JSON tests | VERIFIED |
| Data Normalization | raw and normalized field audit | src/processing/normalizer.py | normalization tests | VERIFIED |
| NIK Validation | numeric, length, date, gender, consistency | src/validation/nik_validator.py | date/NIK edge tests | VERIFIED |
| Birth Date Validation | parsing and NIK/OCR comparison | src/validation/date_validator.py | valid/invalid/leap tests | VERIFIED |
| Gender Validation | category and encoded-day consistency | src/validation/nik_validator.py | male/female/mismatch tests | VERIFIED |
| Database Persistence | transactional SQLite and PostgreSQL adapters | src/database; src/services/pipeline.py | SQLite integration/migration tests; PostgreSQL untested | PARTIAL |
| Streamlit Dashboard | home plus seven functional pages | app.py; pages | 8 AppTest entry points, local health/screenshots | VERIFIED |
| OCR Result Display | normalized result and rules on upload page | pages/1_Upload_KTP.py | page smoke test; real result unavailable | IMPLEMENTED NOT VERIFIED |
| Validation Result Display | status/rule table | pages/1_Upload_KTP.py | mocked pipeline; page smoke | VERIFIED |
| Database History | masked table and safe export | pages/3_Database_History.py | masking/export tests | VERIFIED |
| 20+ Image Testing | 20 synthetic files and manifest | data/testing; data/test_manifest.csv | 20/20 integrity and hash validation | VERIFIED |
| Classification Evaluation | accuracy, P/R/F1 and confusion logic | scripts/evaluate.py; src/services/evaluation.py | deterministic metric tests; no predictions | IMPLEMENTED NOT VERIFIED |
| CSV Export | masked/sensitive gates, formula safety, UTF-8 BOM | pages/3_Database_History.py; src/utils/security.py | privacy/export tests | VERIFIED |
| Deployment | Streamlit target/runbook/config | docs/DEPLOYMENT_RUNBOOK.md; .streamlit | private repo/secrets block creation | BLOCKED |

Core gate result: NOT FINAL. Image upload, routing, JSON, rules, database, and Streamlit work locally; the external AI classification/OCR core is not verified with the real provider.

## Adversarial review

| Scenario | Expected behavior | Evidence | Result |
|---|---|---|---|
| Non-image renamed as JPG | Reject before AI | image content verification tests | PASS |
| Oversized/decompression-bomb image | Reject before full processing | byte/pixel/Pillow warning controls | PASS |
| Non-KTP upload | Persist classification, skip OCR | pipeline integration test | PASS |
| Identical production upload | Reject before paid classification | duplicate exception and call-count test | PASS |
| Repeated evaluation sample | Allow controlled repeat | EVALUATION-context test | PASS |
| Embedded “ignore prompt” text | Treat as document data | both prompts plus resilience assertion | PASS BY DESIGN |
| Malformed model JSON | Explicit failure, no fabricated fields | parser/pipeline tests | PASS |
| Timeout/429/5xx | Bounded retry | OpenRouter resilience tests | PASS |
| Invalid API key/bad request | Do not retry indefinitely | client error mapping tests | PASS |
| OCR field missing | Preserve null and review state | schema/normalization/rules | PASS |
| CSV value starts with formula prefix | Neutralize before download | security tests | PASS |
| Legacy SQLite without new columns | Add columns before dependent indexes | migration regression test | PASS |
| String “False” in evaluation CSV | Parse as false, not truthy | evaluation regression test | PASS |
| False-positive non-KTP with present fields | Exclude from KTP OCR completeness | evaluation regression test | PASS |
| Analytics filter narrows documents | Narrow validations to same IDs | page code review and smoke | PASS |
| Data Quality success expression | Do not render internal DeltaGenerator | browser visual recheck | PASS |
| Unauthorized public user | Must be denied | no auth/RBAC exists | FAIL / PRODUCTION BLOCKER |
| Database or backup compromise | Sensitive values protected | no field-level encryption exists | PARTIAL / BLOCKER |
| Cloud restart with SQLite | History persists | Community Cloud local file not durable | FAIL BY TARGET DESIGN |
| Actual OpenRouter behavior | Correct output and performance | no valid key/prediction artifact | BLOCKED |

## High-impact findings and remediation

### F-01 — Legacy SQLite migration could fail

Severity: High.

Finding: schema initialization attempted to create indexes for request_id and data_context before adding those columns to an older documents table.

Impact: an existing installation could fail at startup during upgrade.

Fix: dependent indexes are now created only after the ALTER migration. A legacy-schema test reproduces and guards the sequence.

Status: fixed and verified.

### F-02 — Duplicate production files could spend AI budget again

Severity: High.

Finding: duplicate hashes were advisory only and classification still ran.

Impact: repeated uploads could create avoidable external cost and duplicate data.

Fix: production context raises DuplicateDocumentError immediately after safe image/hash validation and before classification. Evaluation context defaults to allowing repeats.

Status: fixed and verified with AI call counts and row counts.

### F-03 — CSV string booleans could inflate evaluation

Severity: Critical for measurement integrity.

Finding: generic truth conversion treats the non-empty string “False” as truthy.

Impact: exact-match and classification reporting could be optimistic when reading CSV artifacts.

Fix: a strict nullable boolean parser now accepts explicit true/false representations only.

Status: fixed and regression-tested.

### F-04 — OCR completeness used the wrong population

Severity: High.

Finding: predicted-KTP rows could include false-positive non-KTP documents in OCR completeness.

Impact: OCR measurement mixed in ineligible ground truth and used an ambiguous denominator.

Fix: OCR completeness and missing-field rates now use rows that are both actual KTP and predicted KTP, with observed boolean cells only.

Status: fixed and regression-tested.

### F-05 — Current evaluation column names were not preferred

Severity: Medium.

Finding: error metrics favored legacy validation/error columns.

Impact: new evaluation artifacts could undercount validation or API errors.

Fix: validation_status and error_type are used first, with backward-compatible fallback.

Status: fixed.

### F-06 — Analytics validation rows ignored active filters

Severity: Medium.

Finding: document filters changed KPIs but did not narrow validation data.

Impact: dashboard denominators could refer to different populations.

Fix: validations are restricted to filtered document IDs.

Status: fixed and page-smoke verified.

### F-07 — Data Quality rendered an internal component object

Severity: Medium.

Finding: a top-level conditional expression triggered Streamlit magic and displayed a DeltaGenerator representation.

Impact: visible UX defect and internal implementation leakage.

Fix: replaced the expression with explicit if/else calls; recaptured the page.

Status: fixed and visually verified.

### F-08 — Runtime dependencies included pytest

Severity: Low.

Finding: production installs included test tooling.

Impact: unnecessary deployment surface and package weight.

Fix: requirements.txt now contains runtime dependencies; requirements-dev.txt composes runtime plus pytest; CI uses the development file.

Status: fixed.

### F-09 — Pre-deploy scanning skipped output text

Severity: Medium.

Finding: the scanner ignored outputs entirely.

Impact: an accidentally staged text artifact might avoid repository scanning.

Fix: outputs are no longer excluded from the text scan; Git ignore remains the primary prevention.

Status: fixed and scan passed.

### F-10 — Sensitive CSV encoding and masking clarity

Severity: Low.

Finding: CSV downloads lacked an explicit BOM and documentation understated masked fields.

Impact: weaker spreadsheet compatibility and ambiguous privacy communication.

Fix: masked and gated sensitive downloads use UTF-8 BOM; About documentation names NIK, name, address, birthplace, and birth date.

Status: fixed.

## AI classification review

Strengths:

- closed three-value type system;
- is_ktp is cross-checked with KTP_INDONESIA;
- optional bounded confidence;
- reason length limit;
- prompt-injection warning;
- whole-document visual instruction;
- conditional OCR test coverage.

Limitations:

- no real-provider response captured;
- no confusion matrix, accuracy, precision, recall, or F1;
- no calibrated threshold or abstention evaluation;
- configured model capability may change and must be reverified.

Judgment: well-designed integration, insufficient empirical proof.

## AI OCR review

Strengths:

- separate request and prompt;
- 18 nullable fields and no additional properties;
- null preservation and anti-guessing;
- strict provider parameters;
- defensive parser;
- raw/normalized audit;
- no raw response persistence.

Limitations:

- no actual per-field result, CER, completeness, missing/hallucination rate;
- synthetic typography is not real KTP camera variation;
- no reviewer correction interface or feedback loop;
- no model comparison.

Judgment: robust contract, unverified extraction quality.

## Business validation review

The validation layer is one of the strongest parts of the project. It uses Python date semantics, including leap-year behavior; separates INVALID from NOT_CHECKED; derives NIK date/gender carefully; and states its scope.

The century heuristic can remain ambiguous when OCR year is absent. Region checking is intentionally disabled without a current official reference. Both are correctly disclosed.

Judgment: strong for format consistency, intentionally not identity verification.

## Data engineering and analytics review

Data strengths include transactions, parameterized queries, unique request IDs, data-context separation, cascades, raw/normalized audit, provider metadata, migration compatibility, and dialect abstraction.

Analytics strengths include explicit denominators, N/A states, filtered validation populations, completeness, quality/error taxonomies, and provider-only usage/cost.

Remaining concerns are untested production PostgreSQL behavior, potentially sensitive normalized columns, no schema migration framework beyond idempotent SQL, and no automated retention/archive layer.

## Security and privacy verdict

Implemented:

- secret isolation and Git ignore;
- consent/external-provider disclosure;
- no uploaded-image or raw-response persistence;
- input content/size/pixel checks;
- PII masking and safe CSV;
- parameterized SQL/transactions;
- prompt-injection language;
- duplicate cost guard;
- deletion API;
- repository secret/PII-pattern scan.

Not implemented or not verified:

- login, RBAC, tenant isolation, and session authorization;
- application field encryption and managed key rotation;
- automatic retention and backup deletion;
- production network/database TLS verification;
- rate limit, user quotas, abuse protection, and budget alarms;
- security monitoring, incident response, privacy impact assessment, and processor agreements.

Security conclusion: acceptable for a controlled synthetic local demonstration, insufficient for real-PII public production.

## Actual evidence

| Evidence area | Actual result |
|---|---|
| Unit/integration tests | 59 executed, 59 passed, 0 failed |
| Python compilation | PASS |
| Streamlit AppTest | 8 entry points, 0 exceptions |
| Local server | Health endpoint previously returned ok; three retained actual local captures |
| Pre-deploy scan | PASS_WITH_BLOCKERS; no secret files/pattern matches; dataset pass |
| Evaluation dataset | 20 total: 10 KTP-like, 10 non-KTP |
| Dataset conditions | CLEAR 4, DARK 4, ROTATED 4, LOW_RESOLUTION 4, BLUR 2, PARTIALLY_CROPPED 2 |
| Dataset integrity | PASS, issues 0 |
| Classification accuracy | N/A |
| Classification precision/recall/F1 | N/A |
| OCR field accuracy/completeness/CER | N/A |
| External latency/token/cost | N/A |
| SQLite | Local connection and integration tests PASS |
| PostgreSQL | Implemented, not connection-tested |
| Deployment | BLOCKED |
| Live URL | N/A |
| Git repository | Private main repository pushed; Streamlit app access missing |

## Category scores

| Category | Score | Weight | Weighted points | Rationale |
|---|---:|---:|---:|---|
| Requirement Compliance | 82 | 10% | 8.20 | Most requirements implemented; external AI/deployment incomplete |
| AI Classification | 74 | 7% | 5.18 | Sound contract/routing, no empirical classification proof |
| AI OCR | 72 | 8% | 5.76 | Strong schema/controls, no actual extraction evidence |
| Business Rule Validation | 91 | 8% | 7.28 | Transparent, tested, scoped validation |
| Data Engineering | 89 | 5% | 4.45 | Strong transactions/audit/migration; PostgreSQL unverified |
| Data Analysis | 87 | 8% | 6.96 | Database-backed metrics, denominators, N/A handling |
| Model Evaluation | 69 | 8% | 5.52 | Good harness/math, zero model predictions |
| Error Analysis | 83 | 5% | 4.15 | Useful taxonomy/scope; real errors unavailable |
| Software Architecture | 92 | 5% | 4.60 | Clear boundaries and configurable adapters |
| Code Quality | 90 | 4% | 3.60 | Cohesive modules and direct fixes |
| Testing | 93 | 7% | 6.51 | 59 deterministic tests plus page/compile checks |
| Security & Privacy | 88 | 7% | 6.16 | Excellent demo controls; production IAM/encryption missing |
| UI/UX | 88 | 3% | 2.64 | Clear multi-page UI, N/A/consent states, visual QA |
| Deployment | 45 | 5% | 2.25 | Config/runbook exist, no live deployment |
| Documentation | 95 | 4% | 3.80 | Comprehensive and evidence-conscious |
| Business Value | 86 | 3% | 2.58 | Clear operational value, benefits not measured |
| Presentation Readiness | 95 | 2% | 1.90 | Full outline, demo/fallback, 60 Q&A |
| Portfolio Value | 91 | 1% | 0.91 | Strong breadth and engineering judgment |
| Total |  | 100% | 82.45 | Unadjusted weighted score |

Calculation:

    Σ(category score × category weight) = 82.45
    Core external AI and live deployment not verified → maximum final score 79
    Final weighted score = min(82.45, 79) = 79/100

Score interpretation: 70–79 = NEEDS IMPROVEMENT.

## Top strengths

1. Clear AI-versus-rules responsibility boundary.
2. Conservative uncertainty, N/A, and privacy treatment.
3. Reproducible synthetic fixtures with hashes and truth.
4. Database-backed audit and analytics architecture.
5. Strong deterministic regression coverage.
6. Honest deployment/evaluation reporting.

## Top weaknesses

1. No real OpenRouter classification/OCR evidence.
2. No live PostgreSQL-backed deployment or URL.
3. No authentication/RBAC for real PII.
4. No field/backup encryption and automated retention.
5. Synthetic dataset cannot support external validity.
6. No reviewer correction/feedback workflow.

## Prioritized improvement roadmap

### P0 — Required before score-cap removal

1. Grant scoped Streamlit GitHub App access to the private repository.
2. Provision a restricted OpenRouter key and TLS PostgreSQL secret.
3. Run the strict pre-deployment check.
4. Execute the versioned 20-image evaluation and preserve immutable artifacts.
5. Deploy and run the complete live matrix, including restart/persistence and duplicate behavior.
6. Record dated URL, commit SHA, model ID, prompt versions, dataset version, results, and logs.

### P1 — Required before real-PII production

1. Add authentication, RBAC, least privilege, and session controls.
2. Add database/field encryption, managed keys, rotation, and backup deletion.
3. Define retention, lawful basis, access review, audit logging, and incident response.
4. Add rate limiting, user quotas, concurrency control, and cost alerts.
5. Add a human-review/correction queue and correction audit trail.

### P2 — Required for credible model claims

1. Build a lawful, consented, anonymized, representative dataset.
2. Compare eligible models with the same prompts/contracts.
3. Report confidence intervals and condition/subgroup error slices.
4. Calibrate abstention/review thresholds.
5. Monitor drift and rerun evaluation on every model/prompt change.

## Likely jury questions

1. Why does VALID not mean verified identity?
2. How do you prove OCR stops for non-KTP?
3. Why are all model metrics N/A?
4. What exact evidence removes the 79-point cap?
5. How is PII protected while using an external provider?
6. Why is SQLite unacceptable on Community Cloud?
7. How did the red team prevent optimistic metrics?
8. What happens to duplicate uploads and their cost?
9. Which controls are still missing for public use?
10. How would you evaluate model robustness beyond synthetic images?

Full prepared answers are in docs/QNA_PREPARATION.md.

## Presentation recommendation

Recommended order:

1. operational problem;
2. boundary/non-goals;
3. classification gate;
4. strict OCR and null policy;
5. deterministic validation;
6. data/audit/analytics;
7. actual test and dataset evidence;
8. N/A model/deployment evidence;
9. red-team fixes;
10. production decision and roadmap.

Avoid:

- calling the application “identity verification”;
- showing synthetic output without labeling it synthetic;
- calling mocked tests a model evaluation;
- adding a live URL before deployment verification;
- presenting self-reported confidence as calibrated;
- discussing cost saving as measured without a real baseline.

## Final consistency checklist

| Check | Result |
|---|---|
| README test count matches regression | PASS — 59 |
| Dataset counts match metadata/manifest | PASS — 20, 10/10 |
| AI metrics shown as N/A everywhere | PASS |
| Deployment shown as blocked; URL absent | PASS |
| Screenshots labeled local/synthetic/empty | PASS |
| Validation disclaimer present | PASS |
| Runtime/dev dependencies separated | PASS |
| Sensitive artifacts ignored/scanned | PASS |
| Historical reports identified as superseded | PASS after final report updates |

## Final recommendation

For a portfolio or jury demonstration: APPROVE, with transparent disclosure of N/A model metrics and blocked deployment.

For a controlled technical pilot: CONDITIONAL APPROVAL after OpenRouter/PostgreSQL/live verification with synthetic data.

For public or real-PII production: REJECT until P0 and P1 controls are complete and independently reviewed.
