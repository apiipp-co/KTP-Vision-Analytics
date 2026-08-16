from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import database_from_url
from src.services.dataset import validate_manifest
from src.utils.config import Settings


TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".yml", ".yaml", ".json", ".csv", ".example"}
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}


def check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"check": name, "status": status, "detail": detail}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-secrets", action="store_true")
    parser.add_argument("--require-persistent-database", action="store_true")
    args = parser.parse_args()
    cfg = Settings.from_env()
    results: list[dict[str, str]] = []

    required = ["app.py", "requirements.txt", "README.md", ".streamlit/config.toml"]
    missing = [value for value in required if not (ROOT / value).is_file()]
    results.append(check("repository_layout", "PASS" if not missing else "FAIL", f"missing={missing}"))

    forbidden = [ROOT / ".env", ROOT / ".streamlit" / "secrets.toml"]
    present = [str(path.relative_to(ROOT)) for path in forbidden if path.exists()]
    results.append(check("secret_files", "PASS" if not present else "FAIL", f"present={present}"))

    leaked: list[str] = []
    patterns = [re.compile(r"sk-or-v1-[A-Za-z0-9_-]{16,}"), re.compile(r"postgres(?:ql)?://[^\s:@]+:[^\s@]+@")]
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts) or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(pattern.search(content) for pattern in patterns):
            leaked.append(str(path.relative_to(ROOT)))
    results.append(check("secret_patterns", "PASS" if not leaked else "FAIL", f"matches={leaked}"))

    manifest = pd.read_csv(ROOT / "data" / "test_manifest.csv").fillna("")
    _manifest, issues = validate_manifest(manifest, ROOT)
    results.append(check("dataset_integrity", "PASS" if not issues else "FAIL", f"issues={len(issues)}"))

    secret_status = "PASS" if cfg.openrouter_api_key else ("FAIL" if args.require_secrets else "BLOCKED")
    results.append(check("openrouter_secret", secret_status, "configured" if cfg.openrouter_api_key else "OPENROUTER_API_KEY missing"))
    persistent = cfg.database_url.startswith(("postgresql://", "postgres://"))
    db_status = "PASS" if persistent else ("FAIL" if args.require_persistent_database else "WARNING")
    results.append(check("database_persistence", db_status, "PostgreSQL" if persistent else "SQLite is non-durable on Community Cloud"))
    try:
        database_from_url(cfg.database_url, ROOT).initialize()
        results.append(check("database_connection", "PASS", "CONNECTED"))
    except Exception as exc:
        results.append(check("database_connection", "FAIL", type(exc).__name__))

    failed = [item for item in results if item["status"] == "FAIL"]
    print(json.dumps({"status": "FAIL" if failed else "PASS_WITH_BLOCKERS" if any(i["status"] == "BLOCKED" for i in results) else "PASS",
                      "checks": results}, indent=2))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
