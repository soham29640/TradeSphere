"""
paper_app.py
────────────
Condition 1 — MARKET LIVE (≥ 25 min / 5 bars of today's 5-min data):
    • Auto-refresh every 5 minutes
    • On each refresh: LSTM retrains on (last-day-minus-25min + today) 5-min bars
    • Trading window: OPEN for 1 min after each refresh → LOCKED for 4 min
    • Chart: gap-free slice = last (last_day_bars - today_bars) + today bars

Condition 2 — MARKET CLOSED (< 25 min today OR market not open):
    • Shows last complete session chart (5-min bars, static)
    • NO LSTM, NO prediction, NO buy/sell panel
"""

import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.paper.paper_trade       import PaperTrader
from backend.paper.data_loader       import get_market_state
from backend.paper.train_and_predict import train_and_predict

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Paper Trading · Trade Sphere",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auto-refresh every 5 minutes (live cadence = 5-min bars) ─────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=300_000, key="paper_refresh")   # 300 000 ms = 5 min
except ImportError:
    pass

# ── Styles ────────────────────────────────────────────────────────────────────
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
        radial-gradient(ellipse 70% 40% at 80% 0%, rgba(0,194,255,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 10% 80%, rgba(168,85,247,0.04) 0%, transparent 60%),
        var(--bg) !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 48px 64px !important; }

/* Page header */
.page-header { padding: 40px 0 32px; border-bottom: 1px solid var(--border); margin-bottom: 0; }
.breadcrumb { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.2em;
    color: var(--muted); text-transform: uppercase; margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px; }
.breadcrumb .sep { color: rgba(255,255,255,0.1); }
.breadcrumb .active { color: var(--blue); }
.page-title { font-family: 'Bebas Neue', sans-serif; font-size: 52px; letter-spacing: 0.04em;
    color: #fff; line-height: 1; margin-bottom: 8px; }
.page-title span { background: linear-gradient(90deg, var(--blue), var(--green));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.page-caption { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 0.1em;
    color: var(--muted); text-transform: uppercase; }

/* Section headers */
.section-hdr { display: flex; align-items: center; gap: 16px; margin: 36px 0 18px; }
.section-hdr-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.2em;
    color: var(--muted); text-transform: uppercase; white-space: nowrap; }
.section-hdr::after { content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, var(--border), transparent); }

/* Status pill */
.status-pill { display: inline-flex; align-items: center; gap: 8px; font-family: 'DM Mono', monospace;
    font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 14px; border-radius: 2px; margin-bottom: 20px; }
.status-pill.live   { color: var(--green); background: rgba(0,255,170,0.07);
    border: 1px solid rgba(0,255,170,0.2); }
.status-pill.closed { color: var(--red);   background: rgba(255,77,109,0.07);
    border: 1px solid rgba(255,77,109,0.2); }
.dot { width: 7px; height: 7px; border-radius: 50%; }
.dot.green { background: var(--green); animation: pulse 1.5s infinite; }
.dot.red   { background: var(--red); }
@keyframes pulse { 0%,100%{ opacity:1; } 50%{ opacity:.3; } }

/* Closed banner */
.closed-banner { border: 1px solid rgba(255,77,109,0.2); background: rgba(255,77,109,0.04);
    padding: 20px 28px; margin-bottom: 32px; font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted); letter-spacing: 0.06em; line-height: 1.9; }
.closed-banner strong { color: var(--red); }

/* Trading window banner */
.window-open { border: 1px solid rgba(0,255,170,0.25); background: rgba(0,255,170,0.05);
    padding: 14px 24px; margin-bottom: 20px; font-family: 'DM Mono', monospace;
    font-size: 11px; letter-spacing: 0.08em; color: var(--green); }
.window-locked { border: 1px solid rgba(255,193,69,0.2); background: rgba(255,193,69,0.04);
    padding: 14px 24px; margin-bottom: 20px; font-family: 'DM Mono', monospace;
    font-size: 11px; letter-spacing: 0.08em; color: var(--gold); }

/* KPI strip */
.kpi-strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px;
    background: var(--border); border: 1px solid var(--border); margin-bottom: 32px; }
.kpi-card { background: var(--bg2); padding: 22px 24px; position: relative;
    overflow: hidden; transition: background .3s; }
