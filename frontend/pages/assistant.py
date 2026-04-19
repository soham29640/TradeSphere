import streamlit as st
import google.generativeai as genai
import datetime, time

st.set_page_config(
    page_title="AI Assistant · Trade Sphere",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Gemini setup ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are an expert AI market intelligence assistant for TradeSphere — a platform with 4 AI modules:

1. **Price Predictor** — 3-layer LSTM on 5-min OHLCV bars, 60-bar window, 30-step horizon, auto-retrains every 24h
2. **Pattern Detector** — CNN/ResNet multi-label classifier for 20 classical chart patterns (224px input, sigmoid output, top-3 results)
3. **Volatility Forecast** — Ensemble of GARCH + LSTM + Attention-LSTM, forecasts next-day volatility, 75th percentile risk threshold
4. **Paper Trading** — LSTM-powered simulated trading with 5-min retrain, 1-min trade windows, live buy/sell signals

You have deep expertise in:
- Technical analysis and chart patterns (Head & Shoulders, Cup & Handle, Flags, Wedges, etc.)
- Quantitative finance (LSTM, GARCH, attention mechanisms, time-series forecasting)
- Risk management, position sizing, Kelly criterion
- Market microstructure, volatility regimes, options Greeks
- Backtesting, Sharpe ratio, drawdown analysis

Your personality: sharp, confident, data-driven. You give concrete, actionable answers. You reference the platform's specific tools when relevant. You never give financial advice but you educate deeply.

Keep responses concise but insightful. Use markdown formatting. When asked about platform features, be specific about the model architectures."""

TODAY = datetime.date.today().strftime("%B %d, %Y")

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

:root {
  --green:#00ffaa; --blue:#00c2ff; --red:#ff4d6d;
  --gold:#ffc145; --purple:#b56dff; --orange:#ff7b3d;
  --bg:#03060a; --bg2:#080d14; --bg3:#0d1520; --bg4:#111c2a;
  --border:rgba(255,255,255,0.07); --text:#c8d5e8;
  --muted:#3a4d62; --muted2:#5a6f85;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"]{
  background:var(--bg) !important;
  font-family:'Space Grotesk',sans-serif;color:var(--text);
}
[data-testid="stHeader"],footer,[data-testid="stToolbar"],
#MainMenu,[data-testid="stSidebarCollapsedControl"]{display:none !important;}
[data-testid="stMainBlockContainer"]{padding:0 !important;max-width:100% !important;}
section.main>div{padding:0 !important;}
[data-testid="stVerticalBlock"]{gap:0 !important;}

.bg-grid{
  position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:
    linear-gradient(rgba(0,255,170,0.02) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,170,0.02) 1px,transparent 1px);
  background-size:80px 80px;animation:gridPan 25s linear infinite;
}
@keyframes gridPan{to{background-position:80px 80px;}}
.orb{position:fixed;border-radius:50%;filter:blur(130px);pointer-events:none;z-index:0;}
.orb-1{width:500px;height:500px;top:-100px;right:-100px;background:rgba(0,255,170,0.05);}
.orb-2{width:400px;height:400px;bottom:-80px;left:-80px;background:rgba(181,109,255,0.04);}

/* ── Nav ── */
.nav{
  position:relative;z-index:20;
  display:flex;justify-content:space-between;align-items:center;
  padding:18px 56px;border-bottom:1px solid var(--border);
  background:rgba(3,6,10,0.85);backdrop-filter:blur(20px);
}
.nav-logo{font-family:'Syne',sans-serif;font-size:16px;font-weight:800;
  letter-spacing:.06em;color:#fff;text-transform:uppercase;}
.nav-logo span{color:var(--green);}
.nav-right{display:flex;align-items:center;gap:16px;}
.nav-status{
  display:flex;align-items:center;gap:7px;
  font-family:'JetBrains Mono',monospace;font-size:9px;
  letter-spacing:.12em;color:var(--green);text-transform:uppercase;
}
.pulse-dot{width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:pulse 2s infinite;}
@keyframes pulse{
  0%,100%{box-shadow:0 0 0 0 rgba(0,255,170,.5);}
  70%{box-shadow:0 0 0 8px rgba(0,255,170,0);}
}

/* ── Layout ── */
.chat-layout{
  position:relative;z-index:5;
  display:grid;grid-template-columns:280px 1fr;
  height:calc(100vh - 61px);
}

/* ── Sidebar ── */
.chat-sidebar{
  background:var(--bg2);border-right:1px solid var(--border);
  padding:28px 24px;overflow-y:auto;
}
.sidebar-title{
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--muted);margin-bottom:20px;padding-bottom:12px;
  border-bottom:1px solid var(--border);
}
.sidebar-section{margin-bottom:28px;}
.sidebar-section-title{
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.15em;
  text-transform:uppercase;color:var(--muted);margin-bottom:12px;
}
.suggest-btn{
  display:block;width:100%;text-align:left;
  font-family:'Space Grotesk',sans-serif;font-size:12px;
  color:var(--muted2);padding:10px 14px;margin-bottom:6px;
  border:1px solid var(--border);border-radius:2px;
  background:rgba(255,255,255,.02);cursor:pointer;
  transition:all .2s;line-height:1.5;
}
.suggest-btn:hover{
  color:var(--text);background:rgba(0,255,170,.04);
  border-color:rgba(0,255,170,.2);
}
.stat-row{
  display:flex;justify-content:space-between;align-items:center;
  padding:8px 0;border-bottom:1px solid var(--border);font-size:12px;
}
.stat-row:last-child{border-bottom:none;}
.stat-key{color:var(--muted2);}
.stat-val-g{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--green);}
.stat-val-w{font-family:'JetBrains Mono',monospace;font-size:11px;color:#fff;}

/* ── Chat area ── */
.chat-main{display:flex;flex-direction:column;overflow:hidden;}
.chat-messages{flex:1;overflow-y:auto;padding:32px 40px;display:flex;flex-direction:column;gap:24px;}
.chat-messages::-webkit-scrollbar{width:4px;}
.chat-messages::-webkit-scrollbar-track{background:transparent;}
.chat-messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}

/* ── Messages ── */
.msg{display:flex;gap:14px;align-items:flex-start;animation:msgIn .3s ease both;}
@keyframes msgIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.msg.user{flex-direction:row-reverse;}
.msg-avatar{
  width:34px;height:34px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:700;
}
.avatar-ai{
  background:linear-gradient(135deg,rgba(0,255,170,.15),rgba(0,194,255,.1));
  border:1px solid rgba(0,255,170,.3);color:var(--green);
  font-family:'JetBrains Mono',monospace;font-size:11px;
}
.avatar-user{
  background:rgba(181,109,255,.12);border:1px solid rgba(181,109,255,.25);
  color:var(--purple);font-family:'JetBrains Mono',monospace;font-size:10px;
}
.msg-bubble{
  max-width:680px;padding:16px 20px;border-radius:2px;
  font-size:13.5px;line-height:1.75;
}
.bubble-ai{
  background:var(--bg2);border:1px solid var(--border);color:var(--text);
  border-top-left-radius:0;
}
.bubble-user{
  background:rgba(181,109,255,.08);border:1px solid rgba(181,109,255,.18);
  color:var(--text);border-top-right-radius:0;
}
.msg-time{
  font-family:'JetBrains Mono',monospace;font-size:8px;
  color:var(--muted);margin-top:6px;letter-spacing:.08em;
}
.msg.user .msg-time{text-align:right;}

/* markdown inside bubbles */
.bubble-ai h1,.bubble-ai h2,.bubble-ai h3{
  font-family:'Syne',sans-serif;color:#fff;margin:12px 0 6px;
}
.bubble-ai strong{color:#fff;}
.bubble-ai code{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  background:rgba(0,255,170,.08);color:var(--green);
  padding:1px 5px;border-radius:2px;
}
.bubble-ai ul,.bubble-ai ol{padding-left:18px;margin:8px 0;}
.bubble-ai li{margin-bottom:4px;}
.bubble-ai hr{border:none;border-top:1px solid var(--border);margin:12px 0;}

/* ── Typing indicator ── */
.typing{display:flex;gap:5px;padding:6px 0;align-items:center;}
.typing span{
  width:6px;height:6px;border-radius:50%;background:var(--green);opacity:.4;
  animation:typingBounce .8s ease-in-out infinite;
}
.typing span:nth-child(2){animation-delay:.15s;}
.typing span:nth-child(3){animation-delay:.3s;}
@keyframes typingBounce{0%,80%,100%{transform:scale(1);opacity:.4;}40%{transform:scale(1.3);opacity:1;}}

/* ── Input area ── */
.chat-input-wrap{
  padding:20px 40px 28px;border-top:1px solid var(--border);
  background:rgba(3,6,10,.6);backdrop-filter:blur(10px);
}
[data-testid="stChatInput"]{
  background:var(--bg2) !important;border:1px solid var(--border2) !important;
  border-radius:2px !important;color:var(--text) !important;
  font-family:'Space Grotesk',sans-serif !important;
}
[data-testid="stChatInput"]:focus-within{
  border-color:rgba(0,255,170,.35) !important;
  box-shadow:0 0 20px rgba(0,255,170,.08) !important;
}
.input-hint{
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.12em;
  color:var(--muted);text-transform:uppercase;margin-top:8px;text-align:center;
}

/* ── Empty state ── */
.empty-state{
  flex:1;display:flex;flex-direction:column;
  align-items:center;justify-content:center;padding:60px 40px;text-align:center;
}
.empty-icon{
  font-size:48px;margin-bottom:24px;
  animation:floatIcon 4s ease-in-out infinite alternate;
}
@keyframes floatIcon{from{transform:translateY(0);}to{transform:translateY(-12px);}}
.empty-title{
  font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
  color:#fff;margin-bottom:10px;
}
.empty-title span{color:var(--green);}
.empty-sub{font-size:13px;color:var(--muted2);max-width:380px;line-height:1.7;}
.quick-prompts{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:28px;}
.qprompt{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.1em;
  padding:8px 16px;border:1px solid var(--border);border-radius:2px;
  color:var(--muted2);background:rgba(255,255,255,.02);
  cursor:pointer;transition:all .2s;text-transform:uppercase;
}
.qprompt:hover{color:var(--green);border-color:rgba(0,255,170,.25);background:rgba(0,255,170,.04);}

/* Streamlit tweaks */
div[data-testid="stButton"]>button{
  background:rgba(255,255,255,.03) !important;
  border:1px solid var(--border) !important;
  color:var(--muted2) !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:9px !important;letter-spacing:.12em !important;
  padding:8px 16px !important;border-radius:2px !important;
  text-transform:uppercase !important;transition:all .2s !important;
}
div[data-testid="stButton"]>button:hover{
  color:var(--green) !important;
  border-color:rgba(0,255,170,.25) !important;
  background:rgba(0,255,170,.04) !important;
}
</style>

<div class="bg-grid"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="nav">
  <div class="nav-logo">Trade<span>Sphere</span> &nbsp;<span style="color:var(--muted);font-size:12px;font-weight:300;">/ AI Assistant</span></div>
  <div class="nav-right">
    <div class="nav-status"><div class="pulse-dot"></div>GEMINI 1.5 FLASH · ONLINE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0

# ── Layout: sidebar + chat ─────────────────────────────────────────────────────
sidebar_col, main_col = st.columns([1, 3.2], gap="small")

SUGGESTIONS = [
    ("Patterns", [
        "Explain the Head & Shoulders pattern",
        "When does a bull flag fail?",
        "How does the CNN detect double tops?",
    ]),
    ("LSTM & Models", [
        "How does the 3-layer LSTM work?",
        "What is the 60-bar window for?",
        "Explain GARCH vs Attention-LSTM",
    ]),
    ("Trading Strategy", [
        "Best risk/reward for breakouts?",
        "How do I size a paper trade?",
        "What is the 75th percentile threshold?",
    ]),
]

with sidebar_col:
    st.markdown("""<div class="chat-sidebar">
    <div class="sidebar-title">✦ TRADESPHERE ASSISTANT</div>
    """, unsafe_allow_html=True)

    # Back button
    if st.button("← Back to Home", key="back_home_asst"):
        st.switch_page("home.py")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    for section, prompts in SUGGESTIONS:
        st.markdown(f'<div class="sidebar-section-title">{section}</div>', unsafe_allow_html=True)
        for p in prompts:
            if st.button(p, key=f"sug_{p[:20]}"):
                st.session_state.messages.append({"role": "user", "content": p})
                st.session_state._pending_prompt = p
                st.rerun()

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">SESSION STATS</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-row"><span class="stat-key">Messages</span><span class="stat-val-w">{st.session_state.msg_count}</span></div>
    <div class="stat-row"><span class="stat-key">Model</span><span class="stat-val-g">Gemini 1.5</span></div>
    <div class="stat-row"><span class="stat-key">Date</span><span class="stat-val-w">{TODAY}</span></div>
    """, unsafe_allow_html=True)

    if st.button("🗑 Clear Chat", key="clear_chat"):
        st.session_state.messages = []
        st.session_state.msg_count = 0
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    # ── No API key warning ─────────────────────────────────────────────────────
    if not GEMINI_API_KEY:
        st.warning("⚠️ Add `GEMINI_API_KEY` to `.streamlit/secrets.toml` to enable the AI assistant.")

    # ── Message history ────────────────────────────────────────────────────────
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div class="empty-state">
              <div class="empty-icon">✦</div>
              <div class="empty-title">Ask me <span>anything</span></div>
              <p class="empty-sub">I'm your AI market intelligence assistant. Ask about chart patterns, model architectures, trading strategies, or how to use TradeSphere's tools.</p>
              <div class="quick-prompts">
                <div class="qprompt">How does LSTM predict prices?</div>
                <div class="qprompt">What is a cup and handle?</div>
                <div class="qprompt">Explain volatility regimes</div>
                <div class="qprompt">Best entry signals?</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                role = msg["role"]
                content = msg["content"]
                ts = msg.get("time", "")

                if role == "user":
                    st.markdown(f"""
                    <div class="msg user">
                      <div class="avatar-msg" style="display:flex;flex-direction:column;align-items:flex-end;">
                        <div class="msg-bubble bubble-user">{content}</div>
                        <div class="msg-time">{ts}</div>
                      </div>
                      <div class="msg-avatar avatar-user">YOU</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Render assistant markdown properly
                    st.markdown(f"""
                    <div class="msg">
                      <div class="msg-avatar avatar-ai">AI</div>
                      <div style="display:flex;flex-direction:column;">
                    """, unsafe_allow_html=True)
                    with st.container():
                        st.markdown(content)
                    st.markdown(f"""
                        <div class="msg-time">{ts} · Gemini 1.5 Flash</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Chat input ─────────────────────────────────────────────────────────────
    st.markdown('<div class="chat-input-wrap">', unsafe_allow_html=True)
    prompt = st.chat_input("Ask about markets, patterns, models, strategies...", key="chat_input")
    st.markdown('<div class="input-hint">Powered by Gemini 1.5 Flash · TradeSphere AI</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle pending prompt from sidebar buttons
    pending = st.session_state.pop("_pending_prompt", None)
    if pending:
        prompt = pending

    # ── Generate response ──────────────────────────────────────────────────────
    if prompt and GEMINI_API_KEY:
        now = datetime.datetime.now().strftime("%H:%M")

        # Add user message
        if not st.session_state.messages or st.session_state.messages[-1]["content"] != prompt:
            st.session_state.messages.append({"role": "user", "content": prompt, "time": now})

        st.session_state.msg_count += 1

        # Build Gemini conversation history
        history = []
        for m in st.session_state.messages[:-1]:
            gemini_role = "user" if m["role"] == "user" else "model"
            history.append({"role": gemini_role, "parts": [m["content"]]})

        try:
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            chat = model.start_chat(history=history)

            with st.spinner(""):
                st.markdown("""
                <div class="msg" style="margin-bottom:8px;">
                  <div class="msg-avatar avatar-ai">AI</div>
                  <div class="msg-bubble bubble-ai">
                    <div class="typing"><span></span><span></span><span></span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                response = chat.send_message(prompt)
                reply = response.text

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "time": datetime.datetime.now().strftime("%H:%M")
            })
            st.rerun()

        except Exception as e:
            st.error(f"Gemini error: {e}")

    elif prompt and not GEMINI_API_KEY:
        st.error("Please add your `GEMINI_API_KEY` to `.streamlit/secrets.toml`")