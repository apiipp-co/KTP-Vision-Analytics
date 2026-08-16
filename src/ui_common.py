from __future__ import annotations

from dataclasses import replace
from html import escape
import sqlite3

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from src.database.connection import database_from_url
from src.database.repository import DocumentRepository
from src.utils.config import PROJECT_ROOT, Settings


def settings() -> Settings:
    base = Settings.from_env()
    try:
        secrets = st.secrets
        overrides = {}
        mapping = {
            "OPENROUTER_API_KEY": "openrouter_api_key",
            "OPENROUTER_MODEL": "openrouter_model",
            "DATABASE_URL": "database_url",
            "OPENROUTER_TIMEOUT_SECONDS": "timeout_seconds",
            "OPENROUTER_MAX_RETRIES": "max_retries",
            "MAX_IMAGE_SIZE_MB": "max_image_size_mb",
            "MAX_IMAGE_PIXELS": "max_image_pixels",
            "APP_ENV": "app_env",
            "DEMO_MODE": "demo_mode",
            "ALLOW_SENSITIVE_EXPORT": "allow_sensitive_export",
        }
        for secret_name, attribute in mapping.items():
            if secret_name in secrets and str(secrets[secret_name]).strip():
                value = secrets[secret_name]
                if attribute in {"timeout_seconds"}:
                    value = float(value)
                elif attribute in {"max_retries", "max_image_size_mb", "max_image_pixels"}:
                    value = int(value)
                elif attribute in {"demo_mode", "allow_sensitive_export"}:
                    value = str(value).strip().lower() in {"1", "true", "yes", "on"}
                overrides[attribute] = value
        return replace(base, **overrides)
    except (FileNotFoundError, KeyError):
        return base


@st.cache_resource
def repository(database_url: str) -> DocumentRepository:
    return DocumentRepository(database_from_url(database_url, PROJECT_ROOT))


def require_repository(database_url: str) -> DocumentRepository:
    try:
        return repository(database_url)
    except (ValueError, RuntimeError, sqlite3.Error, OSError):
        st.error("Database tidak tersedia atau konfigurasi DATABASE_URL tidak didukung. Periksa koneksi lalu muat ulang halaman.")
        st.stop()


