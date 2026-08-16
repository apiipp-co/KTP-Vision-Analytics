from __future__ import annotations

import copy
import json
from html import escape

import pandas as pd
import streamlit as st

from src.ai.openrouter_client import OpenRouterClient, OpenRouterError
from src.processing.image_processor import ImageValidationError
from src.processing.json_parser import JSONParseError
from src.services.pipeline import DocumentPipeline, DuplicateDocumentError
from src.ui_common import configure_page, require_repository, settings, sidebar_notice
from src.utils.constants import IDENTITY_FIELDS
from src.utils.security import mask_identity_field, safe_filename, sha256_bytes


configure_page("Upload KTP")
sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)

st.title("Upload & Process Document")
st.warning("Dokumen identitas memuat data pribadi. Gunakan hanya dokumen milik sendiri/yang Anda berhak proses. Untuk demo publik, gunakan data sintetis atau anonim.")
st.caption("Gambar dikirim melalui OpenRouter ke provider AI eksternal untuk klasifikasi/OCR, diproses di memori, dan tidak disimpan sebagai file oleh aplikasi ini.")
consent = st.checkbox("Saya menyatakan memiliki hak/izin untuk memproses dokumen ini dan memahami penggunaan layanan AI eksternal.")
uploaded = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded:
    content = uploaded.getvalue()
    upload_token = sha256_bytes(content)
    if st.session_state.get("upload_token") != upload_token:
        st.session_state["upload_token"] = upload_token
        st.session_state.pop("last_result", None)
    left, right = st.columns([2, 1])
    left.image(content, caption="Preview (ditampilkan hanya pada sesi ini)", width="stretch")
    right.markdown("#### File metadata")
    right.write({"name": safe_filename(uploaded.name), "type": uploaded.type, "size_kb": round(len(content) / 1024, 2)})
    if st.button("Process Document", type="primary", width="stretch", disabled=not consent):
        st.session_state.pop("last_result", None)
        if not cfg.openrouter_api_key:
            st.error("OPENROUTER_API_KEY belum dikonfigurasi. Isi `.env` atau Streamlit Secrets.")
            st.stop()
        progress = st.progress(0, text="Menyiapkan pipeline")

        def report(message: str, value: float) -> None:
            progress.progress(value, text=message)

        try:
            client = OpenRouterClient(cfg.openrouter_api_key, cfg.openrouter_model, cfg.timeout_seconds, cfg.max_retries)
            result = DocumentPipeline(client, repo, cfg.max_image_size_mb, cfg.max_image_pixels).process(uploaded.name, content, report)
            safe_result = copy.deepcopy(result)
            safe_result.image.content = b""
            safe_result.fields = {name: mask_identity_field(name, value) for name, value in result.fields.items()}
            safe_result.audit = {
                name: {key: mask_identity_field(name, value) for key, value in values.items()}
                for name, values in result.audit.items()
            }
            for rule in safe_result.validation.rules:
                if rule.actual_value:
                    rule.actual_value = "[masked]"
                if rule.expected_value:
                    rule.expected_value = "[masked]"
            st.session_state["last_result"] = safe_result
        except DuplicateDocumentError as exc:
            progress.empty()
            st.warning(str(exc))
        except OpenRouterError as exc:
            repo.log_event("openrouter", "ERROR", str(exc))
            progress.empty()
            st.error(str(exc))
        except (ImageValidationError, JSONParseError) as exc:
            progress.empty()
            st.error(str(exc))
        except Exception:
            repo.log_event("application", "ERROR", "Internal processing error without PII details.")
            progress.empty()
            st.error("Pemrosesan gagal karena kesalahan internal yang aman. Detail PII tidak dicetak ke layar/log.")

result = st.session_state.get("last_result")
if result:
    st.caption(f"Request ID: `{result.request_id}`")
    if result.duplicate:
        st.warning(f"Dokumen dengan hash sama pernah diproses (ID {result.duplicate['id']}, {result.duplicate['processed_at']}).")
    classification = result.classification
    confidence = "N/A" if classification.confidence is None else f"{classification.confidence:.1%} (self-reported model)"
    st.markdown("### Document Classification")
    st.markdown(
        f"<div class='status-card'><b>Prediction:</b> {escape(classification.document_type)}<br>"
        f"<b>Status:</b> {'Detected' if classification.is_ktp else 'BUKAN_KTP'}<br>"
        f"<b>Confidence:</b> {escape(confidence)}<br><span class='muted'>{escape(classification.reason)}</span></div>",
        unsafe_allow_html=True,
    )
    if result.stopped_after_classification:
        st.info("OCR dihentikan karena gambar tidak diklasifikasikan sebagai KTP Indonesia.")
    else:
        st.markdown("### OCR Result")
        rows = []
        for name in IDENTITY_FIELDS:
            value = result.fields.get(name)
            rows.append({"Field": name.replace("_", " ").title(), "Value": value or "—"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        with st.expander("Show Raw vs Normalized OCR (PII masked)"):
            safe_audit = json.loads(json.dumps(result.audit))
            st.json(safe_audit)
        st.markdown("### Validation Result")
        status = result.validation.status.replace("_", " ")
        if result.validation.status == "VALID":
            st.success(status)
        elif result.validation.status == "INVALID":
            st.error(status)
        else:
            st.warning(status)
        st.dataframe(pd.DataFrame([rule.as_dict() for rule in result.validation.rules]), hide_index=True, width="stretch")
        st.caption("Scope: rule-based format validation; bukan konfirmasi identitas ke Dukcapil.")

if st.button("Reset session result"):
    st.session_state.pop("last_result", None)
    st.session_state.pop("upload_token", None)
    st.rerun()