.kpi-card:hover { background: var(--bg3); }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; }
.kpi-card.c-blue::before   { background: linear-gradient(90deg,transparent,var(--blue),transparent); }
.kpi-card.c-green::before  { background: linear-gradient(90deg,transparent,var(--green),transparent); }
.kpi-card.c-purple::before { background: linear-gradient(90deg,transparent,var(--purple),transparent); }
.kpi-card.c-gold::before   { background: linear-gradient(90deg,transparent,var(--gold),transparent); }
.kpi-card.c-red::before    { background: linear-gradient(90deg,transparent,var(--red),transparent); }
.kpi-lbl { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.18em;
    color: var(--muted); text-transform: uppercase; margin-bottom: 10px; }
.kpi-val { font-family: 'Bebas Neue', sans-serif; font-size: 34px;
    letter-spacing: 0.04em; color: #fff; line-height: 1; }
.kpi-val.pos { color: var(--green); }
.kpi-val.neg { color: var(--red); }
.kpi-sub { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--muted);
    margin-top: 6px; letter-spacing: 0.06em; }

/* Chart wrap */
.chart-wrap { border: 1px solid var(--border); background: var(--bg2);
    padding: 4px; margin-bottom: 24px; }

/* Model info bar */
.model-bar { border: 1px solid rgba(168,85,247,0.15); background: rgba(168,85,247,0.04);
    padding: 12px 24px; margin-bottom: 24px; display: flex; align-items: center;
    gap: 20px; flex-wrap: wrap; font-family: 'DM Mono', monospace;
    font-size: 10px; letter-spacing: 0.1em; color: var(--muted); }
.model-bar .ml { color: var(--purple); text-transform: uppercase; letter-spacing: 0.15em; }
.model-bar .mv { color: #fff; }

/* Signal box */
.signal-box { border: 1px solid var(--border); background: var(--bg2);
    padding: 28px 32px; position: relative; }
.signal-box::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg,transparent,var(--purple),transparent); }
.signal-val { font-family: 'Bebas Neue', sans-serif; font-size: 48px;
    letter-spacing: 0.06em; margin-bottom: 8px; }
.signal-val.buy  { color: var(--green); }
.signal-val.sell { color: var(--red); }
.signal-val.hold { color: var(--gold); }
.signal-chg { font-family: 'DM Mono', monospace; font-size: 11px;
    letter-spacing: 0.1em; color: var(--muted); }

/* Trade panel */
.trade-panel { border: 1px solid var(--border); background: var(--bg2);
    padding: 28px 32px; margin-bottom: 28px; position: relative; }
.trade-panel::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg,transparent,var(--blue),transparent); }
.trade-lbl { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.2em;
    color: var(--muted); text-transform: uppercase; margin-bottom: 10px; }

[data-testid="stNumberInput"] label { display: none !important; }
[data-testid="stNumberInput"] input { background: var(--bg3) !important;
    border: 1px solid var(--border) !important; color: #fff !important;
    font-family: 'DM Mono', monospace !important; border-radius: 2px !important; }

div[data-testid="column"]:nth-child(1) button {
    background: rgba(0,255,170,0.08) !important;
    border: 1px solid rgba(0,255,170,0.35) !important;
    color: var(--green) !important; font-family: 'DM Mono', monospace !important;
    font-size: 12px !important; letter-spacing: 0.14em !important;
    text-transform: uppercase !important; width: 100% !important;
    padding: 12px !important; border-radius: 2px !important; transition: background .2s !important;
}
div[data-testid="column"]:nth-child(1) button:hover { background: rgba(0,255,170,0.15) !important; }
div[data-testid="column"]:nth-child(2) button {
    background: rgba(255,77,109,0.08) !important;
    border: 1px solid rgba(255,77,109,0.35) !important;
    color: var(--red) !important; font-family: 'DM Mono', monospace !important;
    font-size: 12px !important; letter-spacing: 0.14em !important;
    text-transform: uppercase !important; width: 100% !important;
    padding: 12px !important; border-radius: 2px !important; transition: background .2s !important;
}
div[data-testid="column"]:nth-child(2) button:hover { background: rgba(255,77,109,0.15) !important; }

/* Stop-loss alert */
.sl-alert { border: 1px solid rgba(255,77,109,0.3); background: rgba(255,77,109,0.06);
    padding: 14px 20px; margin-bottom: 16px; font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--red); letter-spacing: 0.06em; }

