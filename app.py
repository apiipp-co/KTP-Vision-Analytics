from html import escape

import streamlit as st

from src.services.analytics import dashboard_metrics
from src.ui_common import configure_page, require_repository, section_header, settings, sidebar_notice


configure_page("KTP Vision Analytics")


def overview_page() -> None:
    sidebar_notice()
    cfg = settings()
    repo = require_repository(cfg.database_url)
    documents = repo.history()
    metrics = dashboard_metrics(documents)

    st.markdown(
        f"""
        <div class="hero-shell">
          <div class="hero-copy">
            <div class="hero-kicker">Document intelligence workspace</div>
            <h1>Identity data,<br><span class="highlight">made reliable.</span></h1>
            <p>Klasifikasi KTP, OCR terstruktur, validasi aturan, dan insight operasional dalam satu alur yang aman serta dapat diaudit.</p>
            <div class="hero-proof">
              <span class="proof-pill">In-memory processing</span>
              <span class="proof-pill">18 structured fields</span>
              <span class="proof-pill">Deterministic validation</span>
            </div>
          </div>
          <div class="hero-visual">
            <div class="visual-top">
              <span class="visual-label">Processing activity</span>
              <span class="visual-live">System ready</span>
            </div>
            <div class="visual-main">
              <div class="visual-value">{metrics['total']}<small> documents</small></div>
              <div class="signal-chart" aria-hidden="true">
                <i style="height:24%"></i><i style="height:42%"></i><i style="height:68%"></i><i style="height:38%"></i>
                <i style="height:56%"></i><i style="height:47%"></i><i style="height:86%"></i><i style="height:64%"></i>
              </div>
              <div class="visual-foot"><span>{metrics['ktp']} KTP detected</span><span>{metrics['valid']} valid results</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="hero-actions-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)

    cta, note = st.columns([1, 2.5], vertical_alignment="center")
    with cta:
        st.page_link("pages/1_Upload_KTP.py", label="Mulai pindai dokumen", icon=":material/document_scanner:", use_container_width=True)
    with note:
        st.caption("Gambar diproses hanya di memori dan tidak disimpan sebagai file oleh aplikasi.")

    st.markdown(
        f"""
        <div class="runtime-strip">
          <div class="runtime-item"><span>Active AI model</span><strong>{escape(cfg.openrouter_model)}</strong></div>
          <div class="runtime-item"><span>Vision provider</span><strong>OpenRouter</strong></div>
          <div class="runtime-item"><span>Application mode</span><strong>{'Demo / privacy-safe' if cfg.demo_mode else 'Operational'}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("Operational overview", "Ringkasan aktivitas yang berasal langsung dari database.", "Live data")
    labels = [
        ("Total Documents", metrics["total"]), ("KTP Detected", metrics["ktp"]),
        ("Non-KTP", metrics["non_ktp"]), ("Valid", metrics["valid"]),
        ("Invalid", metrics["invalid"]), ("Review", metrics["review"]),
    ]
    for start in range(0, len(labels), 3):
        columns = st.columns(3)
        for column, (label, value) in zip(columns, labels[start:start + 3]):
            column.metric(label, value)

    section_header("From image to insight", "Alur dua tahap mengurangi pemrosesan yang tidak perlu dan menjaga hasil tetap dapat ditelusuri.", "4 stages")
    st.markdown(
        """
        <div class="feature-grid">
          <div class="feature-card"><div class="feature-number">01</div><h3>Secure upload</h3><p>Validasi format, ukuran, pixel, orientasi, dan duplikasi dilakukan sebelum inferensi.</p></div>
          <div class="feature-card"><div class="feature-number">02</div><h3>AI classification</h3><p>Model memastikan dokumen adalah KTP Indonesia sebelum membaca data identitas.</p></div>
          <div class="feature-card"><div class="feature-number">03</div><h3>Structured OCR</h3><p>Delapan belas field diekstrak ke kontrak JSON tertutup; field tak terbaca tetap kosong.</p></div>
          <div class="feature-card"><div class="feature-number">04</div><h3>Deterministic rules</h3><p>NIK, tanggal, gender, kategori, dan konsistensi diperiksa oleh aturan Python transparan.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.2, 1])
    with left:
        with st.container(border=True):
            st.markdown("#### Built for accountable AI")
            st.write("Setiap hasil membawa versi prompt, model, durasi, usage, audit raw-vs-normalized, dan validation trace untuk review yang bertanggung jawab.")
    with right:
        with st.container(border=True):
            st.markdown("#### Privacy controls active")
            st.write("PII dimasking pada permukaan umum, ekspor sensitif dibatasi, dan byte gambar tidak pernah dipersistenkan.")

    if cfg.demo_mode:
        st.success("Demo mode aktif · PII dimasking · raw export dinonaktifkan · image persistence tidak digunakan")

    if not cfg.openrouter_api_key:
        st.warning("`OPENROUTER_API_KEY` belum tersedia. Dashboard tetap dapat dibuka, tetapi pemrosesan AI belum dapat dijalankan.")


navigation = st.navigation([
    st.Page(overview_page, title="Overview", icon=":material/dashboard:"),
    st.Page("pages/1_Upload_KTP.py", title="Upload KTP", icon=":material/document_scanner:"),
    st.Page("pages/2_Analytics.py", title="Analytics", icon=":material/monitoring:"),
    st.Page("pages/3_Database_History.py", title="Database History", icon=":material/history:"),
    st.Page("pages/5_Error_Analysis.py", title="Error Analysis", icon=":material/troubleshoot:"),
    st.Page("pages/6_Model_Evaluation.py", title="Model Evaluation", icon=":material/science:"),
    st.Page("pages/7_Data_Quality.py", title="Data Quality", icon=":material/fact_check:"),
    st.Page("pages/4_About.py", title="About", icon=":material/info:"),
])
navigation.run()
