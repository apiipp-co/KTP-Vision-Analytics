import streamlit as st

from src.ui_common import configure_page, sidebar_notice


configure_page("About")
sidebar_notice()
st.title("About KTP Vision Analytics")
st.markdown("""
Project portfolio untuk klasifikasi dokumen, OCR multimodal, data quality, dan analytics KTP Indonesia.

**Batasan penting**

- Model vision dapat salah mengklasifikasi atau membaca teks.
- Confidence adalah nilai yang dilaporkan model dan bukan probabilitas terkalibrasi.
- Rule NIK hanya memeriksa format/konsistensi. Aplikasi tidak terhubung ke layanan verifikasi Dukcapil.
- Kualitas gambar, glare, crop, blur, dan resolusi memengaruhi hasil.
- Gunakan hanya gambar milik sendiri, berizin, dianonimkan, atau sintetis.

**Privacy**

Gambar tidak disimpan. NIK dimasking pada tampilan dan export default. Database lokal tetap mengandung hasil ekstraksi untuk validasi; lindungi file database dan batasi aksesnya.
""")