def configure_page(title: str, icon: str = "🪪") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    pio.templates["ktp_editorial"] = go.layout.Template(
        layout=go.Layout(
            colorway=["#171918", "#dfff45", "#bfc9df", "#bdd8b9", "#a9aaa5", "#f1b6b9"],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, Arial, sans-serif", "color": "#242624", "size": 12},
            title={"font": {"size": 17, "color": "#171918"}, "x": 0.02},
            xaxis={"gridcolor": "#dedfd9", "zerolinecolor": "#dedfd9"},
            yaxis={"gridcolor": "#dedfd9", "zerolinecolor": "#dedfd9"},
            legend={"bgcolor": "rgba(0,0,0,0)"},
        )
    )
    pio.templates.default = "ktp_editorial"
    st.markdown("""
    <style>
      :root {
        --ink: #171918;
        --muted: #73756f;
        --canvas: #efefe9;
        --surface: #f8f8f4;
        --surface-strong: #ffffff;
        --line: #d9dad4;
        --lime: #dfff45;
        --lime-soft: #efffb0;
        --sage: #dcebd7;
        --periwinkle: #e0e4f0;
        --warm: #e7e4dd;
        --shadow: 0 18px 48px rgba(25, 27, 25, .07);
      }

      html {scroll-behavior: smooth;}
      html, body, [class*="css"] {font-family:"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}
      .stApp {
        background:var(--canvas);
        color: var(--ink);
      }
      [data-testid="stHeader"] {background:rgba(239,239,233,.82); backdrop-filter:blur(14px);}
      .block-container {padding:2.25rem 2rem 5rem; max-width:1280px;}
      [data-testid="stVerticalBlock"] {gap:1.15rem;}
      [data-testid="stHorizontalBlock"] {gap:1.1rem;}
      h1, h2, h3 {letter-spacing:-.045em; color:var(--ink); font-weight:520;}
      p {line-height:1.65;}

      [data-testid="stSidebar"] {
        background:#f7f7f3;
        border-right:1px solid var(--line);
      }
      [data-testid="stSidebar"] * {color:var(--ink);}
      [data-testid="stSidebarHeader"] {position:relative; min-height:88px; padding:.8rem 3.15rem .8rem .9rem; overflow:hidden; border-bottom:1px solid var(--line);}
      [data-testid="stSidebarHeader"]::before {content:none;}
      [data-testid="stSidebarHeader"]::after {content:"KTP Vision\A Document intelligence"; position:absolute; left:1rem; right:3.15rem; top:50%; transform:translateY(-50%); white-space:pre-line; overflow:hidden; color:var(--ink); font-size:.88rem; line-height:1.25; font-weight:680; letter-spacing:-.02em;}
      [data-testid="stSidebarHeader"] [data-testid="stLogoSpacer"] {display:none;}
      [data-testid="stSidebarCollapseButton"] {position:absolute; z-index:2; right:.65rem; top:50%; margin:0; transform:translateY(-50%);}
      [data-testid="stSidebarNav"] {padding-top:.55rem;}
      [data-testid="stSidebarNav"] a {
        min-height:2.7rem; border-radius:999px; margin:.18rem .7rem; padding-inline:.85rem;
        transition:background .18s ease, color .18s ease, transform .18s ease;
      }
      [data-testid="stSidebarNav"] a:hover {background:#e9e9e3; transform:translateX(2px);}
      [data-testid="stSidebarNav"] a[aria-current="page"] {
        background:var(--ink); box-shadow:none;
      }
      [data-testid="stSidebarNav"] a[aria-current="page"] * {color:#fff; font-weight:600;}
      [data-testid="stSidebarNavLink"] span[label="app"] {position:relative; display:inline-block; width:4.2rem; min-height:1.2rem; overflow:visible !important; color:transparent !important; text-indent:-9999px;}
      [data-testid="stSidebarNavLink"] span[label="app"]::after {content:"Overview"; position:absolute; inset:0 auto auto 0; display:block; color:#fff !important; font-size:.875rem; line-height:1.2rem; text-indent:0;}
      .sidebar-trust {
        margin:1rem .45rem 0; padding:1rem; border-radius:20px;
        background:var(--sage); border:1px solid rgba(23,25,24,.08);
      }
      .sidebar-trust-title {font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; color:#454a43 !important; font-weight:750;}
      .trust-row {display:flex; gap:.55rem; align-items:flex-start; margin-top:.68rem; font-size:.72rem; color:#595d57 !important; line-height:1.42;}
      .trust-dot {width:.38rem; height:.38rem; flex:0 0 auto; margin-top:.3rem; border-radius:50%; background:var(--ink);}

      .page-intro {margin:.25rem 0 2rem; animation:reveal .5s cubic-bezier(.2,.8,.2,1) both;}
      .eyebrow {display:inline-flex; align-items:center; gap:.5rem; padding:.42rem .7rem; margin-bottom:.85rem; border:1px solid var(--line); border-radius:999px; background:#f8f8f4; color:#555850; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; font-weight:700;}
      .eyebrow::before {content:""; width:.45rem; height:.45rem; border-radius:50%; background:var(--lime); border:1px solid rgba(23,25,24,.14);}
      .page-intro h1 {font-size:clamp(2.15rem,3.5vw,3.8rem); line-height:.98; margin:0; max-width:880px; font-weight:500;}
      .page-intro p {margin:.9rem 0 0; color:var(--muted); font-size:1rem; max-width:760px;}

      .hero-shell {
        display:grid; grid-template-columns:minmax(0,1.18fr) minmax(320px,.82fr); gap:1.15rem;
        overflow:hidden; min-height:440px; padding:1.1rem; border:1px solid #cfd0ca; border-radius:34px;
        background:#d9dad4; box-shadow:var(--shadow); animation:reveal .6s cubic-bezier(.2,.8,.2,1) both;
      }
      .hero-copy {display:flex; flex-direction:column; justify-content:center; padding:clamp(2rem,4vw,3.4rem); border-radius:25px; background:var(--surface);}
      .hero-kicker {display:inline-flex; align-items:center; align-self:flex-start; gap:.5rem; padding:.43rem .7rem; border:1px solid var(--line); border-radius:999px; color:#555850; background:#fff; font-size:.68rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;}
      .hero-kicker::before {content:""; width:.45rem; height:.45rem; border-radius:50%; background:var(--lime);}
      .hero-shell h1 {max-width:680px; margin:1.35rem 0 1.15rem; color:var(--ink); font-size:clamp(2.55rem,5vw,4.65rem); line-height:.96; letter-spacing:-.06em; font-weight:480;}
      .hero-shell h1 .highlight {position:relative; display:inline-block; z-index:0;}
      .hero-shell h1 .highlight::after {content:""; position:absolute; z-index:-1; left:-.04em; right:-.04em; bottom:.03em; height:.28em; border-radius:.04em; background:var(--lime); transform:scaleX(.12); transform-origin:left; animation:highlight-in .65s .4s ease forwards;}
      .hero-shell p {max-width:640px; margin:0; color:var(--muted); font-size:1.02rem;}
      .hero-proof {display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.65rem;}
      .proof-pill {padding:.5rem .72rem; border-radius:999px; color:#555750; background:#eeeeea; border:1px solid var(--line); font-size:.72rem;}
      .hero-visual {position:relative; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; padding:1.6rem; border-radius:25px; background:var(--sage); border:1px solid rgba(23,25,24,.07);}
      .hero-visual::before {content:""; position:absolute; width:210px; height:210px; right:-55px; top:-55px; border:1px solid rgba(23,25,24,.12); border-radius:50%; box-shadow:0 0 0 32px rgba(255,255,255,.16),0 0 0 64px rgba(255,255,255,.10);}
      .visual-top {position:relative; z-index:1; display:flex; align-items:center; justify-content:space-between; gap:1rem;}
      .visual-label {font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:#545951; font-weight:750;}
      .visual-live {display:flex; align-items:center; gap:.38rem; padding:.38rem .58rem; border-radius:999px; background:rgba(255,255,255,.55); font-size:.67rem;}
      .visual-live::before {content:""; width:.42rem; height:.42rem; border-radius:50%; background:var(--ink); animation:quiet-pulse 2.4s ease-in-out infinite;}
      .visual-main {position:relative; z-index:1; margin-top:2.5rem;}
      .visual-value {display:flex; align-items:flex-end; gap:.55rem; font-size:clamp(4.2rem,8vw,7rem); line-height:.82; letter-spacing:-.08em; font-weight:450;}
      .visual-value small {padding-bottom:.42rem; font-size:.82rem; line-height:1; letter-spacing:0; color:#5f645d;}
      .signal-chart {display:flex; align-items:end; gap:.36rem; height:92px; margin:1.7rem 0 .65rem; padding:0 .3rem; border-bottom:1px solid rgba(23,25,24,.2);}
      .signal-chart i {display:block; flex:1; min-width:8px; border-radius:999px 999px 2px 2px; background:rgba(23,25,24,.18); animation:bar-in .7s cubic-bezier(.2,.8,.2,1) both; transform-origin:bottom;}
      .signal-chart i:nth-child(3), .signal-chart i:nth-child(7) {background:var(--lime);}
      .visual-foot {display:flex; justify-content:space-between; gap:.75rem; color:#5a5f57; font-size:.7rem;}
      .hero-actions-spacer {height:.8rem;}
      .runtime-strip {display:grid; grid-template-columns:1.55fr .75fr .9fr; gap:.55rem; margin:.8rem 0 .25rem; padding:.5rem; border:1px solid var(--line); border-radius:24px; background:#e3e4de;}
      .runtime-item {min-width:0; padding:.85rem 1rem; border-radius:18px; background:var(--surface);}
      .runtime-item:nth-child(2) {background:var(--periwinkle);}
      .runtime-item:nth-child(3) {background:var(--sage);}
      .runtime-item span {display:block; margin-bottom:.28rem; color:var(--muted); font-size:.65rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase;}
      .runtime-item strong {display:block; overflow:hidden; color:var(--ink); font-size:.84rem; font-weight:620; text-overflow:ellipsis; white-space:nowrap;}

      [data-testid="stMetric"] {
        min-height:132px; padding:1.25rem 1.35rem; background:var(--surface); border:1px solid var(--line);
        border-radius:22px; box-shadow:none; transition:transform .2s ease, background .2s ease; animation:reveal .48s both;
      }
      [data-testid="stMetric"]:hover {transform:translateY(-3px); background:#fff;}
      [data-testid="stMetricLabel"] {color:var(--muted); font-weight:600;}
      [data-testid="stMetricValue"] {color:var(--ink); letter-spacing:-.055em; font-weight:480;}

      [data-testid="stFileUploaderDropzone"] {
        min-height:175px; padding:1.65rem; border:1px dashed #a9aaa4; border-radius:24px;
        background:var(--surface); transition:border-color .2s ease, background .2s ease, transform .2s ease;
      }
      [data-testid="stFileUploaderDropzone"]:hover {border-color:var(--ink); background:var(--lime-soft); transform:translateY(-2px);}
      [data-testid="stFileUploaderDropzone"] button {border-radius:999px; background:var(--ink); color:#fff; border:0;}
      [data-testid="stImage"] img {border-radius:22px; box-shadow:none;}
      [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line) !important; border-radius:24px !important; box-shadow:none; background:var(--surface);}

      .stButton > button, .stDownloadButton > button, [data-testid="stPageLink"] a {
        min-height:2.9rem; border-radius:999px; font-weight:650; transition:transform .18s ease, background .18s ease, box-shadow .18s ease;
      }
      .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], [data-testid="stPageLink"] a {
        border:1px solid rgba(23,25,24,.12); color:var(--ink); background:var(--lime); box-shadow:none;
      }
      .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPageLink"] a:hover {transform:translateY(-2px); box-shadow:0 8px 18px rgba(23,25,24,.10);}
      .stButton > button:active, .stDownloadButton > button:active {transform:translateY(0);}
      [data-baseweb="tab-list"] {gap:.35rem; padding:.32rem; border:1px solid var(--line); border-radius:999px; background:#e5e6e0;}
      [data-baseweb="tab"] {border-radius:999px; padding:.7rem 1rem; font-weight:600;}
      [data-baseweb="tab-highlight"] {background:var(--ink); border-radius:999px;}

      [data-testid="stAlert"] {margin:.25rem 0 .75rem; padding:.9rem 1rem; border-radius:18px; border-width:1px; box-shadow:none;}
      [data-testid="stCheckbox"] {padding:.35rem 0 .85rem;}
      [data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:20px; overflow:hidden; box-shadow:none;}
      [data-testid="stExpander"] {border:1px solid var(--line); border-radius:18px; overflow:hidden; background:var(--surface);}
      [data-baseweb="input"] > div, [data-baseweb="select"] > div {border-radius:999px; border-color:var(--line); background:var(--surface);}
      [data-testid="stPlotlyChart"] {padding:.6rem; border:1px solid var(--line); border-radius:24px; background:var(--surface); overflow:hidden;}

      .section-heading {display:flex; align-items:flex-end; justify-content:space-between; gap:1.25rem; margin:2.8rem 0 1.2rem;}
      .section-heading h2 {margin:0; font-size:1.55rem; font-weight:530;}
      .section-heading p {margin:.3rem 0 0; color:var(--muted); font-size:.9rem;}
      .section-tag {white-space:nowrap; padding:.4rem .65rem; border-radius:999px; color:var(--ink); background:var(--lime); border:1px solid rgba(23,25,24,.1); font-size:.67rem; font-weight:750; text-transform:uppercase; letter-spacing:.07em;}

      .feature-grid {display:grid; grid-template-columns:repeat(4,1fr); gap:.9rem; margin:1rem 0 1.8rem;}
      .feature-card {min-height:190px; position:relative; padding:1.25rem; border:1px solid var(--line); border-radius:24px; background:var(--surface); box-shadow:none; transition:transform .2s ease; animation:reveal .5s both;}
      .feature-card:nth-child(2) {background:var(--sage);}
      .feature-card:nth-child(3) {background:var(--periwinkle);}
      .feature-card:nth-child(4) {background:var(--warm);}
      .feature-card:hover {transform:translateY(-4px);}
      .feature-number {display:grid; place-items:center; width:2.1rem; height:2.1rem; border-radius:50%; color:var(--ink); background:var(--lime); font-weight:750; font-size:.7rem;}
      .feature-card h3 {margin:2.4rem 0 .38rem; font-size:1rem; letter-spacing:-.025em;}
      .feature-card p {margin:0; color:var(--muted); font-size:.84rem; line-height:1.55;}

      .status-card {padding:1.25rem 1.4rem; border:1px solid var(--line); border-radius:24px; background:var(--periwinkle); margin:.6rem 0; box-shadow:none;}
      .status-grid {display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem; margin-bottom:.65rem;}
      .status-item span {display:block; color:var(--muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.07em; font-weight:700;}
      .status-item strong {display:block; margin-top:.2rem; color:var(--ink);}
      .muted {color:var(--muted); font-size:.9rem;}
      .metadata-list {display:grid; gap:.15rem;}
      .metadata-row {display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.8rem 0; border-bottom:1px solid var(--line);}
      .metadata-row:last-child {border-bottom:0;}
      .metadata-row span {color:var(--muted); font-size:.82rem;}
      .metadata-row strong {max-width:68%; text-align:right; word-break:break-word; color:var(--ink); font-size:.88rem;}
      .security-banner {display:flex; gap:1rem; align-items:flex-start; padding:1.2rem 1.3rem; margin:.35rem 0 .65rem; border-radius:20px; background:var(--lime-soft); border:1px solid rgba(23,25,24,.1);}
      .security-icon {display:grid; place-items:center; flex:0 0 auto; width:2.25rem; height:2.25rem; border-radius:50%; color:#fff; background:var(--ink); font-weight:700;}
      .security-banner strong {display:block; color:var(--ink); font-size:.9rem;}
      .security-banner p {margin:.2rem 0 0; color:#5f625c; font-size:.8rem; line-height:1.5;}
      .workflow-rail {display:grid; grid-template-columns:repeat(3,1fr); gap:.5rem; padding:.42rem; margin:.15rem 0 1.35rem; border:1px solid var(--line); border-radius:999px; background:#e4e5df;}
      .workflow-step {display:flex; align-items:center; justify-content:center; gap:.5rem; min-height:2.55rem; padding:.4rem .7rem; border-radius:999px; color:#777973; font-size:.75rem; font-weight:600;}
      .workflow-step b {display:grid; place-items:center; width:1.35rem; height:1.35rem; border:1px solid #bfc0ba; border-radius:50%; font-size:.62rem; font-weight:700;}
      .workflow-step.active {color:var(--ink); background:var(--surface); box-shadow:0 3px 10px rgba(23,25,24,.06);}
      .workflow-step.active b {border-color:var(--ink); background:var(--lime);}

      @keyframes reveal {from {opacity:0; transform:translateY(10px)} to {opacity:1; transform:translateY(0)}}
      @keyframes highlight-in {to {transform:scaleX(1)}}
      @keyframes bar-in {from {transform:scaleY(0)} to {transform:scaleY(1)}}
      @keyframes quiet-pulse {0%,100% {opacity:.35} 50% {opacity:1}}
      @media (max-width: 900px) {
        .block-container {padding:1.5rem 1.2rem 4rem;}
        .hero-shell {grid-template-columns:1fr; min-height:auto; border-radius:26px;}
        .hero-copy,.hero-visual {border-radius:20px;}
        .hero-visual {min-height:330px;}
        .feature-grid {grid-template-columns:repeat(2,1fr);}
        .runtime-strip {grid-template-columns:1fr; border-radius:20px;}
        .status-grid {grid-template-columns:1fr;}
      }
      @media (max-width: 580px) {
        .block-container {padding-inline:.85rem;}
        .feature-grid {grid-template-columns:1fr;}
        .page-intro h1 {font-size:2rem;}
        .section-heading {align-items:flex-start; flex-direction:column;}
        .workflow-step span {display:none;}
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; transition-duration:.01ms !important;}
      }
    </style>
    """, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"<div class='page-intro'><div class='eyebrow'>{escape(eyebrow)}</div>"
        f"<h1>{escape(title)}</h1><p>{escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "", tag: str | None = None) -> None:
    tag_markup = f"<span class='section-tag'>{escape(tag)}</span>" if tag else ""
    st.markdown(
        f"<div class='section-heading'><div><h2>{escape(title)}</h2>"
        f"<p>{escape(description)}</p></div>{tag_markup}</div>",
        unsafe_allow_html=True,
    )


def sidebar_notice() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-trust">
              <div class="sidebar-trust-title">Privacy by design</div>
              <div class="trust-row"><i class="trust-dot"></i><span>Gambar diproses di memori dan tidak disimpan.</span></div>
              <div class="trust-row"><i class="trust-dot"></i><span>PII dimasking pada layar dan ekspor default.</span></div>
              <div class="trust-row"><i class="trust-dot"></i><span>Validasi format, bukan verifikasi Dukcapil.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
