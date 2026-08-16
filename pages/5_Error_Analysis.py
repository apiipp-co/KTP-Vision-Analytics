from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.services.evaluation import load_evaluation_artifacts, operational_error_analysis
from src.ui_common import configure_page, require_repository, settings, sidebar_notice


configure_page("Error Analysis")
sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
documents = repo.history()
validations = repo.validations()
fields = repo.fields()
logs = repo.logs()
evaluation, _metrics = load_evaluation_artifacts()
analysis = operational_error_analysis(documents, validations, fields, logs, evaluation)

st.title("Error Analysis")
st.caption("Count dan percentage dihitung dari database/evaluation artifact aktual. Scope dan denominator ditampilkan agar persentase tidak menyesatkan.")

if analysis.empty:
    st.info("Belum ada data operasional atau hasil inference aktual untuk dianalisis.")
else:
    display = analysis.copy()
    display["percentage"] = display["percentage"].map(lambda value: "N/A" if value is None else f"{value:.2f}%")
    st.dataframe(display, hide_index=True, width="stretch")
    chart_data = analysis.dropna(subset=["percentage"])
    if not chart_data.empty:
        st.plotly_chart(px.bar(chart_data, x="count", y="category", color="scope", orientation="h",
                               title="Error Frequency"), width="stretch")

if evaluation is None:
    st.warning("False Positive, False Negative, OCR Error, dan API Error: N/A — evaluation inference belum dijalankan.")
else:
    with st.expander("Actual evaluation rows"):
        safe_columns = [column for column in evaluation.columns if not column.startswith("ocr_")]
        st.dataframe(evaluation[safe_columns], hide_index=True, width="stretch")
