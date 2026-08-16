# Security and Privacy Audit

Audit date: 2026-08-16 (Asia/Jakarta)

## Data inventory and controls

| Data | Location/flow | Sensitivity | Control |
| --- | --- | --- | --- |
| Uploaded image | Browser → Streamlit memory → OpenRouter/provider | Critical PII | Consent gate, format/byte/pixel checks, no file persistence, removed from session result |
| NIK/name/address/birth data | Structured response → configured database | Critical PII | Parameterized SQL, masked UI/default CSV, raw export disabled in demo |
| Raw AI response | In-process only | Critical PII | Not persisted or logged |
| Document SHA-256 | Database | Linkable metadata | Used only for duplicate advisory |
| Request/model/duration/status | Database/logs | Low/medium | Safe metadata only; no request body/header/secret |
| Evaluation truth | Local synthetic JSON | Non-real fixture data | Version/hash/provenance; private paths ignored for real datasets |

## Threat review

| Threat | Control | Status |
| --- | --- | --- |
| Secret committed | `.env*`, `secrets.toml`, key files ignored; regex predeploy scan | PASS |
| Prompt injection printed in image | Classification/OCR prompts treat image text as untrusted data; strict output schema | IMPLEMENTED |
| Malformed/oversized/decompression-bomb image | Byte, MIME/content, minimum dimension, maximum pixel and Pillow verification | TESTED |
| Path traversal filename | Basename + character allowlist + length cap | TESTED |
| SQL injection | Parameterized values; fixed query structure | TESTED |
| CSV formula injection | `= + - @` prefixes neutralized in exports | TESTED |
| PII exposure in UI/export | Central NIK/name/address/date masking; demo disables raw export | TESTED |
| PII retained in session state | Stored result is deep-copied, image bytes removed and PII masked | IMPLEMENTED |
| PII in logs/errors | Sanitized error taxonomy and generic UI messages | TESTED |
| Evaluation/production mixing | Separate evaluation DB plus `data_context` column | IMPLEMENTED |
| Non-durable cloud SQLite | PostgreSQL adapter and production readiness warning | IMPLEMENTED; credential test blocked |

## Remaining risks

- OpenRouter and the selected downstream provider process uploaded data. Operators must review their current terms, retention controls, routing policy and lawful basis before real identity data is used.
- Application-level authentication/RBAC and field encryption are not implemented; a public deployment must remain demo-only with synthetic/anonymized data.
- Database backups and provider logs are outside this repository and require an operator retention/deletion policy.
- Consent UI records a user assertion; it is not legal verification.

Conclusion: local/demo privacy controls are implemented and tested. Processing real KTP data in public production remains `NOT READY` until access control, organizational/legal review, production database security, and live provider verification are complete.
