from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.services.analytics import export_columns, masked_history
from src.utils.security import safe_csv_frame
from src.ui_common import page_header, require_repository, settings, sidebar_notice


sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
raw = repo.history()
data = masked_history(raw)

page_header(
    "Audit trail",
    "Every processed document, traceable.",
    "Telusuri riwayat pemrosesan, filter hasil, dan ekspor data yang sudah dimasking dengan aman.",
)
if data.empty:
    st.info("Belum ada dokumen tersimpan.")
    st.stop()

primary_filters = st.columns(3)
search = primary_filters[0].text_input("Search filename")
document_type = primary_filters[1].selectbox("Document type", ["ALL", *sorted(data["document_type"].dropna().unique())])
validation_status = primary_filters[2].selectbox("Validation", ["ALL", *sorted(data["validation_status"].dropna().unique())])
processed_dates = pd.to_datetime(data["processed_at"], errors="coerce", utc=True).dt.date
minimum_date = processed_dates.dropna().min()
maximum_date = processed_dates.dropna().max()
has_dates = pd.notna(minimum_date) and pd.notna(maximum_date)
secondary_filters = st.columns(3)
page_size = secondary_filters[0].selectbox("Rows per page", [10, 25, 50, 100], index=1)
date_from = secondary_filters[1].date_input("From", value=minimum_date, min_value=minimum_date, max_value=maximum_date) if has_dates else None
date_to = secondary_filters[2].date_input("To", value=maximum_date, min_value=minimum_date, max_value=maximum_date) if has_dates else None

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
pagination, pagination_note = st.columns([1, 3], vertical_alignment="bottom")
page = pagination.number_input("Page", min_value=1, max_value=total_pages, value=1)
pagination_note.caption(f"{len(filtered)} record(s) · halaman {page} dari {total_pages}")
start = (int(page) - 1) * page_size
visible_columns = ["id", "file_name", "document_type", "nik_masked", "nama", "tanggal_lahir", "jenis_kelamin", "validation_status", "processed_at"]
st.dataframe(filtered.iloc[start:start + page_size][visible_columns], hide_index=True, width="stretch")

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