/* Data table */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 0 !important; }

/* Divider */
.divider { height: 1px; background: var(--border); margin: 8px 0 32px; }

/* Back button */
.back-btn button { background: transparent !important; border: 1px solid var(--border) !important;
    color: var(--muted) !important; font-family: 'DM Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.12em !important;
    width: 100% !important; text-transform: uppercase !important; }
</style>
""", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="breadcrumb">
        <span>Trade Sphere</span><span class="sep">›</span>
        <span class="active">Smart Paper Trading</span>
    </div>
    <div class="page-title">SMART <span>PAPER TRADING</span></div>
    <div class="page-caption">LSTM · 5-min refresh · 1-min trade window · Dynamic training window</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Ticker selector + nav ─────────────────────────────────────────────────────
col_ticker, _, col_nav = st.columns([2, 4, 1])
with col_ticker:
    ticker = st.text_input("Ticker", value="AAPL",
                           label_visibility="collapsed").upper().strip()
with col_nav:
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Home"):
        st.switch_page("home.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Persistent session state ──────────────────────────────────────────────────
if "trader" not in st.session_state:
    st.session_state.trader = PaperTrader(
        starting_cash=100_000.0,
        stop_loss_pct=2.0,
        max_position=500,
    )
trader: PaperTrader = st.session_state.trader

# Cache: prediction result keyed by (ticker, today_bars) so we retrain
# only when a new 5-min bar arrives, not on every widget interaction.
if "pred_cache" not in st.session_state:
    st.session_state.pred_cache = {}

# Track the last refresh_key that triggered open_trading_window()
if "last_window_key" not in st.session_state:
    st.session_state.last_window_key = None

# ── Fetch market state ────────────────────────────────────────────────────────
try:
    with st.spinner("Fetching market data …"):
        state = get_market_state(ticker)
except Exception as exc:
    st.markdown(
        f'<div style="border:1px solid rgba(255,77,109,0.3);background:rgba(255,77,109,0.05);'
        f'padding:24px;font-family:DM Mono,monospace;font-size:13px;color:#ff4d6d;">'
        f'❌ Data fetch failed: {exc}</div>',
        unsafe_allow_html=True,
    )
    st.stop()

is_live       = state["is_live"]
df_chart      = state["df_chart"]
df_train      = state["df_train"]
current_price = state["current_price"]
today_bars    = state["today_bars"]
last_day_bars = state["last_day_bars"]
last_updated  = state["last_updated"]
fetch_error   = state.get("fetch_error")

# Show fetch warning banner (non-fatal — partial data may still render)
if fetch_error:
    st.markdown(
        f'<div style="border:1px solid rgba(255,193,69,0.3);background:rgba(255,193,69,0.05);'
        f'padding:14px 24px;font-family:DM Mono,monospace;font-size:11px;color:#ffc145;'
        f'letter-spacing:0.06em;margin-bottom:16px;">⚠ {fetch_error}</div>',
        unsafe_allow_html=True,
    )

# ── Market status pill ────────────────────────────────────────────────────────
if is_live:
    st.markdown(
        f'<div class="status-pill live"><div class="dot green"></div>'
        f'Market Live &nbsp;·&nbsp; {today_bars} bars today &nbsp;·&nbsp; updated {last_updated}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="status-pill closed"><div class="dot red"></div>'
        f'Market Closed &nbsp;·&nbsp; showing last session &nbsp;·&nbsp; {last_updated}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
<div class="closed-banner">
<strong>Market is closed.</strong>&nbsp; Chart shows the last complete trading session (5-min bars).
<br>LSTM training, predictions and trade execution are <strong>disabled</strong>.
<br>They activate automatically once the market opens and today's first bar is available.
</div>
""", unsafe_allow_html=True)

# ── Open trading window on each new 5-min bar (live only) ────────────────────
if is_live:
    refresh_key = f"{ticker}_{today_bars}"
    if st.session_state.last_window_key != refresh_key:
        trader.open_trading_window()
        st.session_state.last_window_key = refresh_key

    # Stop-loss check — always fires, bypasses window lock
    sl_msg = trader.check_stop_loss(current_price)
    if sl_msg:
        st.markdown(f'<div class="sl-alert">{sl_msg}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 01 — Portfolio KPIs  (always visible)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-hdr"><span class="section-hdr-label">01 — Portfolio</span></div>',
            unsafe_allow_html=True)

