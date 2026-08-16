from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.quality import operational_quality
from src.services.dataset import manifest_summary, validate_manifest
from src.ui_common import page_header, require_repository, section_header, settings, sidebar_notice
from src.utils.config import PROJECT_ROOT


sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
page_header(
    "Data governance",
    "Quality starts before inference.",
    "Validasi dataset evaluasi dan kesehatan data operasional sebelum menginterpretasikan performa model.",
)

manifest = pd.read_csv(PROJECT_ROOT / "data" / "test_manifest.csv").fillna("")
_validated, dataset_issues = validate_manifest(manifest, PROJECT_ROOT)
dataset_summary = manifest_summary(manifest, dataset_issues)
section_header("Evaluation dataset", "Komposisi, provenance, consent, dan integritas fixture pengujian.", "Synthetic v2")
cols = st.columns(4)
cols[0].metric("Images", dataset_summary["total_images"])
cols[1].metric("Issues", dataset_summary["issue_count"])
cols[2].metric("KTP", dataset_summary["class_distribution"].get("KTP", 0))
cols[3].metric("Non-KTP", dataset_summary["class_distribution"].get("NON_KTP", 0))
if dataset_issues:
    st.error("Dataset validation FAIL")
else:
    st.success("Dataset validation PASS")
if dataset_issues:
    st.dataframe(pd.DataFrame(dataset_issues), hide_index=True, width="stretch")
st.dataframe(manifest[["image_id", "expected_class", "document_type", "source_type", "image_condition",
                       "consent_status", "dataset_version"]], hide_index=True, width="stretch")

section_header("Operational database", "Pemeriksaan kualitas data yang telah disimpan selama pemrosesan.", "Continuous checks")
quality, report = operational_quality(repo.history())
st.json(quality)
if report.empty:
    st.info("Tidak ada issue operasional yang terdeteksi; `NO_DATA` bukan bukti kualitas model.")
else:
    st.dataframe(report, hide_index=True, width="stretch")
