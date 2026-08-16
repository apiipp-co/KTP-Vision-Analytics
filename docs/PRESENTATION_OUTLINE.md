# Presentation Outline — 15 Slides

Target duration: 10–12 minutes plus Q&A.
Narrative: problem → control design → evidence → limitations → next decision.

## Slide 1 — Title

KTP Vision Analytics: controlled AI classification, OCR, validation, and analytics.

Speaker note: Open by saying this is a privacy-aware decision-support pipeline, not an official identity-verification service.

## Slide 2 — The problem

- manual transcription is slow and inconsistent;
- irrelevant images waste OCR calls;
- unreadable text can become hallucinated data;
- KTP content creates material privacy risk.

Speaker note: Keep the problem operational, not theoretical.

## Slide 3 — Design objectives

- classify before extracting;
- preserve uncertainty;
- validate independently;
- retain traceability;
- measure only actual evidence.

Speaker note: State the central principle: the AI extracts; Python rules decide format consistency.

## Slide 4 — Scope and non-goals

Show a two-column in/out table.

Speaker note: Explicitly rule out Dukcapil, biometrics, fraud detection, and production claims.

## Slide 5 — End-to-end architecture

Use the README flow diagram.

Speaker note: Emphasize conditional OCR and in-memory image handling.

## Slide 6 — Classification gate

KTP_INDONESIA continues; OTHER and UNCERTAIN stop.

Speaker note: Explain how this controls cost and false extraction. Mention production duplicate rejection before any AI call.

## Slide 7 — Structured OCR contract

Show the 18 field groups and null-for-unreadable rule.

Speaker note: Explain strict JSON Schema, prompt versioning, and image text as untrusted data.

## Slide 8 — Independent validation

Show NIK/date/gender/region/category rules and VALID/INVALID/REVIEW_REQUIRED.

Speaker note: Say VALID means format consistency only. Region is NOT_CHECKED without current official data.

## Slide 9 — Data model and audit trail

Show documents, extracted_fields, validation_results, processing_logs.

Speaker note: Highlight raw-versus-normalized audit, request ID, model/prompt metadata, and delete cascades.

## Slide 10 — Analytics and operational insight

Show the Analytics and Data Quality screenshots.

Speaker note: Metrics come from stored observations. Tokens/cost appear only when provider-reported.

## Slide 11 — Dataset

20 synthetic files, balanced 10/10, six conditions, hashes and ground truth.

Speaker note: This proves repeatability and safe testing, not real-world model performance.

## Slide 12 — Evaluation status

Display the completed synthetic run: 20/20 processed, 100% classification metrics, 139/140 populated OCR fields exact, and zero API/JSON errors.

Speaker note: State the boundary clearly: these are reproducible controlled-fixture results and must not be generalized to real KTP photographs.

## Slide 13 — Verification evidence

- 64 automated tests;
- eight Streamlit entry points without exceptions;
- local health check;
- dataset integrity pass;
- security/pre-deploy scanning.

Speaker note: Clarify that AI calls are mocked in tests.

## Slide 14 — Red-team findings and fixes

- legacy SQLite migration ordering;
- duplicate inference cost;
- false CSV boolean interpretation;
- OCR metric denominator;
- analytics validation filter;
- Data Quality rendering leak.

Speaker note: Explain one fix deeply, then summarize the rest.

## Slide 15 — Readiness verdict and roadmap

Verdict: NEEDS REVISION for production; strong local/portfolio evidence.

Next steps: rotate the exposed key, grant repository access, provision platform secrets/PostgreSQL, deploy/live-test, and add RBAC/encryption/retention.

Speaker note: End with a decision-ready ask: approve a controlled verification phase, not production release.

## Presentation delivery advice

- Spend most time on architecture, evidence, and trade-offs.
- Do not read all 18 fields or every rule.
- Keep N/A visible only for genuinely unavailable evidence such as live PostgreSQL/cloud behavior and production cost.
- Use one synthetic image only, and show the SYNTHETIC marking.
- If the API is unavailable, move immediately to the prepared fallback and explain why.
- Close with the exact blockers and ownership needed to resolve them.
