"""
frontend/pages/agent.py  –  Live Trading Agent page
─────────────────────────────────────────────────────
Part of the Trade Sphere multi-page app.
Reached via home.py → "→ TRADE" button.

Import paths updated for new project structure:
    backend/agent/trading_agent.py   (was src/agents/trading_agent.py)
    models/agent/LSTM_model.ptl      (was models/LSTM_model.ptl)
    models/agent/standard_scaler.pkl (was models/standard_scaler.pkl)
"""

import os
import sys
import threading
import time
from datetime import datetime
from queue import Empty, Queue

import streamlit as st

# ── Make backend importable from frontend/pages/ ──────────────────────────────
# __file__ = frontend/pages/agent.py  →  go up 2 levels to project root
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_LOG_LINES    = 500
DISPLAY_LINES    = 40
REFRESH_INTERVAL = 1.0


# ── Session-state initialisation ─────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "ag_running":    False,
        "ag_logs":       [],
        "ag_log_queue":  Queue(),
        "ag_stop_event": None,
        "ag_api_key":    "",
        "ag_api_secret": "",
        "ag_base_url":   "https://paper-api.alpaca.markets",
        "ag_keys_saved": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# ── Background thread ─────────────────────────────────────────────────────────
def run_agent(
    ticker: str,
    qty: int,
    interval: int,
    stop_event: threading.Event,
    log_q: Queue,
) -> None:
    """Runs in a daemon thread; pushes log dicts onto log_q."""
    # Import here so path injection above is in effect
    from backend.agent.trading_agent import TradingAgent

    def push(msg: str) -> None:
        log_q.put({"type": "log", "msg": msg})

    push(f"🚀  Agent started for {ticker} (qty={qty}, interval={interval}s)")

    try:
        agent = TradingAgent(ticker)

        while not stop_event.is_set():
            now = datetime.now().strftime("%H:%M:%S")
            try:
                action, current, predicted = agent.act(qty=qty)
                if current is not None and predicted is not None:
                    msg = f"[{now}] {action} | ${current:.2f} → ${predicted:.2f}"
                else:
                    msg = f"[{now}] {action}"
            except Exception as exc:
                msg = f"[{now}] ❌ {exc}"

            push(msg)

            deadline = time.monotonic() + interval
            while time.monotonic() < deadline and not stop_event.is_set():
                time.sleep(0.25)

    except Exception as exc:
        push(f"💥 Fatal thread error: {exc}")
    finally:
        push("🛑  Agent thread exited.")


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Alpaca Paper Trading Agent · Trade Sphere", layout="wide", page_icon="💹")

# ── Inline CSS (matches Trade Sphere dark theme) ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');
:root {
  --green:#00ffaa; --orange:#ff7b3d; --red:#ff4d6d;
  --bg:#03060a; --bg2:#080d14; --bg3:#0d1520;
  --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
  --text:#c8d5e8; --muted:#3a4d62; --muted2:#5a6f85;
}
html, body, [data-testid="stAppViewContainer"] {
  background:var(--bg) !important;
  font-family:'Space Grotesk',sans-serif; color:var(--text);
}
[data-testid="stHeader"], footer, #MainMenu { display:none !important; }
[data-testid="stMainBlockContainer"] { padding:32px 48px !important; max-width:100% !important; }

/* back button */
.back-btn {
  display:inline-flex; align-items:center; gap:8px;
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.15em;
  color:var(--muted2); text-transform:uppercase; cursor:pointer;
  border:1px solid var(--border); padding:6px 14px; border-radius:2px;
  background:var(--bg2); margin-bottom:24px; text-decoration:none;
  transition:all .2s;
}
.back-btn:hover { color:var(--green); border-color:rgba(0,255,170,.3); }

/* page header */
.page-header { margin-bottom:32px; }
.page-header .eyebrow {
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.22em;
  color:var(--orange); text-transform:uppercase; margin-bottom:10px;
}
.page-header h1 {
  font-family:'Syne',sans-serif; font-size:36px; font-weight:800;
  color:#fff; letter-spacing:-.01em; margin:0;
}
.page-header h1 span { color:var(--orange); }

/* credential card */
.cred-card {
  background:var(--bg2); border:1px solid var(--border);
  border-top:2px solid var(--orange); padding:24px 28px; margin-bottom:28px;
}
.cred-title {
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.18em;
  color:var(--orange); text-transform:uppercase; margin-bottom:16px;
}

/* status pill */
.status-pill {
  display:inline-flex; align-items:center; gap:7px;
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.12em;
  padding:5px 14px; border-radius:2px; text-transform:uppercase;
}
.status-running { background:rgba(0,255,170,.08); border:1px solid rgba(0,255,170,.3); color:var(--green); }
.status-stopped { background:rgba(255,123,61,.08); border:1px solid rgba(255,123,61,.3); color:var(--orange); }
.live-dot { width:7px; height:7px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(0,255,170,.5);} 70%{box-shadow:0 0 0 9px rgba(0,255,170,0);} }

/* terminal */
.terminal-label {
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.2em;
  color:var(--muted2); text-transform:uppercase; margin-bottom:10px;
}

