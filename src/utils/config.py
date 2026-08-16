from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"
    database_url: str = "sqlite:///data/ktp_vision.db"
    timeout_seconds: float = 90.0
    max_retries: int = 2
    max_image_size_mb: int = 10
    max_image_pixels: int = 20_000_000
    app_env: str = "development"
    demo_mode: bool = True
    allow_sensitive_export: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip(),
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/ktp_vision.db").strip(),
            timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "90")),
            max_retries=max(0, int(os.getenv("OPENROUTER_MAX_RETRIES", "2"))),
            max_image_size_mb=max(1, int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))),
            max_image_pixels=max(1_000_000, int(os.getenv("MAX_IMAGE_PIXELS", "20000000"))),
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            demo_mode=os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"},
            allow_sensitive_export=os.getenv("ALLOW_SENSITIVE_EXPORT", "false").strip().lower() in {"1", "true", "yes", "on"},
        )

    def sqlite_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Implementasi lokal saat ini mendukung DATABASE_URL sqlite:/// saja.")
        path = Path(self.database_url[len(prefix):])
        return path if path.is_absolute() else PROJECT_ROOT / path
