from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.insights import generate_insights
from src.services.evaluation import load_evaluation_artifacts
from src.services.analytics import completeness, dashboard_metrics, failure_analysis
from src.ui_common import page_header, require_repository, section_header, settings, sidebar_notice


sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
documents = repo.history()
validations = repo.validations()
if not documents.empty:
    st.sidebar.markdown("### Dashboard filters")
    model_options = ["ALL", *sorted(documents["classification_model"].dropna().astype(str).unique())]
    status_options = ["ALL", *sorted(documents["validation_status"].dropna().astype(str).unique())]
    type_options = ["ALL", *sorted(documents["document_type"].dropna().astype(str).unique())]
    selected_model = st.sidebar.selectbox("Model", model_options)
    selected_status = st.sidebar.selectbox("Validation", status_options)
    selected_type = st.sidebar.selectbox("Document type", type_options)
    if selected_model != "ALL": documents = documents[documents["classification_model"] == selected_model]
    if selected_status != "ALL": documents = documents[documents["validation_status"] == selected_status]
    if selected_type != "ALL": documents = documents[documents["document_type"] == selected_type]
    validations = validations[validations["document_id"].isin(documents["id"])]
metrics = dashboard_metrics(documents)

page_header(
    "Operations intelligence",
    "Analytics that explain the workflow.",
    "Pantau volume, hasil klasifikasi, kualitas field, durasi pemrosesan, dan usage model dari data aktual.",
)
section_header("Performance snapshot", "KPI mengikuti filter aktif dan dihitung langsung dari database.", "Live metrics")
snapshot_items = [
    ("Total", "total"), ("KTP", "ktp"), ("Non-KTP", "non_ktp"),
    ("Valid", "valid"), ("Invalid", "invalid"), ("Review", "review"),
]
for start in range(0, len(snapshot_items), 3):
    columns = st.columns(3)
    for column, (label, key) in zip(columns, snapshot_items[start:start + 3]):
        column.metric(label, metrics[key])

if documents.empty:
    st.info("Belum ada data pemrosesan. Semua KPI berasal dari database dan tetap 0 sampai dokumen diproses.")
    st.stop()

left, right = st.columns(2)
classification_counts = documents["document_type"].value_counts().rename_axis("document_type").reset_index(name="count")
left.plotly_chart(px.pie(classification_counts, names="document_type", values="count", title="Classification Distribution", hole=.45), width="stretch")
validation_counts = documents["validation_status"].value_counts().rename_axis("status").reset_index(name="count")
right.plotly_chart(px.bar(validation_counts, x="status", y="count", title="Validation Distribution", color="status"), width="stretch")

trend = documents.copy()
timestamps = pd.to_datetime(trend["processed_at"], errors="coerce", utc=True)
span_days = max(0, (timestamps.max() - timestamps.min()).days) if timestamps.notna().any() else 0
frequency, label = ("D", "day") if span_days <= 45 else (("W", "week") if span_days <= 240 else ("MS", "month"))
trend["period"] = timestamps.dt.tz_convert(None).dt.to_period(frequency).dt.start_time
trend = trend.dropna(subset=["period"]).groupby("period").size().reset_index(name="uploads")
st.plotly_chart(px.line(trend, x="period", y="uploads", markers=True, title=f"Processing Trend by {label}"), width="stretch")

left, right = st.columns(2)
failures = failure_analysis(validations)
if failures.empty:
    left.info("Belum ada validation failure untuk dianalisis.")
else:
    left.plotly_chart(px.bar(failures, x="failure_count", y="rule_name", orientation="h", title="Validation Failure Analysis"), width="stretch")
quality = completeness(documents)
if quality.empty:
    right.info("Belum ada KTP untuk menghitung data completeness.")
else:
    right.plotly_chart(px.bar(quality, x="completeness_pct", y="field", orientation="h", range_x=[0, 100], title="OCR Data Completeness (%)"), width="stretch")

