import os
import sys
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.price.load_and_predict_price_model import predict_next_prices

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Price Predictor · Trade Sphere",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st_autorefresh(interval=300_000, key="auto_refresh")

WINDOW = 60

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700;900&display=swap');

:root {
    --green:  #00ffaa;
    --blue:   #00c2ff;
    --red:    #ff4d6d;
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
        radial-gradient(ellipse 70% 40% at 10% 0%, rgba(0,255,170,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 90% 80%, rgba(0,194,255,0.04) 0%, transparent 60%),
        var(--bg) !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 48px 48px !important; }

/* ── Page header ── */
.page-header { padding: 40px 0 32px; border-bottom: 1px solid var(--border); margin-bottom: 0; }
.breadcrumb {
    font-family: 'DM Mono', monospace; font-size: 10px;
    letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase;
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}
.breadcrumb .sep { color: rgba(255,255,255,0.1); }
.breadcrumb .active { color: var(--green); }
.page-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 52px;
    letter-spacing: 0.04em; color: #fff; line-height: 1; margin-bottom: 8px;
}
.page-title span {
    background: linear-gradient(90deg, var(--green), var(--blue));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.page-caption {
    font-family: 'DM Mono', monospace; font-size: 11px;
    letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase;
    display: flex; align-items: center; gap: 10px;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--green);
    display: inline-block; box-shadow: 0 0 0 0 rgba(0,255,170,0.4);
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(0,255,170,0.5); }
    70%  { box-shadow: 0 0 0 8px rgba(0,255,170,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,255,170,0); }
}

/* ── Control bar ── */
.control-bar {
    display: grid; grid-template-columns: 1fr 2fr auto;
    gap: 1px; background: var(--border);
    border: 1px solid var(--border);
    border-top: none; margin-bottom: 40px;
}
.control-cell {
    background: var(--bg2); padding: 20px 28px;
    transition: background 0.2s;
}
.control-cell:hover { background: var(--bg3); }
.control-lbl {
    font-family: 'DM Mono', monospace; font-size: 9px;
    letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase;
    margin-bottom: 10px;
}
.control-hint {
    font-family: 'DM Mono', monospace; font-size: 10px;
    color: var(--green); letter-spacing: 0.08em; margin-top: 6px;
}

/* Override Streamlit inputs inside control bar */
[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0 !important; color: #fff !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 28px !important; letter-spacing: 0.06em !important;
    padding: 0 0 6px 0 !important; box-shadow: none !important;
}
[data-testid="stTextInput"] input:focus {
    border-bottom-color: var(--green) !important; box-shadow: none !important;
}
[data-testid="stTextInput"] label { display: none !important; }

[data-testid="stSlider"] > div > div > div > div { background: var(--green) !important; }
[data-testid="stSlider"] label { display: none !important; }
[data-testid="stSlider"] * { color: var(--muted) !important; font-family: 'DM Mono', monospace !important; }

/* Back button */
.back-cell button {
    background: transparent !important; border: none !important;
    color: var(--muted) !important; font-family: 'DM Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; padding: 0 !important;
    box-shadow: none !important; height: auto !important;
}
.back-cell button:hover { color: #fff !important; }

/* ── Metric cards ── */
.metric-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1px; background: var(--border);
    border: 1px solid var(--border); margin-bottom: 40px;
}
.metric-card { background: var(--bg2); padding: 28px 32px; position: relative; overflow: hidden; transition: background 0.3s; }
.metric-card:hover { background: var(--bg3); }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; }
.metric-card.green::before { background: linear-gradient(90deg, transparent, var(--green), transparent); }
.metric-card.blue::before  { background: linear-gradient(90deg, transparent, var(--blue), transparent); }
.metric-card.muted::before { background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); }
.metric-lbl { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.18em; color: var(--muted); text-transform: uppercase; margin-bottom: 14px; }
.metric-val { font-family: 'Bebas Neue', sans-serif; font-size: 44px; letter-spacing: 0.04em; color: #fff; line-height: 1; margin-bottom: 6px; }
.metric-delta { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; }
.metric-delta.up  { color: var(--green); }
.metric-delta.dn  { color: var(--red); }
.metric-delta.neu { color: var(--muted); }

/* ── Section headers ── */
.section-hdr { display: flex; align-items: center; gap: 16px; margin: 40px 0 20px; }
.section-hdr-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; white-space: nowrap; }
.section-hdr::after { content: ''; flex: 1; height: 1px; background: linear-gradient(to right, var(--border), transparent); }