portfolio = trader.status(current_price)
ret_pct   = portfolio["Total Return %"]
upnl      = portfolio["Unrealised P&L"]

st.markdown(
'<div class="kpi-strip">'
f'<div class="kpi-card c-blue"><div class="kpi-lbl">Portfolio Value</div>'
f'<div class="kpi-val">${portfolio["Portfolio Value"]:,.2f}</div>'
f'<div class="kpi-sub">Started $100,000</div></div>'
f'<div class="kpi-card c-green"><div class="kpi-lbl">Cash</div>'
f'<div class="kpi-val">${portfolio["Cash"]:,.2f}</div></div>'
f'<div class="kpi-card c-gold"><div class="kpi-lbl">Holdings</div>'
f'<div class="kpi-val">{portfolio["Holdings"]:.0f} sh</div>'
f'<div class="kpi-sub">Avg ${portfolio["Avg Cost"]:.2f}</div></div>'
f'<div class="kpi-card c-purple"><div class="kpi-lbl">Unrealised P&amp;L</div>'
f'<div class="kpi-val {"pos" if upnl>=0 else "neg"}">${upnl:+,.2f}</div></div>'
f'<div class="kpi-card {"c-green" if ret_pct>=0 else "c-red"}"><div class="kpi-lbl">Total Return</div>'
f'<div class="kpi-val {"pos" if ret_pct>=0 else "neg"}">{ret_pct:+.2f}%</div>'
f'<div class="kpi-sub">Realised ${portfolio["Realised P&L"]:+,.2f}</div></div>'
'</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 02 — Candlestick chart  (always visible)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-hdr"><span class="section-hdr-label">02 — Chart</span></div>',
            unsafe_allow_html=True)

# ── Gap-free chart slice ──────────────────────────────────────────────────────
if not df_chart.empty and is_live and today_bars > 0 and last_day_bars > 0:
    last_day_keep  = max(0, last_day_bars - today_bars)
    total_keep     = last_day_keep + today_bars
    df_chart_plot  = df_chart.tail(total_keep).copy()
elif not df_chart.empty:
    df_chart_plot = df_chart.copy()
else:
    df_chart_plot = df_chart.copy()

if not df_chart_plot.empty:
    df_chart_plot.index = df_chart_plot.index.strftime("%m/%d %H:%M")

if df_chart_plot.empty:
    st.markdown(
        '<div style="border:1px solid rgba(255,255,255,0.06);background:#090d12;'
        'padding:60px;text-align:center;font-family:DM Mono,monospace;'
        'font-size:11px;color:#3d4d60;letter-spacing:0.1em;">'
        'NO DATA AVAILABLE — check ticker symbol or network</div>',
        unsafe_allow_html=True,
    )
    fig = go.Figure()
else:
    fig = go.Figure(data=[go.Candlestick(
        x=df_chart_plot.index,
        open=df_chart_plot["Open"], high=df_chart_plot["High"],
        low=df_chart_plot["Low"],   close=df_chart_plot["Close"],
        increasing_line_color="#00ffaa", decreasing_line_color="#ff4d6d",
        increasing_fillcolor="rgba(0,255,170,0.15)",
        decreasing_fillcolor="rgba(255,77,109,0.15)",
        name=ticker,
    )])

