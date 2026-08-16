from __future__ import annotations

from dataclasses import replace
import sqlite3

import streamlit as st

from src.database.connection import database_from_url
from src.database.repository import DocumentRepository
from src.utils.config import PROJECT_ROOT, Settings


def settings() -> Settings:
    base = Settings.from_env()
    try:
        secrets = st.secrets
        overrides = {}
        mapping = {
            "OPENROUTER_API_KEY": "openrouter_api_key",
            "OPENROUTER_MODEL": "openrouter_model",
            "DATABASE_URL": "database_url",
            "OPENROUTER_TIMEOUT_SECONDS": "timeout_seconds",
            "OPENROUTER_MAX_RETRIES": "max_retries",
            "MAX_IMAGE_SIZE_MB": "max_image_size_mb",
            "MAX_IMAGE_PIXELS": "max_image_pixels",
            "APP_ENV": "app_env",
            "DEMO_MODE": "demo_mode",
            "ALLOW_SENSITIVE_EXPORT": "allow_sensitive_export",
        }
        for secret_name, attribute in mapping.items():
            if secret_name in secrets and str(secrets[secret_name]).strip():
                value = secrets[secret_name]
                if attribute in {"timeout_seconds"}:
                    value = float(value)
                elif attribute in {"max_retries", "max_image_size_mb", "max_image_pixels"}:
                    value = int(value)
                elif attribute in {"demo_mode", "allow_sensitive_export"}:
                    value = str(value).strip().lower() in {"1", "true", "yes", "on"}
                overrides[attribute] = value
        return replace(base, **overrides)
    except (FileNotFoundError, KeyError):
        return base


@st.cache_resource
def repository(database_url: str) -> DocumentRepository:
    return DocumentRepository(database_from_url(database_url, PROJECT_ROOT))


def require_repository(database_url: str) -> DocumentRepository:
    try:
        return repository(database_url)
    except (ValueError, RuntimeError, sqlite3.Error, OSError):
        st.error("Database tidak tersedia atau konfigurasi DATABASE_URL tidak didukung. Periksa koneksi lalu muat ulang halaman.")
        st.stop()


def configure_page(title: str, icon: str = "🪪") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.markdown("""
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px;}
      [data-testid="stMetric"] {background:#f8fafc; border:1px solid #e2e8f0; padding:1rem; border-radius:12px;}
      .status-card {padding:1rem 1.2rem; border:1px solid #dbe3ed; border-radius:12px; background:#f8fafc; margin:.6rem 0;}
      .muted {color:#64748b; font-size:.9rem;}
    </style>
    """, unsafe_allow_html=True)


def sidebar_notice() -> None:
    with st.sidebar:
        st.markdown("### Privacy by design")
        st.caption("Gambar diproses di memori dan tidak disimpan. PII dimasking pada tampilan umum dan export default.")
        st.caption("Pemrosesan AI mengirim gambar ke OpenRouter dan provider model yang dipilih.")
        st.caption("Validasi adalah pemeriksaan format/rule, bukan verifikasi resmi Dukcapil.")