/* streamlit overrides */
div[data-testid="stCode"] {
  background:var(--bg2) !important; border:1px solid var(--border) !important;
  border-radius:0 !important; font-family:'JetBrains Mono',monospace !important;
  font-size:11px !important;
}
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
  background:var(--bg3) !important; border:1px solid var(--border2) !important;
  border-radius:2px !important; color:#fff !important;
  font-family:'JetBrains Mono',monospace !important; font-size:12px !important;
}
div[data-testid="stSelectbox"] > div { background:var(--bg3) !important; border-radius:2px !important; }
</style>
""", unsafe_allow_html=True)

# ── Back button ───────────────────────────────────────────────────────────────
if st.button("← Back to Home", key="back_home"):
    st.switch_page("home.py")

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="eyebrow">04/06 &nbsp;·&nbsp; Module</div>
  <h1>Alpaca <span>Paper Trading Agent</span></h1>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CREDENTIALS SECTION
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="cred-card"><div class="cred-title">🔑 Alpaca Credentials</div></div>', unsafe_allow_html=True)

with st.expander("🔑 Enter Alpaca API Keys", expanded=not st.session_state.ag_keys_saved):
    st.caption("Get your free keys from [alpaca.markets](https://alpaca.markets) → Paper Trading dashboard.")

    c1, c2 = st.columns(2)
    api_key    = c1.text_input("API Key ID",     value=st.session_state.ag_api_key,
                                placeholder="PKXXXXXXXXXXXXXXXX",
                                disabled=st.session_state.ag_running)
    api_secret = c2.text_input("API Secret Key", value=st.session_state.ag_api_secret,
                                placeholder="your secret key",
                                type="password",
                                disabled=st.session_state.ag_running)

    mode = st.radio(
        "Trading Mode",
        ["📄 Paper (safe)", "💰 Live (real money)"],
        horizontal=True,
        disabled=st.session_state.ag_running,
    )
    base_url = (
        "https://paper-api.alpaca.markets"
        if "Paper" in mode
        else "https://api.alpaca.markets"
    )

    if st.button("💾 Save Credentials", disabled=st.session_state.ag_running, use_container_width=True):
        if not api_key.strip() or not api_secret.strip():
            st.error("Both API Key and Secret are required.")
        else:
            os.environ["APCA_API_KEY_ID"]    = api_key.strip()
            os.environ["APCA_API_SECRET_KEY"] = api_secret.strip()
            os.environ["APCA_API_BASE_URL"]   = base_url

            st.session_state.ag_api_key    = api_key.strip()
            st.session_state.ag_api_secret = api_secret.strip()
            st.session_state.ag_base_url   = base_url
            st.session_state.ag_keys_saved = True
            st.success("✅ Credentials saved!")
            st.rerun()

# Credential status
if st.session_state.ag_keys_saved:
    masked = st.session_state.ag_api_key[:4] + "••••••••" + st.session_state.ag_api_key[-4:]
    mode_label = "Paper" if "paper" in st.session_state.ag_base_url else "Live"
    st.success(f"🟢 Credentials ready &nbsp;|&nbsp; Key: `{masked}` &nbsp;|&nbsp; Mode: `{mode_label}`")
else:
    st.warning("⬆️ Enter and save your Alpaca credentials above before starting the bot.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TRADING CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

# Status
running = st.session_state.ag_running
if running:
    st.markdown('<div class="status-pill status-running"><div class="live-dot"></div>Agent Running</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-pill status-stopped">● Agent Stopped</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
ticker   = col1.text_input("Ticker",         "AAPL",        disabled=running)
qty      = col2.number_input("Qty",          1, 100, 5,     disabled=running)
interval = col3.selectbox("Interval (sec)",  [30, 60, 120], disabled=running)

btn1, btn2 = st.columns(2)

start_disabled = running or not st.session_state.ag_keys_saved
if btn1.button("▶️  Start Agent", disabled=start_disabled, use_container_width=True):
    os.environ["APCA_API_KEY_ID"]    = st.session_state.ag_api_key
    os.environ["APCA_API_SECRET_KEY"] = st.session_state.ag_api_secret
    os.environ["APCA_API_BASE_URL"]   = st.session_state.ag_base_url

    stop_event = threading.Event()
    thread = threading.Thread(
        target=run_agent,
        args=(ticker, int(qty), int(interval), stop_event, st.session_state.ag_log_queue),
        daemon=True,
    )
    thread.start()
    st.session_state.ag_running    = True
    st.session_state.ag_stop_event = stop_event
    st.session_state.ag_logs       = []
    st.rerun()

if btn2.button("⏹  Stop Agent", disabled=not running, use_container_width=True):
    if st.session_state.ag_stop_event:
        st.session_state.ag_stop_event.set()
    st.session_state.ag_running = False
    st.rerun()

st.divider()

# ── Drain log queue ───────────────────────────────────────────────────────────
try:
    while True:
        item = st.session_state.ag_log_queue.get_nowait()
        if item.get("type") == "log":
            st.session_state.ag_logs.append(item["msg"])
except Empty:
    pass

if len(st.session_state.ag_logs) > MAX_LOG_LINES:
    st.session_state.ag_logs = st.session_state.ag_logs[-MAX_LOG_LINES:]

# ── Live terminal ─────────────────────────────────────────────────────────────
st.markdown('<div class="terminal-label">🖥 &nbsp;Live Terminal</div>', unsafe_allow_html=True)
if st.session_state.ag_logs:
    st.code("\n".join(st.session_state.ag_logs[-DISPLAY_LINES:]), language="")
else:
    st.info("No logs yet. Save credentials and press ▶️ Start Agent to begin.")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if st.session_state.ag_running:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()