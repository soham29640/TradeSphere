import os
import sys

import torch
import pandas as pd
import streamlit as st
import torchvision.transforms as transforms
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.pattern.model import ChartPatternCNN

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL_PATH  = "models/pattern/chart_pattern_model.pth"
NUM_CLASSES = 20
THRESHOLD   = 0.5
TOP_K       = 3

CLASS_NAMES = [
    "Ascending-Triangle", "Channel-down", "Channel-up", "Cup-and-handle",
    "Descending-Triangle", "Double-Bottom", "Double-Top", "Falling-Wedge",
    "Head-Shoulders", "Inverse-Head-Shoulders", "Resistance-Emerging",
    "Resistance-breakout", "Rising-Wedge", "Rounding-Bottom", "Rounding-Top",
    "Support-breakout", "Triangle", "Triple-Bottom", "Triple-Top", "Rectangle",
]

INFER_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pattern Detector · Trade Sphere",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700;900&display=swap');

:root {
    --green:  #00ffaa;
    --blue:   #00c2ff;
    --red:    #ff4d6d;
    --gold:   #ffc145;
    --bg:     #050709;
    --bg2:    #090d12;
    --bg3:    #0e1520;
    --border: rgba(255,255,255,0.06);
    --text:   #cdd5e0;
    --muted:  #3d4d60;
}
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'Outfit', sans-serif; color: var(--text);
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 70% 40% at 90% 0%, rgba(255,77,109,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 10% 80%, rgba(255,193,69,0.03) 0%, transparent 60%),
        var(--bg) !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'Outfit', sans-serif !important; color: var(--text) !important; }
[data-testid="stMainBlockContainer"] { padding: 0 48px 48px !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,77,109,0.03) !important;
    border: 1px dashed rgba(255,77,109,0.25) !important;
    border-radius: 0 !important;
}
[data-testid="stFileUploader"] label { display: none !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-family: 'DM Mono', monospace !important; font-size: 11px !important;
    letter-spacing: 0.1em !important; color: var(--muted) !important; text-transform: uppercase !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: rgba(255,77,109,0.1) !important;
    border: 1px solid rgba(255,77,109,0.3) !important;
    color: var(--red) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important; letter-spacing: 0.1em !important;
    border-radius: 2px !important;
}

/* Page header */
.page-header { padding: 40px 0 36px; border-bottom: 1px solid var(--border); margin-bottom: 40px; }
.breadcrumb {
    font-family: 'DM Mono', monospace; font-size: 10px;
    letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase;
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}
.breadcrumb .sep { color: rgba(255,255,255,0.1); }
.breadcrumb .active { color: var(--red); }
.page-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 52px;
    letter-spacing: 0.04em; color: #fff; line-height: 1; margin-bottom: 8px;
}
.page-title span {
    background: linear-gradient(90deg, var(--red), var(--gold));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.page-caption {
    font-family: 'DM Mono', monospace; font-size: 11px;
    letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase;
}

/* Section headers */
.section-hdr { display: flex; align-items: center; gap: 16px; margin: 40px 0 20px; }
.section-hdr-label {
    font-family: 'DM Mono', monospace; font-size: 10px;
    letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; white-space: nowrap;
}
.section-hdr::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, var(--border), transparent);
}
.upload-label { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.upload-label span {
    font-family: 'DM Mono', monospace; font-size: 10px;
    letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; white-space: nowrap;
}
.upload-label::after { content: ''; flex: 1; height: 1px; background: linear-gradient(to right, var(--border), transparent); }

/* Result cards — all written as static CSS, no dynamic classes needed */
.result-grid {
    display: flex; flex-direction: column;
    gap: 1px; background: var(--border); border: 1px solid var(--border);
    margin-bottom: 40px;
}
.result-card {
    background: var(--bg2); padding: 20px 28px;
    display: flex; align-items: center; gap: 20px;
    position: relative; overflow: hidden;
    transition: background 0.3s;
}
.result-card:hover { background: var(--bg3); }
.result-accent {
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
}
.accent-green { background: var(--green); }
.accent-gold  { background: var(--gold); }

.result-rank {
    font-family: 'Bebas Neue', sans-serif; font-size: 36px;
    color: rgba(255,255,255,0.08); min-width: 40px; text-align: center;
}
.result-info { flex: 1; min-width: 0; }
.result-name { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 4px; letter-spacing: -0.01em; }
.result-status {
    font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
}
.status-green { color: var(--green); }
.status-gold  { color: var(--gold); }

.result-bar-wrap { flex: 1; }
.result-bar-track { width: 100%; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.bar-green { height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--green), var(--blue)); }
.bar-gold  { height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--gold), var(--red)); }

.result-pct {
    font-family: 'Bebas Neue', sans-serif; font-size: 28px;
    letter-spacing: 0.05em; min-width: 80px; text-align: right;
}
.pct-green { color: var(--green); }
.pct-gold  { color: var(--gold); }

/* Prob rows */
.prob-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.prob-name { font-size: 12px; color: var(--text); min-width: 180px; }
.prob-track { flex: 1; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; }
.prob-fill  { height: 100%; border-radius: 2px; background: rgba(0,255,170,0.4); }
.prob-val   { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--muted); min-width: 50px; text-align: right; }

/* Image frame */
.img-frame { border: 1px solid var(--border); padding: 4px; background: var(--bg2); margin-bottom: 8px; }
.img-meta  { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--muted); letter-spacing: 0.1em; margin-top: 8px; }

