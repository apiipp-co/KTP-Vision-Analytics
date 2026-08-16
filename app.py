import streamlit as st

from src.services.analytics import dashboard_metrics
from src.ui_common import configure_page, require_repository, settings, sidebar_notice


configure_page("KTP Vision Analytics")
sidebar_notice()
cfg = settings()
repo = require_repository(cfg.database_url)
documents = repo.history()
metrics = dashboard_metrics(documents)

st.title("KTP Vision Analytics")
st.subheader("AI-Powered Indonesian Identity Document Classification, OCR & Validation")
st.write("Upload gambar → klasifikasi AI → OCR AI Vision → JSON → normalisasi → business rules → database → analytics.")
st.info("Mulai dari halaman **Upload KTP** di navigasi. Aplikasi tidak menyimpan file gambar.")
if cfg.demo_mode:
    st.success("Demo mode aktif: PII display dimasking, raw export dimatikan, dan image persistence tidak digunakan.")

columns = st.columns(6)
labels = [
    ("Total Documents", metrics["total"]), ("KTP Detected", metrics["ktp"]),
    ("Non-KTP", metrics["non_ktp"]), ("Valid", metrics["valid"]),
    ("Invalid", metrics["invalid"]), ("Review", metrics["review"]),
]
for column, (label, value) in zip(columns, labels):
    column.metric(label, value)

st.markdown("### Cara kerja")
st.markdown("""
1. Model vision mengklasifikasikan dokumen tanpa mengekstrak PII lengkap.
2. Hanya hasil `KTP_INDONESIA` yang diteruskan ke request OCR terpisah.
3. Parser menolak JSON malformed; field tak terbaca tetap `null`.
4. Python menormalisasi dan memvalidasi struktur tanpa mengklaim verifikasi Dukcapil.
5. Metadata/hasil terstruktur tersimpan di database dan menggerakkan dashboard secara langsung.
""")

if not cfg.openrouter_api_key:
    st.warning("`OPENROUTER_API_KEY` belum tersedia. Dashboard tetap dapat dibuka, tetapi pemrosesan AI belum dapat dijalankan.")