# Trade markers + LSTM forecast (only when chart has data)
trades_df = trader.get_trade_dataframe()
if not df_chart_plot.empty:
    if is_live and not trades_df.empty:
        buys  = trades_df[trades_df["Action"] == "BUY"]
        sells = trades_df[trades_df["Action"] == "SELL"]

        def _snap_to_label(ts_series, index_labels):
            snapped = []
            for ts in pd.to_datetime(ts_series):
                label = ts.strftime("%m/%d %H:%M")
                snapped.append(label if label in index_labels else index_labels[-1])
            return snapped

        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=_snap_to_label(buys["Timestamp"], df_chart_plot.index.tolist()),
                y=buys["Price"],
                mode="markers", name="BUY",
                marker=dict(symbol="triangle-up", size=14, color="#00ffaa"),
            ))
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=_snap_to_label(sells["Timestamp"], df_chart_plot.index.tolist()),
                y=sells["Price"],
                mode="markers", name="SELL",
                marker=dict(symbol="triangle-down", size=14, color="#ff4d6d"),
            ))

    if is_live and ticker in st.session_state.pred_cache:
        pred = st.session_state.pred_cache[ticker]
        if pred.get("predicted_close"):
            last_label = df_chart_plot.index[-1]
            next_label = (
                pd.to_datetime(last_label, format="%m/%d %H:%M", errors="coerce")
                + pd.Timedelta(minutes=5)
            )
            next_label_str = next_label.strftime("%m/%d %H:%M") if not pd.isnull(next_label) else "Next"
            fig.add_trace(go.Scatter(
                x=[last_label, next_label_str],
                y=[pred["current_close"], pred["predicted_close"]],
                mode="lines+markers", name="LSTM Forecast",
                line=dict(color="#a855f7", width=2, dash="dot"),
                marker=dict(size=8, color="#a855f7"),
            ))

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono", color="#3d4d60", size=11),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.06)",
        rangeslider_visible=False,
        type="category",
        tickangle=-45,
        nticks=20,
    ),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)",
               linecolor="rgba(255,255,255,0.06)", side="right"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6b7a90")),
    hovermode="x unified",
    margin=dict(l=10, r=60, t=10, b=40),
    height=480,
)
st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LIVE-ONLY SECTIONS  (hidden entirely when market is closed)
# ══════════════════════════════════════════════════════════════════════════════
if is_live:

    # ── SECTION 03 — LSTM Signal ──────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">03 — LSTM Signal</span></div>',
                unsafe_allow_html=True)

    refresh_key = f"{ticker}_{today_bars}"
    if st.session_state.pred_cache.get("_key") != refresh_key:
        with st.spinner(f"Training LSTM … today {today_bars} bars + last-day {last_day_bars} bars"):
            pred = train_and_predict(df_train, ticker=ticker)
        st.session_state.pred_cache[ticker] = pred
        st.session_state.pred_cache["_key"] = refresh_key
    else:
        pred = st.session_state.pred_cache.get(ticker, {})

    sig_col, meta_col = st.columns([3, 2])

    with sig_col:
        st.markdown('<div class="signal-box">', unsafe_allow_html=True)
        if pred.get("error"):
            st.markdown(
                f'<div style="font-family:DM Mono,monospace;font-size:11px;color:var(--gold);">'
                f'⚠ {pred["error"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            sig     = pred["signal"]
            sig_cls = "buy" if "BUY" in sig else ("sell" if "SELL" in sig else "hold")
            st.markdown(
f'<div class="kpi-lbl">Next 5-min candle forecast</div>'
f'<div class="signal-val {sig_cls}">{sig}</div>'
f'<div class="signal-chg">'
f'Current&nbsp;${pred["current_close"]:.4f}&nbsp;→&nbsp;'
f'Predicted&nbsp;${pred["predicted_close"]:.4f}'
f'&nbsp;&nbsp;|&nbsp;&nbsp;Δ&nbsp;{pred["change_pct"]:+.4f}%'
f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with meta_col:
        if not pred.get("error"):
            st.markdown(
f'<div class="model-bar">'
f'<span class="ml">Trained on</span><span class="mv">{pred["trained_on"]} bars</span>'
f'<span>·</span>'
f'<span class="ml">Last-day bars</span><span class="mv">{last_day_bars}</span>'
f'<span>·</span>'
f'<span class="ml">Today bars</span><span class="mv">{today_bars}</span>'
f'<span>·</span>'
f'<span class="ml">Val RMSE</span><span class="mv">${pred["rmse"]:.4f}</span>'
f'<span>·</span>'
f'<span class="ml">Window</span><span class="mv">60 bars (5-min)</span>'
f'</div>',
                unsafe_allow_html=True,
            )
        labels = ["Cash", "Equity"]
        values = [portfolio["Cash"], portfolio["Holdings"] * current_price]
        fig2 = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=["#00c2ff", "#a855f7"], width=0.4,
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono", color="#3d4d60", size=11),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
            margin=dict(l=10, r=10, t=20, b=10), height=200,
            showlegend=False,
        )
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION 04 — Trade execution ──────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">04 — Trade Execution</span></div>',
                unsafe_allow_html=True)

    win_open, win_secs = trader.is_window_open()
    if win_open:
        st.markdown(
            f'<div class="window-open">🟢 TRADE WINDOW OPEN — {win_secs}s remaining'
            f'&nbsp;·&nbsp; Execute now at 1-min price · window closes in ~{win_secs}s</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="window-locked">🔒 TRADE WINDOW LOCKED'
            f'&nbsp;·&nbsp; Next window opens with the next 5-min bar'
            f'&nbsp;·&nbsp; ~{win_secs}s remaining in lockout</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="trade-panel">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="trade-lbl">Execute at current price &nbsp;'
        f'<span style="color:#fff;font-size:15px;">${current_price:.4f}</span>'
        f'&nbsp;·&nbsp; Qty</div>',
        unsafe_allow_html=True,
    )

    qty_col, buy_col, sell_col, reset_col = st.columns([2, 2, 2, 1])

    with qty_col:
        quantity = st.number_input("qty", min_value=1, max_value=500,
                                   value=1, step=1, label_visibility="collapsed")
    with buy_col:
        buy_disabled = not win_open
        if st.button("▲ BUY", key="buy_btn", disabled=buy_disabled):
            msg = trader.buy(current_price, quantity,
                             str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            st.session_state["trade_msg"] = msg
            st.rerun()
    with sell_col:
        sell_disabled = not win_open
        if st.button("▼ SELL", key="sell_btn", disabled=sell_disabled):
            msg = trader.sell(current_price, quantity,
                              str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            st.session_state["trade_msg"] = msg
            st.rerun()
    with reset_col:
        if st.button("↺ Reset", key="reset_btn"):
            trader.reset()
            st.session_state["trade_msg"]   = "Portfolio reset."
            st.session_state.pred_cache     = {}
            st.session_state.last_window_key = None
            st.rerun()

    if st.session_state.get("trade_msg"):
        msg   = st.session_state["trade_msg"]
        color = "var(--green)" if "✅" in msg else ("var(--gold)" if "🔒" in msg else "var(--red)")
        st.markdown(
            f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{color};'
            f'margin-top:12px;letter-spacing:0.08em;">{msg}</div>',
            unsafe_allow_html=True,
        )
        st.session_state["trade_msg"] = ""

    st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION 05 — Trade history ────────────────────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">05 — Trade History</span></div>',
                unsafe_allow_html=True)

    trades_df = trader.get_trade_dataframe()
    if trades_df.empty:
        st.markdown(
            '<div style="font-family:DM Mono,monospace;font-size:11px;color:var(--muted);">'
            'No trades yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        def _color_action(val):
            if val == "BUY":  return "color: #00ffaa"
            if val == "SELL": return "color: #ff4d6d"
            return ""

        styled = (
            trades_df.style
            .applymap(_color_action, subset=["Action"])
            .set_properties(**{
                "background-color": "#090d12",
                "color":            "#cdd5e0",
                "font-family":      "DM Mono, monospace",
                "font-size":        "12px",
            })
            .format({
                "Price":       "${:.4f}",
                "Cash":        "${:,.2f}",
                "RealisedPnL": "${:+,.2f}",
                "AvgCost":     "${:.4f}",
            })
        )
        st.dataframe(styled, use_container_width=True, height=280)

# ══════════════════════════════════════════════════════════════════════════════
# CLOSED — read-only trade history only (no controls, no prediction)
# ══════════════════════════════════════════════════════════════════════════════
else:
    trades_df = trader.get_trade_dataframe()
    if not trades_df.empty:
        st.markdown(
            '<div class="section-hdr"><span class="section-hdr-label">'
            '03 — Trade History (read-only)</span></div>',
            unsafe_allow_html=True,
        )

        def _color_action(val):
            if val == "BUY":  return "color: #00ffaa"
            if val == "SELL": return "color: #ff4d6d"
            return ""

        styled = (
            trades_df.style
            .applymap(_color_action, subset=["Action"])
            .set_properties(**{
                "background-color": "#090d12",
                "color":            "#cdd5e0",
                "font-family":      "DM Mono, monospace",
                "font-size":        "12px",
            })
            .format({
                "Price":       "${:.4f}",
                "Cash":        "${:,.2f}",
                "RealisedPnL": "${:+,.2f}",
                "AvgCost":     "${:.4f}",
            })
        )
        st.dataframe(styled, use_container_width=True, height=280)