/* Sidebar */
.sidebar-module {
    font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.2em;
    color: var(--red); text-transform: uppercase; margin-bottom: 24px; padding: 6px 12px;
    background: rgba(255,77,109,0.05); border: 1px solid rgba(255,77,109,0.15);
    border-radius: 2px; text-align: center;
}
.sidebar-label {
    font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.15em;
    color: var(--muted); text-transform: uppercase;
    margin: 20px 0 8px; padding-bottom: 6px; border-bottom: 1px solid var(--border);
}
.sidebar-info { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--muted); letter-spacing: 0.06em; line-height: 1.9; }
.back-btn button {
    background: transparent !important; border: 1px solid var(--border) !important;
    color: var(--muted) !important; font-family: 'DM Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.12em !important;
    width: 100% !important; text-transform: uppercase !important;
}
.back-btn button:hover { border-color: rgba(255,255,255,0.15) !important; color: #fff !important; }

[data-testid="stExpander"] { border: 1px solid var(--border) !important; background: var(--bg2) !important; border-radius: 0 !important; }
[data-testid="stExpander"] summary { font-family: 'DM Mono', monospace !important; font-size: 11px !important; letter-spacing: 0.1em !important; color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)


# ── Model ──────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = ChartPatternCNN(num_classes=NUM_CLASSES)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    model.to(device).eval()
    return model, device

def predict(image: Image.Image, model, device):
    tensor = INFER_TRANSFORM(image).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = torch.sigmoid(model(tensor))[0]
    top_probs, top_idxs = torch.topk(probs, TOP_K)
    return probs, top_idxs, top_probs

def build_card(rank, label, confidence, detected):
    """Build a single result card as a self-contained HTML string."""
    accent = "accent-green" if detected else "accent-gold"
    bar    = "bar-green"    if detected else "bar-gold"
    pct    = "pct-green"    if detected else "pct-gold"
    status_cls  = "status-green" if detected else "status-gold"
    status_text = "DETECTED"     if detected else "LOW CONFIDENCE"
    return (
        f'<div class="result-card">'
        f'<div class="result-accent {accent}"></div>'
        f'<div class="result-rank">{rank}</div>'
        f'<div class="result-info">'
        f'<div class="result-name">{label}</div>'
        f'<div class="result-status {status_cls}">{status_text}</div>'
        f'</div>'
        f'<div class="result-bar-wrap">'
        f'<div class="result-bar-track">'
        f'<div class="{bar}" style="width:{confidence:.1f}%"></div>'
        f'</div></div>'
        f'<div class="result-pct {pct}">{confidence:.1f}%</div>'
        f'</div>'
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-module">MODULE 02 · PATTERN DETECTOR</div>', unsafe_allow_html=True)
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Back to Home", key="back_home"):
        st.switch_page("home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Model Config</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-info">
        Classes: {NUM_CLASSES}<br>
        Top-K results: {TOP_K}<br>
        Threshold: {THRESHOLD}<br>
        Input: 224 × 224 px<br>
        Activation: Sigmoid
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Pattern Classes</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-info">' + '<br>'.join(CLASS_NAMES) + '</div>',
        unsafe_allow_html=True
    )


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="breadcrumb">
        <span>Trade Sphere</span><span class="sep">›</span><span class="active">Pattern Detector</span>
    </div>
    <div class="page-title">PATTERN <span>DETECTOR</span></div>
    <div class="page-caption">CNN · Multi-label · 20 classical chart patterns · Upload any candlestick image</div>
</div>
""", unsafe_allow_html=True)

# ── Uploader in main area ──────────────────────────────────────────────────────
st.markdown('<div class="upload-label"><span>01 — Upload Chart Image</span></div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is None:
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:11px;color:#3d4d60;
    letter-spacing:0.1em;text-align:center;padding:32px 0;">
    ↑ &nbsp; DROP A CANDLESTICK CHART IMAGE ABOVE TO BEGIN ANALYSIS
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Run inference ──────────────────────────────────────────────────────────────
image = Image.open(uploaded_file).convert("RGB")
model, device = load_model()

with st.spinner(""):
    all_probs, top_idxs, top_probs = predict(image, model, device)

results = [
    (rank, CLASS_NAMES[idx], float(prob) * 100, float(prob) >= THRESHOLD)
    for rank, (idx, prob) in enumerate(zip(top_idxs.tolist(), top_probs.tolist()), start=1)
]

# ── Layout ─────────────────────────────────────────────────────────────────────
col_img, col_res = st.columns([1, 1], gap="large")

with col_img:
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">02 — Uploaded Chart</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="img-frame">', unsafe_allow_html=True)
    st.image(image, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="img-meta">{image.width} × {image.height} px · RGB</div>', unsafe_allow_html=True)

with col_res:
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">03 — Detection Results</span></div>', unsafe_allow_html=True)

    # Build ALL cards as a single HTML string — avoids Streamlit's partial render issue
    all_cards = (
        '<div class="result-grid">'
        + build_card(*results[0])
        + build_card(*results[1])
        + build_card(*results[2])
        + '</div>'
    )
    st.markdown(all_cards, unsafe_allow_html=True)

# ── All class probabilities ────────────────────────────────────────────────────
st.markdown('<div class="section-hdr"><span class="section-hdr-label">04 — All Class Probabilities</span></div>', unsafe_allow_html=True)

all_data = sorted(
    zip(CLASS_NAMES, [round(float(p) * 100, 2) for p in all_probs.tolist()]),
    key=lambda x: x[1], reverse=True
)
prob_rows = "".join(
    f'<div class="prob-row">'
    f'<div class="prob-name">{name}</div>'
    f'<div class="prob-track"><div class="prob-fill" style="width:{conf}%"></div></div>'
    f'<div class="prob-val">{conf:.1f}%</div>'
    f'</div>'
    for name, conf in all_data
)

with st.expander("SHOW ALL 20 PATTERNS"):
    st.markdown(prob_rows, unsafe_allow_html=True)