section_header("Automated insights", "Sinyal ringkas yang dihasilkan dari pola operasional saat ini.", "Insights")
for insight in generate_insights(documents, quality):
    st.info(insight)

section_header("Actual performance", "Latency aktual dari proses yang telah selesai.", "Observed")
duration_columns = st.columns(4)
for column, (label, key) in zip(duration_columns, [
    ("Average", "avg_ms"), ("Median", "median_ms"), ("Minimum", "min_ms"), ("Maximum", "max_ms"),
]):
    value = metrics[key]
    column.metric(f"{label} Processing", "N/A" if value is None else f"{value / 1000:.2f}s")

durations = pd.to_numeric(documents["total_duration_ms"], errors="coerce").dropna() / 1000
if not durations.empty:
    st.plotly_chart(px.histogram(x=durations, nbins=min(30, max(5, len(durations))),
                                labels={"x": "Duration (seconds)"}, title="Processing Duration Distribution"),
                    width="stretch")

usage = documents[["input_tokens", "output_tokens", "total_tokens", "api_cost"]].apply(pd.to_numeric, errors="coerce")
if usage.notna().any().any():
    section_header("API usage", "Token dan biaya hanya ditampilkan bila dilaporkan oleh provider.", "Provider-reported")
    usage_cols = st.columns(4)
    usage_cols[0].metric("Input tokens", int(usage["input_tokens"].sum()))
    usage_cols[1].metric("Output tokens", int(usage["output_tokens"].sum()))
    usage_cols[2].metric("Total tokens", int(usage["total_tokens"].sum()))
    usage_cols[3].metric("Reported cost", f"${usage['api_cost'].sum():.6f}" if usage["api_cost"].notna().any() else "N/A")
else:
    st.caption("Token/cost analysis: N/A — provider belum mengembalikan usage yang dapat disimpan.")

_evaluation, evaluation_metrics = load_evaluation_artifacts()
section_header("Model evaluation", "Metrik eksperimen hanya ditampilkan ketika artifact inference tersedia.", "Evidence-based")
if evaluation_metrics is None:
    st.info("Classification Accuracy, Precision, Recall, F1, dan Confusion Matrix: N/A — actual inference belum tersedia.")
else:
    metric_columns = st.columns(4)
    for column, (label, key) in zip(metric_columns, [
        ("Accuracy", "accuracy"), ("Precision KTP", "precision_ktp"),
        ("Recall KTP", "recall_ktp"), ("F1 KTP", "f1_ktp"),
    ]):
        value = evaluation_metrics.get(key)
        column.metric(label, "N/A" if value is None else f"{value:.2%}")
    matrix = evaluation_metrics.get("confusion_matrix", {})
    matrix_frame = pd.DataFrame(
        [[matrix.get("tp", 0), matrix.get("fn", 0)], [matrix.get("fp", 0), matrix.get("tn", 0)]],
        index=["Actual KTP", "Actual Non-KTP"], columns=["Predicted KTP", "Predicted Non-KTP"],
    )
    st.dataframe(matrix_frame, width="stretch")
    ocr_columns = st.columns(2)
    completeness_value = evaluation_metrics.get("ocr_data_completeness")
    missing_value = evaluation_metrics.get("missing_field_rate")
    ocr_columns[0].metric("OCR Data Completeness", "N/A" if completeness_value is None else f"{completeness_value:.2%}")
    ocr_columns[1].metric("Missing Field Rate", "N/A" if missing_value is None else f"{missing_value:.2%}")
    exact = evaluation_metrics.get("field_exact_match") or {}
    required_fields = ["nik", "nama", "tanggal_lahir", "jenis_kelamin", "alamat"]
    exact_rows = [{"field": field, "exact_match_accuracy": exact.get(field)} for field in required_fields]
    exact_frame = pd.DataFrame(exact_rows)
    exact_frame["exact_match_accuracy"] = exact_frame["exact_match_accuracy"].map(
        lambda value: "N/A" if value is None else f"{value:.2%}"
    )
    st.dataframe(exact_frame, hide_index=True, width="stretch")
