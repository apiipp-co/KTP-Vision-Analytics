# Streamlit Community Cloud Deployment Runbook

Target: Streamlit Community Cloud, `app.py`, Python 3.12, `DEMO_MODE=true` for public portfolio use.

## Pre-deploy gate

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/predeploy_check.py --require-secrets --require-persistent-database
streamlit run app.py
```

Required platform secrets:

```toml
OPENROUTER_API_KEY = "your_api_key_here"
OPENROUTER_MODEL = "google/gemini-2.5-flash"
DATABASE_URL = "your_postgresql_database_url_here"
OPENROUTER_TIMEOUT_SECONDS = 90
OPENROUTER_MAX_RETRIES = 2
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_PIXELS = 20000000
APP_ENV = "production"
DEMO_MODE = true
ALLOW_SENSITIVE_EXPORT = false
```

Never commit the values. Use Streamlit Advanced settings/Secrets. Grant the database user only the required schema privileges and require TLS where supported.

## Live verification matrix

Record actual evidence; `PASS` is prohibited until observed on the production URL.

| Test | Expected | Current production status |
| --- | --- | --- |
| Build/startup | App loads without traceback | NOT TESTED |
| Database connection | `CONNECTED` and schema initializes | NOT TESTED |
| Database persistence | Record survives app restart | NOT TESTED |
| Home/navigation | All pages load | NOT TESTED |
| Consent gate | Process button disabled before consent | NOT TESTED |
| Safe KTP fixture | Classification → OCR → validation → save | NOT TESTED |
| Non-KTP fixture | Classification only; OCR not executed | NOT TESTED |
| Corrupt/wrong/large image | Friendly error, zero API call | NOT TESTED |
| Duplicate/rerun | No automatic repeat API request or insert | NOT TESTED |
| History | Masked PII, filters/pagination work | NOT TESTED |
| Analytics/evaluation/quality | Real DB data or explicit empty state | NOT TESTED |
| CSV | UTF-8, masked, formula-safe | NOT TESTED |
| Logs | No secret, image, NIK, address or raw OCR | NOT TESTED |
| Mobile viewport | No blocking overflow; upload usable | NOT TESTED |

After testing, compare API usage/request IDs with intentional clicks, verify dashboard totals against `COUNT(documents)`, reboot the app to prove persistence, and inspect logs once more.

## Rollback and incident handling

- Revoke/rotate any exposed OpenRouter or database credential; deleting it from Git is insufficient.
- Disable the app or switch it private if PII exposure is suspected.
- Preserve only sanitized request IDs/timestamps for investigation.
- Correct the repository, rerun the local gate, redeploy, and repeat the full matrix.
