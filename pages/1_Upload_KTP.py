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
from src.ui_common import page_header, require_repository, section_header, settings, sidebar_notice
from src.utils.constants import IDENTITY_FIELDS
from src.utils.security import mask_identity_field, safe_filename, sha256_bytes


sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)

page_header(
    "Document workspace",
    "Scan smarter. Validate with confidence.",
    "Unggah dokumen, jalankan klasifikasi dan OCR terstruktur, lalu tinjau setiap aturan validasi dalam satu workspace.",
)
workflow_placeholder = st.empty()


def render_workflow(active_step: int) -> None:
    labels = ("Upload document", "AI processing", "Review result")
    steps = "".join(
        f'<div class="workflow-step{" active" if number == active_step else ""}"><b>{number}</b><span>{label}</span></div>'
        for number, label in enumerate(labels, start=1)
    )
    workflow_placeholder.markdown(
        f'<div class="workflow-rail" aria-label="Processing steps">{steps}</div>',
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="security-banner">
      <div class="security-icon">✓</div>
      <div><strong>Secure processing notice</strong><p>Gunakan hanya dokumen milik sendiri atau yang Anda berhak proses. Gambar dikirim ke provider AI melalui OpenRouter, diproses di memori, dan tidak disimpan sebagai file.</p></div>
    </div>
    """,
    unsafe_allow_html=True,
)
consent = st.checkbox("Saya memiliki hak/izin untuk memproses dokumen ini dan memahami penggunaan layanan AI eksternal.")
section_header("Upload document", "JPG, JPEG, atau PNG hingga 10 MB. Gunakan gambar tajam, tidak terpotong, dan minim pantulan.", "Step 1")
uploaded = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
render_workflow(3 if st.session_state.get("last_result") else (2 if uploaded else 1))

if uploaded:
    content = uploaded.getvalue()
    upload_token = sha256_bytes(content)
    if st.session_state.get("upload_token") != upload_token:
        st.session_state["upload_token"] = upload_token
        st.session_state.pop("last_result", None)
    left, right = st.columns([1.75, 1], gap="large")
    with left:
        with st.container(border=True):
            st.image(content, caption="Preview aman · hanya ditampilkan pada sesi ini", width="stretch")
    with right:
        with st.container(border=True):
            st.markdown("#### File details")
            st.markdown(
                f"""
                <div class="metadata-list">
                  <div class="metadata-row"><span>File name</span><strong>{escape(safe_filename(uploaded.name))}</strong></div>
                  <div class="metadata-row"><span>Format</span><strong>{escape(uploaded.type or 'Unknown')}</strong></div>
                  <div class="metadata-row"><span>File size</span><strong>{len(content) / 1024:.2f} KB</strong></div>
                  <div class="metadata-row"><span>Storage</span><strong>In-memory only</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("File siap diproses" if consent else "Centang persetujuan untuk melanjutkan")

    section_header("Run intelligence pipeline", "Klasifikasi berjalan lebih dahulu; OCR hanya dipanggil untuk KTP Indonesia.", "Step 2")
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
    render_workflow(3)
    section_header("Processing result", "Tinjau prediksi, hasil ekstraksi, dan alasan validasi secara terpisah.", "Completed")
    st.caption(f"Request ID · `{result.request_id}`")
    if result.duplicate:
        st.warning(f"Dokumen dengan hash sama pernah diproses (ID {result.duplicate['id']}, {result.duplicate['processed_at']}).")
    classification = result.classification
    confidence = "N/A" if classification.confidence is None else f"{classification.confidence:.1%} (self-reported model)"
    st.markdown(
        f"<div class='status-card'><div class='status-grid'>"
        f"<div class='status-item'><span>Prediction</span><strong>{escape(classification.document_type)}</strong></div>"
        f"<div class='status-item'><span>Detection</span><strong>{'KTP detected' if classification.is_ktp else 'Not a KTP'}</strong></div>"
        f"<div class='status-item'><span>Model confidence</span><strong>{escape(confidence)}</strong></div>"
        f"<div class='status-item'><span>AI model</span><strong>{escape(classification.model or cfg.openrouter_model)}</strong></div>"
        f"</div><span class='muted'>{escape(classification.reason)}</span></div>",
        unsafe_allow_html=True,
    )
    if result.stopped_after_classification:
        st.info("OCR dihentikan karena gambar tidak diklasifikasikan sebagai KTP Indonesia.")
    else:
        rows = []
        for name in IDENTITY_FIELDS:
            value = result.fields.get(name)
            rows.append({"Field": name.replace("_", " ").title(), "Value": value or "—"})

        ocr_tab, audit_tab, validation_tab = st.tabs(["Extracted fields", "Normalization audit", "Validation rules"])
        with ocr_tab:
            st.caption("Nilai sensitif dimasking pada tampilan ini.")
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        with audit_tab:
            st.caption("Perbandingan nilai mentah dan hasil normalisasi. Seluruh PII tetap dimasking.")
            safe_audit = json.loads(json.dumps(result.audit))
            st.json(safe_audit)
        with validation_tab:
            status = result.validation.status.replace("_", " ")
            if result.validation.status == "VALID":
                st.success(f"Validation status · {status}")
            elif result.validation.status == "INVALID":
                st.error(f"Validation status · {status}")
            else:
                st.warning(f"Validation status · {status}")
            st.dataframe(pd.DataFrame([rule.as_dict() for rule in result.validation.rules]), hide_index=True, width="stretch")
            st.caption("Rule-based format validation · bukan konfirmasi identitas ke Dukcapil.")

    if st.button("Reset workspace", icon=":material/restart_alt:"):
        st.session_state.pop("last_result", None)
        st.session_state.pop("upload_token", None)
        st.rerun()