/* ── Chart wrap ── */
.chart-wrap { border: 1px solid var(--border); background: var(--bg2); padding: 4px; margin-bottom: 24px; }

/* ── Expander ── */
[data-testid="stExpander"] { border: 1px solid var(--border) !important; background: var(--bg2) !important; border-radius: 0 !important; }
[data-testid="stExpander"] summary { font-family: 'DM Mono', monospace !important; font-size: 11px !important; letter-spacing: 0.1em !important; color: var(--muted) !important; }

[data-testid="stMetric"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="breadcrumb">
        <span>Trade Sphere</span>
        <span class="sep">›</span>
        <span class="active">Price Predictor</span>
    </div>
    <div class="page-title">PRICE <span>PREDICTOR</span></div>
</div>
""", unsafe_allow_html=True)

# ── Inline control bar ─────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns([1, 2, 1])

with ctrl1:
    st.markdown('<div class="control-lbl">Stock Ticker</div>', unsafe_allow_html=True)
    ticker = st.text_input("ticker", value="AAPL", label_visibility="collapsed").upper().strip()

with ctrl2:
    st.markdown('<div class="control-lbl">Prediction Horizon</div>', unsafe_allow_html=True)
    horizon = st.slider("horizon", 5, 30, 10, label_visibility="collapsed")
    st.markdown(
        f'<div class="control-hint">{horizon} bars · {horizon * 5} min ahead</div>',
        unsafe_allow_html=True
    )

with ctrl3:
    st.markdown('<div class="control-lbl">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div class="back-cell">', unsafe_allow_html=True)
    if st.button("← Back to Home", key="back_home"):
        st.switch_page("home.py")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'DM Mono\',monospace;font-size:9px;color:#3d4d60;'
        'letter-spacing:0.08em;margin-top:8px;line-height:1.8;">Local CSV · Auto-refresh 5min<br>Retrain: 24hr</div>',
        unsafe_allow_html=True
    )

# Thin separator
st.markdown('<div style="height:1px;background:var(--border);margin:0 0 40px;"></div>', unsafe_allow_html=True)

# Live caption
st.markdown(f"""
<div class="page-caption" style="margin-bottom:32px;">
    <span class="live-dot"></span>
    {ticker} &nbsp;·&nbsp; 5-min bars &nbsp;·&nbsp; LSTM forecast &nbsp;·&nbsp; horizon {horizon * 5}min
</div>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data(ticker: str):
    path = f"data/raw/price/{ticker}.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run update_data.py first.")
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

