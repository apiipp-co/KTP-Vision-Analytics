# Portfolio and Interview Description

## One-line project description

Built a privacy-aware Streamlit pipeline that classifies Indonesian identity documents, conditionally extracts 18 KTP fields through OpenRouter Vision, validates them with deterministic rules, and exposes auditable analytics.

## CV — three bullets

- Designed a two-stage multimodal AI pipeline that gates structured OCR behind KTP classification, preserves unreadable fields as null, and versions model/prompt metadata for reproducibility.
- Implemented auditable normalization, NIK/date/gender validation, SQLite/PostgreSQL persistence, masked exports, duplicate-cost controls, and database-backed quality/error analytics.
- Built a balanced 20-image synthetic evaluation fixture set and 59-test pre-final regression suite; documented external metrics as N/A until a real OpenRouter run and production deployment are verified.

## LinkedIn / portfolio description

KTP Vision Analytics explores how to build document AI responsibly, not just how to call a vision model. The Streamlit application first classifies an authorized image and only runs OCR for KTP_INDONESIA. A strict 18-field JSON contract, null-for-unreadable policy, defensive parsing, deterministic Python validation, and raw-versus-normalized audit trail make uncertainty visible.

The data layer supports SQLite locally and PostgreSQL as a production target. Operational pages report observed completeness, validation mix, failures, latency, usage, and cost, while sensitive UI/export values are masked. I also generated a reproducible 20-image synthetic dataset, built automated regression/security checks, and performed a red-team review that corrected migration, duplicate-cost, metric-denominator, CSV-boolean, filtering, and UI-rendering defects.

I deliberately report model accuracy and live deployment as N/A/blocked until credentials, PostgreSQL, and Streamlit verification are available. That boundary is part of the engineering outcome.

## Interview story

Situation: KTP transcription needs automation, but unrestricted OCR can waste cost, invent missing values, and expose PII.

Task: Build a portfolio-grade document pipeline that is measurable, auditable, and honest about evidence.

Action: I separated classification from OCR, enforced structured output, normalized fields with provenance, implemented independent NIK/date/gender rules, designed local/production database adapters, added masked analytics and safe exports, created a synthetic ground-truth set, and red-teamed the implementation.

Result: The local system passes its regression and UI checks and presents a clear production path. More importantly, it refuses to present unexecuted AI evaluation or blocked deployment as a successful result.

## 30-second pitch

“I built KTP Vision Analytics, a Streamlit application that classifies a document before conditionally calling OpenRouter OCR. It extracts 18 fields into a strict schema, keeps unreadable values null, validates NIK/date/gender rules independently, stores an audit trail, and exposes masked quality analytics. I also built a reproducible synthetic evaluation set and red-teamed the system. The local engineering is verified; model metrics and deployment remain explicitly N/A until real credentials and infrastructure are tested.”

## 60-second pitch

“KTP Vision Analytics addresses two problems in document AI: models can invent data, and identity documents are sensitive. I designed a two-stage pipeline so non-KTP or uncertain images stop before OCR. KTP images enter a strict 18-field JSON contract where unreadable values must be null. Python then normalizes and validates NIK structure, birth date, gender, categories, and optional official region data independently from the model.

Results are stored with request, model, prompt, timing, usage, and field-audit metadata in SQLite locally or PostgreSQL as a production target. The Streamlit app provides masked history, quality, evaluation, and error analytics. A 20-image synthetic fixture set and automated tests cover routing, parsing, persistence, security, and evaluation math. I did not invent model accuracy or a live URL: both remain gated on actual OpenRouter and cloud verification.”

## Three-minute technical pitch

Start with the design constraint: the AI is an extraction component, not the authority.

The upload layer verifies actual JPG/PNG content, byte and decoded-pixel limits, EXIF orientation, and minimum resolution in memory. A hash check rejects duplicate production uploads before an AI call. The first model request performs only document classification using a closed schema. OTHER and UNCERTAIN are persisted and stop. KTP_INDONESIA enters a separate OCR request with 18 nullable fields.

The response passes through defensive JSON parsing and normalization. Every field keeps raw and normalized values. Deterministic rules then validate NIK structure, encoded date and gender, OCR consistency, supported categories, and optionally a current official region reference. Overall status can be VALID, INVALID, or REVIEW_REQUIRED, and VALID explicitly means format consistency—not Dukcapil verification.

The repository writes document, field, and rule evidence transactionally. It supports SQLite for local demos and PostgreSQL for the production target. Analytics are database-backed and do not invent latency or cost when the provider does not return them. Public surfaces mask multiple identity fields, images/raw responses are not stored, and CSV exports are safe by default.

For evaluation, I generated 20 clearly synthetic images with balanced classes, six conditions, hashes, consent metadata, and ground truth. The runner implements classification, OCR, performance, and error metrics, but current AI results remain N/A because no valid credential was available. The final red team caught and fixed issues in legacy migration, duplicate-cost control, boolean parsing, OCR denominators, filter propagation, and Streamlit rendering. The honest production verdict is NEEDS REVISION until external inference, PostgreSQL, deployment, RBAC, encryption, and retention are verified.

## Role-specific summaries

### Recruiter

An end-to-end AI/data application demonstrating product framing, Python engineering, Streamlit UX, databases, automated testing, security awareness, analytics, documentation, and honest readiness assessment.

### Business stakeholder

A controlled workflow that can reduce irrelevant OCR work and make manual review more consistent, while clearly exposing unresolved privacy and production risks. Financial benefit must be measured during a real pilot.

### Data analyst

A database-backed quality system with traceable denominators, field completeness, status distributions, trends, error taxonomy, dataset provenance, masked exports, and explicit N/A handling for unavailable evidence.

### AI engineer

A versioned two-stage vision pipeline with strict schemas, prompt-injection resistance, null-preserving extraction, defensive parsing, retry policy, model metadata, deterministic validation, repeatable evaluation, and separation of mocked integration tests from real model metrics.

### Backend / platform engineer

A layered repository with transactional SQLite/PostgreSQL adapters, legacy migration compatibility, partial uniqueness for request IDs, hash-based duplicate-cost control, cascaded deletion, secret scanning, CI, and a documented cloud runbook.
