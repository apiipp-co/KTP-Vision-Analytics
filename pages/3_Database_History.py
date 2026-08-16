from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.services.analytics import export_columns, masked_history
from src.utils.security import safe_csv_frame
from src.ui_common import configure_page, require_repository, settings, sidebar_notice


configure_page("Database History")
sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
raw = repo.history()
data = masked_history(raw)

st.title("Database History")
if data.empty:
    st.info("Belum ada dokumen tersimpan.")
    st.stop()

filters = st.columns(6)
search = filters[0].text_input("Search filename")
document_type = filters[1].selectbox("Document type", ["ALL", *sorted(data["document_type"].dropna().unique())])
validation_status = filters[2].selectbox("Validation", ["ALL", *sorted(data["validation_status"].dropna().unique())])
page_size = filters[3].selectbox("Rows/page", [10, 25, 50, 100], index=1)
processed_dates = pd.to_datetime(data["processed_at"], errors="coerce", utc=True).dt.date
minimum_date = processed_dates.dropna().min()
maximum_date = processed_dates.dropna().max()
has_dates = pd.notna(minimum_date) and pd.notna(maximum_date)
date_from = filters[4].date_input("From", value=minimum_date, min_value=minimum_date, max_value=maximum_date) if has_dates else None
date_to = filters[5].date_input("To", value=maximum_date, min_value=minimum_date, max_value=maximum_date) if has_dates else None

filtered = data.copy()
if search:
    needle = search.lower()
    mask = filtered["file_name"].fillna("").str.lower().str.contains(needle, regex=False)
    filtered = filtered[mask]
if document_type != "ALL":
    filtered = filtered[filtered["document_type"] == document_type]
if validation_status != "ALL":
    filtered = filtered[filtered["validation_status"] == validation_status]
if date_from and date_to:
    filtered_dates = pd.to_datetime(filtered["processed_at"], errors="coerce", utc=True).dt.date
    filtered = filtered[(filtered_dates >= date_from) & (filtered_dates <= date_to)]

total_pages = max(1, math.ceil(len(filtered) / page_size))
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
start = (int(page) - 1) * page_size
visible_columns = ["id", "file_name", "document_type", "nik_masked", "nama", "tanggal_lahir", "jenis_kelamin", "validation_status", "processed_at"]
st.dataframe(filtered.iloc[start:start + page_size][visible_columns], hide_index=True, width="stretch")
st.caption(f"{len(filtered)} record(s) · page {page}/{total_pages}")

masked_csv = export_columns(raw[raw["id"].isin(filtered["id"])]).to_csv(index=False).encode("utf-8-sig")
st.download_button("Download CSV — Masked Data", masked_csv, "ktp_history_masked.csv", "text/csv", type="primary")

if cfg.demo_mode or not cfg.allow_sensitive_export:
    st.info("Raw/full identity export dinonaktifkan oleh konfigurasi privacy (`DEMO_MODE`/`ALLOW_SENSITIVE_EXPORT`).")
else:
    with st.expander("Raw/full identity export (sensitive)"):
        st.warning("File ini memuat PII lengkap. Gunakan hanya dengan dasar pemrosesan, akses, dan media penyimpanan yang sah.")
        confirmed = st.checkbox("Saya memahami risiko ekspor PII penuh")
        if confirmed:
            full = safe_csv_frame(raw[raw["id"].isin(filtered["id"])])
            st.download_button("Download Sensitive CSV", full.to_csv(index=False).encode("utf-8-sig"), "ktp_history_sensitive.csv", "text/csv")