try:
    with st.spinner(""):
        df = load_data(ticker)

    if df.empty:
        st.error("No data available.")
        st.stop()

    required_cols = ["Date", "Open", "High", "Low", "Close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    if len(df) < WINDOW:
        st.error(f"Need at least {WINDOW} rows, got {len(df)}.")
        st.stop()

    df = df.tail(500)
    current_price = float(df["Close"].iloc[-1])
    prev_price    = float(df["Close"].iloc[-2])
    price_chg     = (current_price - prev_price) / prev_price * 100

    with st.spinner(""):
        predictions = predict_next_prices(df, window_size=WINDOW, horizon=horizon)

    next_price = float(predictions[0])
    change_pct = (next_price - current_price) / current_price * 100
    delta_cls  = "up" if change_pct >= 0 else "dn"
    delta_sym  = "▲" if change_pct >= 0 else "▼"
    curr_cls   = "up" if price_chg >= 0 else "dn"
    curr_sym   = "▲" if price_chg >= 0 else "▼"

    # ── Metrics ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card green">
            <div class="metric-lbl">Current Price</div>
            <div class="metric-val">${current_price:.2f}</div>
            <div class="metric-delta {curr_cls}">{curr_sym} {abs(price_chg):.2f}% vs prev bar</div>
        </div>
        <div class="metric-card blue">
            <div class="metric-lbl">Next Predicted Price</div>
            <div class="metric-val">${next_price:.2f}</div>
            <div class="metric-delta {delta_cls}">{delta_sym} {abs(change_pct):.2f}% forecast</div>
        </div>
        <div class="metric-card muted">
            <div class="metric-lbl">Prediction Horizon</div>
            <div class="metric-val">{horizon}</div>
            <div class="metric-delta neu">bars · {horizon * 5} minutes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Candlestick ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">01 — Candlestick Data</span></div>', unsafe_allow_html=True)

    candle_fig = go.Figure(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00ffaa", increasing_fillcolor="rgba(0,255,170,0.6)",
        decreasing_line_color="#ff4d6d", decreasing_fillcolor="rgba(255,77,109,0.6)",
    ))
    candle_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono", color="#3d4d60", size=11),
        title=dict(text=f"{ticker} — Recent Candlestick Data", font=dict(color="#fff", size=14, family="Outfit")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=50, b=20), height=420,
    )
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(candle_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">02 — Price Forecast</span></div>', unsafe_allow_html=True)

    future_times = pd.date_range(
        start=df["Date"].iloc[-1] + pd.Timedelta(minutes=5),
        periods=horizon, freq="5min"
    )
    forecast = pd.Series(predictions, index=future_times)

    forecast_fig = go.Figure()
    forecast_fig.add_trace(go.Scatter(
        x=df["Date"].tail(100), y=df["Close"].tail(100),
        mode="lines", name="Actual",
        line=dict(color="rgba(0,194,255,0.8)", width=2),
    ))
    forecast_fig.add_trace(go.Scatter(
        x=forecast.index, y=forecast.values,
        mode="lines+markers", name="Predicted",
        line=dict(color="#00ffaa", width=2, dash="dot"),
        marker=dict(color="#00ffaa", size=5),
    ))
    forecast_fig.add_trace(go.Scatter(
        x=[df["Date"].iloc[-1], forecast.index[0]],
        y=[df["Close"].iloc[-1], forecast.values[0]],
        mode="lines", showlegend=False,
        line=dict(color="rgba(0,255,170,0.3)", width=1, dash="dot"),
    ))
    forecast_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono", color="#3d4d60", size=11),
        title=dict(text=f"{ticker} — Forecast ({horizon * 5} min ahead)", font=dict(color="#fff", size=14, family="Outfit")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6b7a90")),
        hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), height=380,
    )
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(forecast_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Raw data ──────────────────────────────────────────────────────────────────
    with st.expander("VIEW RAW DATA"):
        st.dataframe(
            df.tail(50).style.set_properties(**{
                "background-color": "#090d12",
                "color": "#cdd5e0",
                "font-family": "DM Mono, monospace",
                "font-size": "12px",
            }),
            use_container_width=True
        )

except FileNotFoundError as e:
    st.markdown(f"""
    <div style="border:1px solid rgba(255,77,109,0.3);background:rgba(255,77,109,0.05);
    padding:24px 28px;font-family:'DM Mono',monospace;font-size:13px;color:#ff4d6d;">
    ⚠ &nbsp; {e}<br><br>
    <span style="color:#3d4d60;">Run: python backend/price/update_data.py</span>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div style="border:1px solid rgba(255,77,109,0.3);background:rgba(255,77,109,0.05);
    padding:24px 28px;font-family:'DM Mono',monospace;font-size:13px;color:#ff4d6d;">
    ❌ &nbsp; {e}
    </div>
    """, unsafe_allow_html=True)