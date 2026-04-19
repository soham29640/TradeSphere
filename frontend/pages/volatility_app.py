import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.graph_objects as go
from arch import arch_model
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Layer
import tensorflow.keras.backend as K

# ── Custom layer ───────────────────────────────────────────────────────────────
class AttentionSum(Layer):
    def call(self, inputs):
        attention, lstm_output = inputs
        return K.sum(attention * lstm_output, axis=1)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Volatility Forecast · Trade Sphere",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    --purple: #a855f7;
    --orange: #fb923c;
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
        radial-gradient(ellipse 70% 40% at 80% 0%, rgba(168,85,247,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 10% 80%, rgba(0,194,255,0.04) 0%, transparent 60%),
        var(--bg) !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 48px 48px !important; }

/* Page header */
.page-header { padding: 40px 0 32px; border-bottom: 1px solid var(--border); margin-bottom: 0; }
.breadcrumb { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
.breadcrumb .sep { color: rgba(255,255,255,0.1); }
.breadcrumb .active { color: var(--purple); }
.page-title { font-family: 'Bebas Neue', sans-serif; font-size: 52px; letter-spacing: 0.04em; color: #fff; line-height: 1; margin-bottom: 8px; }
.page-title span { background: linear-gradient(90deg, var(--purple), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.page-caption { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase; }

/* Control bar */
.ctrl-lbl { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; margin-bottom: 10px; }
.ctrl-hint { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--purple); letter-spacing: 0.08em; margin-top: 6px; }

[data-testid="stSlider"] > div > div > div > div { background: var(--purple) !important; }
[data-testid="stSlider"] label { display: none !important; }
[data-testid="stFileUploader"] { background: rgba(168,85,247,0.03) !important; border: 1px dashed rgba(168,85,247,0.2) !important; border-radius: 0 !important; }
[data-testid="stFileUploader"] label { display: none !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzone"] button { background: rgba(168,85,247,0.1) !important; border: 1px solid rgba(168,85,247,0.3) !important; color: var(--purple) !important; font-family: 'DM Mono', monospace !important; font-size: 11px !important; border-radius: 2px !important; }

.back-btn button { background: transparent !important; border: 1px solid var(--border) !important; color: var(--muted) !important; font-family: 'DM Mono', monospace !important; font-size: 10px !important; letter-spacing: 0.12em !important; width: 100% !important; text-transform: uppercase !important; }
.back-btn button:hover { border-color: rgba(255,255,255,0.15) !important; color: #fff !important; }

/* Section headers */
.section-hdr { display: flex; align-items: center; gap: 16px; margin: 40px 0 20px; }
.section-hdr-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; white-space: nowrap; }
.section-hdr::after { content: ''; flex: 1; height: 1px; background: linear-gradient(to right, var(--border), transparent); }

/* Risk metric cards */
.risk-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--border); border: 1px solid var(--border); margin-bottom: 40px; }
.risk-card { background: var(--bg2); padding: 28px 32px; position: relative; overflow: hidden; transition: background 0.3s; }
.risk-card:hover { background: var(--bg3); }
.risk-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; }
.risk-card.purple::before { background: linear-gradient(90deg, transparent, var(--purple), transparent); }
.risk-card.orange::before { background: linear-gradient(90deg, transparent, var(--orange), transparent); }
.risk-card.blue::before   { background: linear-gradient(90deg, transparent, var(--blue), transparent); }
.risk-model { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.18em; color: var(--muted); text-transform: uppercase; margin-bottom: 14px; }
.risk-val { font-family: 'Bebas Neue', sans-serif; font-size: 40px; letter-spacing: 0.04em; color: #fff; line-height: 1; margin-bottom: 10px; }
.risk-badge { display: inline-flex; align-items: center; gap: 8px; font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; padding: 5px 12px; border-radius: 2px; }
.risk-badge.high { color: var(--red);   background: rgba(255,77,109,0.08);  border: 1px solid rgba(255,77,109,0.2); }
.risk-badge.low  { color: var(--green); background: rgba(0,255,170,0.08);   border: 1px solid rgba(0,255,170,0.2); }

/* Chart wrap */
.chart-wrap { border: 1px solid var(--border); background: var(--bg2); padding: 4px; margin-bottom: 24px; }

/* Eval metric grid — 3 equal cols */
.eval-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    margin-bottom: 40px;
    width: 100%;
}
.eval-card {
    background: var(--bg2);
    padding: 28px 32px;
    position: relative;
    overflow: hidden;
    transition: background 0.3s;
}
.eval-card:hover { background: var(--bg3); }
.eval-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
}
.eval-card.ev-blue::before   { background: linear-gradient(90deg, transparent, var(--blue), transparent); }
.eval-card.ev-purple::before { background: linear-gradient(90deg, transparent, var(--purple), transparent); }
.eval-card.ev-orange::before { background: linear-gradient(90deg, transparent, var(--orange), transparent); }

