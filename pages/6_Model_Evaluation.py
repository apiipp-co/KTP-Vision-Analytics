from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.services.evaluation import compute_evaluation_metrics
from src.ui_common import configure_page, sidebar_notice
from src.utils.config import PROJECT_ROOT


configure_page("Model Evaluation")
sidebar_notice()
st.title("Model Evaluation")
st.caption("Semua angka pada halaman ini hanya berasal dari prediction artifact aktual. Confidence adalah self-reported model, bukan probabilitas terkalibrasi.")

results_path = PROJECT_ROOT / "outputs" / "evaluation_results.csv"
summary_path = PROJECT_ROOT / "outputs" / "evaluation_summary.json"
ocr_path = PROJECT_ROOT / "outputs" / "ocr_evaluation_results.csv"
if not results_path.exists() or not summary_path.exists():
    st.info("Evaluation data not available. Classification Accuracy, Precision, Recall, F1, OCR accuracy, CER, latency, dan cost = N/A.")
    st.code("python scripts/evaluate.py", language="bash")
    st.stop()

try:
    results = pd.read_csv(results_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
except (OSError, ValueError, json.JSONDecodeError):
    st.error("Evaluation artifact tidak valid; metrics tidak ditampilkan.")
    st.stop()

experiment = summary.get("experiment", {})
st.markdown("### Experiment metadata")
st.json({key: experiment.get(key) for key in ("experiment_id", "started_at", "completed_at", "model", "dataset_versions",
                                                "classification_prompt_version", "ocr_prompt_version", "data_context")})

filters = st.columns(3)
conditions = ["ALL", *sorted(results["image_condition"].dropna().astype(str).unique())]
sources = ["ALL", *sorted(results["source_type"].dropna().astype(str).unique())]
expected = ["ALL", "KTP", "NON_KTP"]
condition = filters[0].selectbox("Image condition", conditions)
source = filters[1].selectbox("Source type", sources)
expected_class = filters[2].selectbox("Expected class", expected)
filtered = results.copy()
if condition != "ALL": filtered = filtered[filtered["image_condition"] == condition]
if source != "ALL": filtered = filtered[filtered["source_type"] == source]
if expected_class != "ALL": filtered = filtered[filtered["expected_class"] == expected_class]
if filtered.empty:
    st.warning("Tidak ada row untuk filter ini.")
    st.stop()

metrics = compute_evaluation_metrics(filtered)
columns = st.columns(6)
for column, (label, key) in zip(columns, [("Images", "total"), ("Accuracy", "accuracy"), ("Precision KTP", "precision_ktp"),
                                                 ("Recall KTP", "recall_ktp"), ("F1 KTP", "f1_ktp"), ("Failed", "failed")]):
    value = metrics.get(key)
    column.metric(label, "N/A" if value is None else (f"{value:.2%}" if isinstance(value, float) else value))

matrix = metrics["confusion_matrix"]
matrix_frame = pd.DataFrame([[matrix["tp"], matrix["fn"]], [matrix["fp"], matrix["tn"]]],
                            index=["Actual KTP", "Actual Non-KTP"], columns=["Predicted KTP", "Predicted Non-KTP"])
left, right = st.columns(2)
left.dataframe(matrix_frame, width="stretch")
condition_frame = filtered.groupby("image_condition", dropna=False)["classification_correct"].agg(["count", "mean"]).reset_index()
right.plotly_chart(px.bar(condition_frame, x="image_condition", y="mean", hover_data=["count"], range_y=[0, 1],
                          title="Accuracy by image condition"), width="stretch")

st.markdown("### OCR quality")
if not ocr_path.exists():
    st.info("OCR evaluation artifact tidak tersedia.")
else:
    ocr = pd.read_csv(ocr_path)
    ocr = ocr[ocr["image_id"].isin(filtered["image_id"])]
    scored = ocr.dropna(subset=["exact_match"])
    if scored.empty:
        st.info("Tidak ada field ground truth yang dapat dinilai pada filter ini.")
    else:
        field = scored.groupby("field_name").agg(exact_match_accuracy=("exact_match", "mean"),
                                                  mean_cer=("character_error_rate", "mean"), samples=("exact_match", "size")).reset_index()
        st.dataframe(field.sort_values("exact_match_accuracy"), hide_index=True, width="stretch")
        st.plotly_chart(px.bar(field, x="field_name", y="exact_match_accuracy", hover_data=["mean_cer", "samples"],
                               range_y=[0, 1], title="Field-level exact match"), width="stretch")

st.markdown("### Hardest cases")
safe_columns = ["image_id", "expected_class", "predicted_class", "classification_correct", "image_condition",
                "classification_confidence", "total_duration_ms", "error_type", "error_message"]
st.dataframe(filtered.sort_values(["classification_correct", "classification_confidence"], ascending=[True, True])
             [[column for column in safe_columns if column in filtered]], hide_index=True, width="stretch")
