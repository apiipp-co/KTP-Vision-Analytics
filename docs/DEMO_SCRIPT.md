# Demo Script — 3 to 5 Minutes

## Preconditions

- Run locally with streamlit run app.py.
- Use only a file from data/testing.
- If a valid OpenRouter key is not configured, do not click Process Document and imply a real result.
- Keep the Model Evaluation page open as factual fallback evidence.

## 0:00–0:30 — Frame the demo

Say:

“This application converts an authorized KTP image into structured, reviewable data. It is not Dukcapil verification. The key design is that classification happens before OCR, and deterministic Python rules remain separate from AI extraction.”

Show the Home page and point to the pipeline summary and current empty/local KPI state.

## 0:30–1:15 — Upload and consent

Open Upload KTP.

Say:

“Before processing, the user must confirm authorization and acknowledge that the image is sent to an external AI provider. The image is validated and resized in memory; the original bytes are not stored.”

Select a clearly marked synthetic KTP fixture. Point out the SYNTHETIC / BUKAN DOKUMEN RESMI marking.

## 1:15–2:10 — Explain the controlled path

If a valid OpenRouter key is available:

1. enable the consent control;
2. click Process Document once;
3. narrate image validation, duplicate check, classification, conditional OCR, parsing, normalization, validation, and storage;
4. show the request ID, classification, normalized fields, and rule results;
5. repeat the disclaimer that confidence is model-reported and VALID is format-only.

If no valid key is available:

Say:

“External inference is intentionally not demonstrated because no valid credential is available. The application fails safely instead of showing fabricated output. The automated suite tests the same orchestration with controlled mock responses.”

Do not present a static result as live.

## 2:10–3:00 — Analytics and audit

Open Analytics and Database History.

Say:

“These pages are database-backed. Filters, completeness, failures, processing time, usage, and cost are derived only from stored observations. Sensitive fields are masked, and default CSV export is spreadsheet-safe.”

If the database is empty, say so plainly. Do not invent operational insights.

## 3:00–3:40 — Dataset and evaluation

Open Data Quality, then Model Evaluation.

Say:

“The evaluation fixture set contains 20 generated images, balanced ten KTP-like and ten non-KTP, with six image conditions, hashes, consent metadata, and ground truth. Dataset validation passes. Model metrics remain N/A because no paid OpenRouter evaluation has been executed.”

## 3:40–4:30 — Red-team proof

Summarize:

- 59 tests before final packaging;
- duplicate files stop before a paid production call;
- malformed JSON and transient failures are covered;
- legacy SQLite migrations are tested;
- prompt-injection text inside images is treated as data;
- no image or raw AI response is persisted.

## 4:30–5:00 — Close

Say:

“The local engineering artifact is ready for supervised demonstration, but production approval is not requested today. The remaining gates are actual OpenRouter evaluation, Streamlit deployment with PostgreSQL, and production authentication, encryption, and retention controls.”

## Backup plan

If the app or network fails:

1. show the retained dated local screenshots in docs/screenshots;
2. show the architecture in README;
3. show the latest test command output;
4. show Model Evaluation N/A;
5. state the failure honestly and continue with the evidence package.

Screenshots are backup UI evidence, never simulated live inference.