.eval-model {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 20px;
}
.eval-metrics { display: flex; gap: 28px; flex-wrap: wrap; }
.eval-metric { display: flex; flex-direction: column; }
.eval-metric-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 32px;
    color: #fff;
    letter-spacing: 0.04em;
    line-height: 1;
    margin-bottom: 6px;
}
.eval-metric-lbl {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
}
/* Color accents per metric */
.eval-metric-val.rmse { color: var(--blue); }
.eval-metric-val.mae  { color: var(--purple); }
.eval-metric-val.mse  { color: var(--orange); }

/* Data table */
[data-testid="stExpander"] { border: 1px solid var(--border) !important; background: var(--bg2) !important; border-radius: 0 !important; }
[data-testid="stExpander"] summary { font-family: 'DM Mono', monospace !important; font-size: 11px !important; letter-spacing: 0.1em !important; color: var(--muted) !important; }

/* Info box */
.info-box { border: 1px solid rgba(168,85,247,0.2); background: rgba(168,85,247,0.04); padding: 20px 24px; margin-bottom: 40px; font-family: 'DM Mono', monospace; font-size: 11px; color: var(--muted); letter-spacing: 0.06em; line-height: 1.9; }
.info-box strong { color: var(--purple); }

/* Best model banner */
.best-model-banner {
    border: 1px solid rgba(0,194,255,0.2);
    background: rgba(0,194,255,0.04);
    padding: 14px 24px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    color: var(--muted);
}
.best-model-banner .best-label { color: var(--blue); text-transform: uppercase; letter-spacing: 0.15em; }
.best-model-banner .best-name  { color: #fff; font-size: 13px; }
.best-model-banner .best-sep   { color: rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="breadcrumb">
        <span>Trade Sphere</span><span class="sep">›</span><span class="active">Volatility Forecast</span>
    </div>
    <div class="page-title">VOLATILITY <span>FORECAST</span></div>
    <div class="page-caption">GARCH · LSTM · Attention-LSTM · Next-day risk classification · 75th percentile threshold</div>
</div>
""", unsafe_allow_html=True)

# ── Control bar ────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns([1, 2, 1])

with ctrl1:
    st.markdown('<div class="ctrl-lbl">Historical Window</div>', unsafe_allow_html=True)
    num_days = st.slider("days", min_value=150, max_value=250, value=200, step=10, label_visibility="collapsed")
    st.markdown(f'<div class="ctrl-hint">{num_days} trading days</div>', unsafe_allow_html=True)

with ctrl2:
    st.markdown('<div class="ctrl-lbl">Upload Returns Data (optional)</div>', unsafe_allow_html=True)
    file = st.file_uploader("upload", type=["csv"], label_visibility="collapsed")

with ctrl3:
    st.markdown('<div class="ctrl-lbl">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Back to Home", key="back_home"):
        st.switch_page("home.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:var(--border);margin:8px 0 32px;"></div>', unsafe_allow_html=True)

# ── Info box ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
    <strong>How it works:</strong> &nbsp; Each model independently forecasts next-day volatility from log returns.
    Predictions are classified as <strong style="color:#ff4d6d;">HIGH RISK</strong> or
    <strong style="color:#00ffaa;">LOW RISK</strong> by comparing against the
    <strong>75th percentile</strong> of recent historical volatility.
    Lower volatility = lower risk.
</div>
""", unsafe_allow_html=True)

# ── Load & process data ────────────────────────────────────────────────────────
if file:
    data = pd.read_csv(file, index_col=0, parse_dates=True)
else:
    data = pd.read_csv("data/raw/volatility/AAPL.csv", index_col=0, parse_dates=True)

data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
data = data.tail(num_days)
data.dropna(subset=['log_return'], inplace=True)

log_return         = data['log_return'].values.reshape(-1, 1)
log_return_squared = log_return ** 2

scaler_X = StandardScaler()
scaled_X = scaler_X.fit_transform(log_return)

scaler_y = StandardScaler()
scaled_y = scaler_y.fit_transform(log_return_squared)

seq_len = 10

# ── Run models ─────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_models():
    lstm_m = load_model("models/volatility/lstm_model.h5")
    attn_m = load_model("models/volatility/attention_model.h5", custom_objects={"AttentionSum": AttentionSum})
    return lstm_m, attn_m

try:
    lstm_model, attn_model = load_models()

    X_next = scaled_X[-seq_len:].reshape(1, seq_len, 1)

    pred_lstm = lstm_model.predict(X_next, verbose=0)
    pred_lstm = np.sqrt(np.clip(scaler_y.inverse_transform(pred_lstm), 0, None))[0][0]

    pred_attn = attn_model.predict(X_next, verbose=0)
    pred_attn = np.sqrt(np.clip(scaler_y.inverse_transform(pred_attn), 0, None))[0][0]

    garch_mdl = arch_model(log_return.squeeze(), vol='GARCH', p=1, q=1)
    garch_fit = garch_mdl.fit(disp='off')
    pred_garch = np.sqrt(garch_fit.forecast(horizon=1).variance.values[-1][0])

    # Risk threshold
    vol_history = np.sqrt(np.clip(scaler_y.inverse_transform(scaled_y), 0, None))
    threshold   = float(np.percentile(vol_history, 75))

    def risk_cls(v): return "high" if v > threshold else "low"
    def risk_txt(v): return "HIGH RISK" if v > threshold else "LOW RISK"

    # ── Risk cards ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">01 — Next-Day Volatility Forecast</span></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="risk-grid">
        <div class="risk-card purple">
            <div class="risk-model">LSTM Model</div>
            <div class="risk-val">{pred_lstm:.6f}</div>
            <div class="risk-badge {risk_cls(pred_lstm)}">{risk_txt(pred_lstm)}</div>
        </div>
        <div class="risk-card orange">
            <div class="risk-model">Attention-LSTM Model</div>
            <div class="risk-val">{pred_attn:.6f}</div>
            <div class="risk-badge {risk_cls(pred_attn)}">{risk_txt(pred_attn)}</div>
        </div>
        <div class="risk-card blue">
            <div class="risk-model">GARCH(1,1) Model</div>
            <div class="risk-val">{pred_garch:.6f}</div>
            <div class="risk-badge {risk_cls(pred_garch)}">{risk_txt(pred_garch)}</div>
        </div>
    </div>
    <div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);
    letter-spacing:0.1em;margin-bottom:40px;">
    75th PERCENTILE THRESHOLD: &nbsp;<span style="color:var(--purple);">{threshold:.6f}</span>
    &nbsp;·&nbsp; Window: {num_days} days
    </div>
    """, unsafe_allow_html=True)

    # ── Forecast chart ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">02 — Volatility Forecast vs Historical</span></div>', unsafe_allow_html=True)

    hist_vol = data['log_return'].rolling(window=20).std().dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_vol.index[-100:], y=hist_vol.values[-100:],
        mode="lines", name="Historical Volatility",
        line=dict(color="rgba(200,210,230,0.5)", width=1.5),
    ))
    fig.add_hline(y=pred_lstm,  line=dict(color="#a855f7", width=1.5, dash="dot"),  annotation_text="LSTM",     annotation_font=dict(color="#a855f7",  size=10, family="DM Mono"))
    fig.add_hline(y=pred_attn,  line=dict(color="#fb923c", width=1.5, dash="dot"),  annotation_text="ATTN-LSTM",annotation_font=dict(color="#fb923c",  size=10, family="DM Mono"))
    fig.add_hline(y=pred_garch, line=dict(color="#00c2ff", width=1.5, dash="dot"),  annotation_text="GARCH",    annotation_font=dict(color="#00c2ff",  size=10, family="DM Mono"))
    fig.add_hline(y=threshold,  line=dict(color="#ff4d6d", width=1,   dash="dash"), annotation_text="75% THRESHOLD", annotation_font=dict(color="#ff4d6d", size=10, family="DM Mono"))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono", color="#3d4d60", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6b7a90")),
        hovermode="x unified", margin=dict(l=20, r=120, t=20, b=20), height=400,
    )
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Evaluation metrics ──────────────────────────────────────────────────────
    eval_path = "data/processed/volatility/outputs/predictions/evaluation_metrics.csv"
    if os.path.exists(eval_path):
        st.markdown('<div class="section-hdr"><span class="section-hdr-label">03 — Model Evaluation Metrics</span></div>', unsafe_allow_html=True)
        eval_df = pd.read_csv(eval_path)

        # Normalize column names (strip whitespace, title-case)
        eval_df.columns = [c.strip() for c in eval_df.columns]

        # Map accent colours per model
        accent_map = {
            "garch":          "ev-blue",
            "lstm":           "ev-purple",
            "attention_lstm": "ev-orange",
            "attn_lstm":      "ev-orange",
            "attention-lstm": "ev-orange",
        }

        def accent_for(model_name: str) -> str:
            key = model_name.strip().lower().replace(" ", "_")
            for k, v in accent_map.items():
                if k in key:
                    return v
            return "ev-purple"

        card_parts = []
        for _, row in eval_df.iterrows():
            model_name = str(row.get("Model", row.get("model", "Unknown")))
            rmse_val   = float(row.get("RMSE",  row.get("rmse",  0)))
            mae_val    = float(row.get("MAE",   row.get("mae",   0)))
            mse_val    = float(row.get("MSE",   row.get("mse",   0)))
            accent     = accent_for(model_name)
            # NO leading spaces — Streamlit markdown treats 4-space indent as a code block
            card_parts.append(
f'<div class="eval-card {accent}">'
f'<div class="eval-model">{model_name}</div>'
f'<div class="eval-metrics">'
f'<div class="eval-metric"><div class="eval-metric-val rmse">{rmse_val:.5f}</div><div class="eval-metric-lbl">RMSE</div></div>'
f'<div class="eval-metric"><div class="eval-metric-val mae">{mae_val:.5f}</div><div class="eval-metric-lbl">MAE</div></div>'
f'<div class="eval-metric"><div class="eval-metric-val mse">{mse_val:.5f}</div><div class="eval-metric-lbl">MSE</div></div>'
f'</div></div>'
            )
        cards_html = '<div class="eval-grid">' + "".join(card_parts) + '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # Best model banner (lowest RMSE)
        best_row = eval_df.loc[eval_df["RMSE"].astype(float).idxmin()]
        best_name = str(best_row.get("Model", best_row.get("model", "—")))
        best_rmse = float(best_row.get("RMSE", best_row.get("rmse", 0)))
        st.markdown(f"""
        <div class="best-model-banner">
            <span class="best-label">Best Performer</span>
            <span class="best-sep">·</span>
            <span class="best-name">{best_name}</span>
            <span class="best-sep">·</span>
            <span>Lowest RMSE &nbsp;<span style="color:var(--blue);">{best_rmse:.5f}</span></span>
        </div>
        """, unsafe_allow_html=True)

    # ── Raw data ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">04 — Raw Data</span></div>', unsafe_allow_html=True)
    with st.expander("VIEW RAW DATA"):
        st.dataframe(
            data.tail(50).style.set_properties(**{
                "background-color": "#090d12",
                "color": "#cdd5e0",
                "font-family": "DM Mono, monospace",
                "font-size": "12px",
            }),
            use_container_width=True
        )

except FileNotFoundError:
    st.markdown("""
    <div style="border:1px solid rgba(168,85,247,0.3);background:rgba(168,85,247,0.05);
    padding:24px 28px;font-family:'DM Mono',monospace;font-size:13px;color:#a855f7;">
    ⚠ &nbsp; Model files not found. Train models first:<br><br>
    <span style="color:#3d4d60;">python backend/volatility/model_lstm.py<br>
    python backend/volatility/model_attention.py</span>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div style="border:1px solid rgba(255,77,109,0.3);background:rgba(255,77,109,0.05);
    padding:24px 28px;font-family:'DM Mono',monospace;font-size:13px;color:#ff4d6d;">
    ❌ &nbsp; {e}
    </div>
    """, unsafe_allow_html=True)