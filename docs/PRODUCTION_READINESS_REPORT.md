# Production Readiness Report

> Updated evidence note, 17 August 2026: OpenRouter evaluation now completed 20/20 synthetic rows with no API/JSON failures, and the regression suite passes 64 tests. Cloud/PostgreSQL deployment and real-PII production controls remain unverified.

Status: `DEPLOYMENT BLOCKED`

| Area | Score | Evidence/status |
| --- | ---: | --- |
| Build stability | 10/10 | Local dependency/test execution passes |
| Runtime stability | 9/10 | AppTest: home + 7 pages, zero exceptions; local health `ok`/HTTP 200; cloud unavailable |
| OpenRouter integration | 9/10 | 20/20 synthetic rows processed; 100% controlled-fixture classification; no API/JSON failures |
| Database persistence | 8/10 | SQLite tested; PostgreSQL adapter implemented; credential/live restart blocked |
| Security | 9/10 | Secret scan, safe SQL/log/export/image controls pass |
| Privacy | 9/10 | Consent/disclosure, masking, demo mode, no image persistence |
| Functional completeness | 9/10 | Conditional OCR, parser, validation, history, analytics implemented |
| Error handling | 9/10 | Safe taxonomy/retries/invalid input tests |
| Performance | 7/10 | Actual duration captured; production latency/cost unavailable |
| Demo readiness | 9/10 | 20 synthetic fixtures, reset and safe defaults |

This component checklist is superseded by the weighted final jury score of **79/100** in FINAL_JURY_REVIEW.md. The cap reflects unverified OpenRouter classification/OCR and deployment. Status remains BLOCKED/NOT READY because no production URL exists and critical OpenRouter/database/live flows have not been verified.

External blockers:

1. No valid `OPENROUTER_API_KEY` in the environment.
2. No production PostgreSQL `DATABASE_URL`.
3. GitHub remote exists at `apiipp-co/ktp-vision-analytics`, but it is private and the Streamlit GitHub App cannot currently see it; repository access or public visibility must be explicitly selected.
4. Streamlit Community Cloud is authenticated and the deployment form is reachable, but final app creation is blocked by repository access and missing runtime secrets.

Do not add a URL, badge, screenshot, accuracy, persistence result or live-test pass until these blockers are removed and the runbook is executed.

Latest local evidence:

- `python -m pytest -q`: 64 passed in the working environment.
- Previous clean-environment verification passed; rerun it at the release commit before cloud publication.
- `python -m compileall`: PASS.
- Streamlit AppTest: 8/8 entrypoints, zero exceptions.
- Local Streamlit server: health `ok`, root HTTP 200.
- Dataset integrity: 20/20 files readable with matching SHA-256.
- Predeploy secret patterns: no matches; `.env` and `secrets.toml` absent.
- GitHub: standalone private repository initialized, committed and pushed to `main`.
- Streamlit Cloud: authenticated; repository visibility/access validation blocks the Deploy button.
