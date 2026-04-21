import streamlit as st
import random, time

st.set_page_config(
    page_title="Trade Sphere",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
# ── CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

TICKER_DATA = [
    ("AAPL",  189.42), ("TSLA",  241.87), ("MSFT",  412.65),
    ("NVDA",  875.30), ("AMZN",  184.22), ("GOOG",  162.91),
    ("META",  504.17), ("SPY",   521.44), ("BTC",  67842.00),
    ("ETH",  3541.00), ("GOLD", 2318.00), ("QQQ",   448.21),
    ("AMD",   156.78), ("NFLX",  628.55), ("CRM",   289.11),
]

MODULE_DATA = [
    {
        "cls":        "mc-price",
        "num":        "01/06",
        "status":     "ACTIVE",
        "icon":       "📈",
        "title":      "Price Predictor",
        "desc":       "3-layer LSTM on 5-min OHLCV bars. Multi-step forecasts with live Yahoo Finance data.",
        "kpis":       [("60", "Win"), ("30", "Hor"), ("5m", "Bar")],
        "tags":       ["LSTM", "BATCH NORM", "LIVE DATA"],
        "spark_seed": 101,
        "spark_up":   True,
        "bgnum":      "01",
        "btn_lbl":    "→ LAUNCH",
        "btn_key":    "price_btn",
        "page":       "pages/price_app.py",
    },
    {
        "cls":        "mc-pattern",
        "num":        "02/06",
        "status":     "ACTIVE",
        "icon":       "🔍",
        "title":      "Pattern Detector",
        "desc":       "CNN multi-label classifier for 20 classical chart patterns. Upload image, get confidence scores.",
        "kpis":       [("20", "Pat"), ("224", "px"), ("TOP3", "Out")],
        "tags":       ["CNN", "RESNET", "UPLOAD"],
        "spark_seed": 202,
        "spark_up":   False,
        "bgnum":      "02",
        "btn_lbl":    "→ DETECT",
        "btn_key":    "pattern_btn",
        "page":       "pages/pattern_app.py",
    },
    {
        "cls":        "mc-vol",
        "num":        "03/06",
        "status":     "ACTIVE",
        "icon":       "🌊",
        "title":      "Volatility Forecast",
        "desc":       "GARCH + LSTM + Attention ensemble. Next-day vol forecast with 75th-percentile risk classification.",
        "kpis":       [("3", "Mdl"), ("75%", "Thr"), ("1D", "Hor")],
        "tags":       ["GARCH", "ATTENTION", "RISK"],
        "spark_seed": 303,
        "spark_up":   True,
        "bgnum":      "03",
        "btn_lbl":    "→ FORECAST",
        "btn_key":    "vol_btn",
        "page":       "pages/volatility_app.py",
    },
    {
        "cls":        "mc-paper",
        "num":        "04/06",
        "status":     "LIVE",
        "icon":       "💹",
        "title":      "Smart Paper Trading",
        "desc":       "Real-time simulated trading via LSTM predictions. 5-min retraining, live buy/sell signals.",
        "kpis":       [("5m", "Rfr"), ("1m", "Win"), ("SIM", "Mod")],
        "tags":       ["LSTM", "REAL-TIME", "AUTO-TRAIN"],
        "spark_seed": 404,
        "spark_up":   True,
        "bgnum":      "04",
        "btn_lbl":    "→ TRADE",
        "btn_key":    "paper_btn",
        "page":       "pages/paper_app.py",
    },
    {
        "cls":        "mc-quest",
        "num":        "05/06",
        "status":     "AI · GEMINI",
        "icon":       "✦",
        "title":      "Daily Quests",
        "desc":       "10 AI-generated MCQ trading challenges daily. Answer, score, earn XP and build your streak.",
        "kpis":       [("10", "Qs"), ("500", "XP"), ("🔥", "Str")],
        "tags":       ["GEMINI", "MCQ", "GAMIFIED"],
        "spark_seed": 505,
        "spark_up":   True,
        "bgnum":      "05",
        "btn_lbl":    "→ QUESTS",
        "btn_key":    "quest_btn",
        "page":       "pages/daily_quest.py",
    },
    {
        "cls":        "mc-agent",
        "num":        "06/06",
        "status":     "ALPACA",
        "icon":       "🤖",
        "title":      "Trading Agent",
        "desc":       "Alpaca-powered autonomous paper trading agent. LSTM signals, live execution, real-time terminal logs.",
        "kpis":       [("AUTO", "Exe"), ("30s", "Int"), ("PAP", "Mod")],
        "tags":       ["ALPACA", "AUTONOMOUS", "LIVE-LOG"],
        "spark_seed": 606,
        "spark_up":   True,
        "bgnum":      "06",
        "btn_lbl":    "→ AGENT",
        "btn_key":    "agent_btn",
        "page":       "pages/agent_app.py",
    },
]

STATS_BAR_DATA = [
    ("6",    "AI Modules"),
    ("20",   "Chart Patterns"),
    ("5M",   "Bar Resolution"),
    ("LSTM", "Price Model"),
    ("CNN",  "Pattern Model"),
    ("GARCH","Vol Model"),
    ("24H",  "Retrain Cycle"),
    ("∞",    "Paper Trades"),
    ("820",  "Daily XP"),
    ("AUTO", "Agent Trades"),
]

NAV_LINKS  = ["Markets", "Models", "Research", "Docs"]
NAV_CTA    = "→ OPEN PLATFORM"
HERO_TITLE = ("MARKETS,", "DECODED.")
HERO_SUB   = (
    "Six AI-powered modules. One unified platform. Predict prices, detect chart "
    "patterns, forecast volatility, simulate live paper trading, complete daily "
    "AI quests, and run an autonomous trading agent — all in real-time."
)
HERO_BADGES = [
    ("hb-live", '<div class="live-dot"></div>LIVE DATA · DAILY REFRESH'),
    ("hb-ai",   '⬡ &nbsp;<span class="num-highlight">6</span> AI MODELS ACTIVE'),
    ("hb-rt",   "◈ &nbsp;REAL-TIME EXECUTION"),
]

# ══════════════════════════════════════════════════════════════════════════════
# ── HELPERS
# ══════════════════════════════════════════════════════════════════════════════

rng = random.Random(int(time.time() // 60))

def _chg():
    v    = rng.uniform(-4.5, 5.5)
    sign = "▲" if v >= 0 else "▼"
    cls  = "up"  if v >= 0 else "dn"
    return sign, cls, abs(v)

def ticker_html():
    items = ""
    for sym, base in TICKER_DATA:
        s, c, pct = _chg()
        price = base * (1 + rng.uniform(-0.03, 0.03))
        fmt   = f"${price:,.2f}" if base < 10_000 else f"${price:,.0f}"
        items += (
            f'<div class="ticker-item">'
            f'<span class="sym">{sym}</span>'
            f'<span class="val">{fmt}</span>'
            f'<span class="{c}">{s} {pct:.2f}%</span>'
            f'</div>'
        )
    return items * 2

def sparkline_svg(seed, up=True):
    r2  = random.Random(seed)
    pts = []
    y   = 30
    for i in range(30):
        y += r2.uniform(-4, 4.5) * (1 if up else -1)
        y  = max(5, min(45, y))
        pts.append((i * (200 / 29), y))
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = path + f" L {pts[-1][0]:.1f},50 L 0,50 Z"
    return (
        f'<svg viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">'
        f'<path d="{area}" fill="rgba(255,255,255,0.03)"/>'
        f'<path d="{path}" fill="none" class="spark-path" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )

def module_card_html(m):
    kpis_html = "".join(
        f'<div class="mc-kpi"><div class="mc-kpi-val">{v}</div><div class="mc-kpi-lbl">{l}</div></div>'
        for v, l in m["kpis"]
    )
    tags_html = "".join(f'<span class="mc-tag">{t}</span>' for t in m["tags"])
    spark     = sparkline_svg(m["spark_seed"], m["spark_up"])
    return (
        f'<div class="mc {m["cls"]}">'
        f'<div class="mc-scan"></div>'
        f'<div class="mc-num">{m["num"]} <span class="mc-status">{m["status"]}</span></div>'
        f'<div class="mc-icon">{m["icon"]}</div>'
        f'<div class="mc-title">{m["title"]}</div>'
        f'<p class="mc-desc">{m["desc"]}</p>'
        f'<div class="sparkline">{spark}</div>'
        f'<div class="mc-kpis">{kpis_html}</div>'
        f'<div class="mc-tags">{tags_html}</div>'
        f'<div class="mc-bgnum">{m["bgnum"]}</div>'
        f'</div>'
    )

# ══════════════════════════════════════════════════════════════════════════════
# ── CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

:root {
  --green:  #00ffaa; --blue:   #00c2ff; --red:    #ff4d6d;
  --gold:   #ffc145; --purple: #b56dff; --cyan:   #00e5ff;
  --orange: #ff7b3d; --teal:   #00d4c8;
  --bg:  #03060a; --bg2: #080d14; --bg3: #0d1520; --bg4: #111c2a;
  --border: rgba(255,255,255,0.07); --border2: rgba(255,255,255,0.12);
  --text: #c8d5e8; --muted: #3a4d62; --muted2: #5a6f85;
}

*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Space Grotesk', sans-serif;
  color: var(--text);
}
[data-testid="stHeader"], footer,
[data-testid="stToolbar"], #MainMenu,
[data-testid="stSidebarCollapsedControl"] { display:none !important; }
[data-testid="stMainBlockContainer"] { padding:0 !important; max-width:100% !important; }
section.main > div { padding:0 !important; }
[data-testid="stVerticalBlock"] { gap:0 !important; }

/* grid bg */
.bg-grid {
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(0,255,170,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,170,0.025) 1px, transparent 1px);
  background-size:80px 80px;
  animation: gridPan 25s linear infinite;
}
@keyframes gridPan { to { background-position:80px 80px; } }

/* orbs */
.orb { position:fixed; border-radius:50%; filter:blur(130px); pointer-events:none; z-index:0; animation:orbDrift 10s ease-in-out infinite alternate; }
.orb-1 { width:700px; height:700px; top:-200px; left:-200px; background:rgba(0,255,170,0.06); }
.orb-2 { width:500px; height:500px; top:40%; right:-150px; background:rgba(0,194,255,0.05); animation-delay:-4s; }
.orb-3 { width:450px; height:450px; bottom:-100px; left:35%; background:rgba(181,109,255,0.045); animation-delay:-7s; }
.orb-4 { width:300px; height:300px; top:60%; left:10%; background:rgba(255,123,61,0.03); animation-delay:-2s; }
.orb-5 { width:280px; height:280px; top:20%; left:60%; background:rgba(0,212,200,0.03); animation-delay:-5s; }
@keyframes orbDrift { from { transform:translateY(0) scale(1); } to { transform:translateY(-50px) scale(1.06); } }

/* ticker */
.ticker-wrap {
  position:relative; z-index:10;
  background:linear-gradient(135deg, var(--bg2) 0%, rgba(8,13,20,0.95) 100%);
  border-bottom:1px solid var(--border);
  overflow:hidden; height:44px; display:flex; align-items:center;
}
.ticker-wrap::before, .ticker-wrap::after {
  content:''; position:absolute; top:0; bottom:0; width:80px; z-index:2;
}
.ticker-wrap::before { left:0;  background:linear-gradient(90deg,  var(--bg2), transparent); }
.ticker-wrap::after  { right:0; background:linear-gradient(-90deg, var(--bg2), transparent); }
.ticker-track { display:flex; animation:ticker 55s linear infinite; width:max-content; }
.ticker-item  { display:inline-flex; align-items:center; gap:10px; padding:0 32px; font-family:'JetBrains Mono',monospace; font-size:11px; border-right:1px solid rgba(255,255,255,0.04); white-space:nowrap; }
.ticker-item .sym { color:rgba(255,255,255,0.35); letter-spacing:.08em; }
.ticker-item .val { color:#fff; font-weight:500; }
.ticker-item .up  { color:var(--green); }
.ticker-item .dn  { color:var(--red); }
@keyframes ticker { from { transform:translateX(0); } to { transform:translateX(-50%); } }

/* nav */
.nav {
  position:relative; z-index:20;
  display:flex; justify-content:space-between; align-items:center;
  padding:20px 56px; border-bottom:1px solid var(--border);
  background:rgba(3,6,10,0.7); backdrop-filter:blur(20px);
}
.nav-logo { font-family:'Syne',sans-serif; font-size:18px; font-weight:800; letter-spacing:0.06em; color:#fff; text-transform:uppercase; }
.nav-logo span { color:var(--green); }
.nav-links { display:flex; gap:32px; align-items:center; }
.nav-link  { font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.15em; color:var(--muted2); text-transform:uppercase; cursor:pointer; transition:color .2s; }
.nav-link:hover { color:var(--green); }
.nav-badge { font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.12em; padding:6px 16px; border:1px solid rgba(0,255,170,0.3); color:var(--green); border-radius:2px; background:rgba(0,255,170,0.06); cursor:pointer; transition:all .2s; }
.nav-badge:hover { background:rgba(0,255,170,0.14); box-shadow:0 0 20px rgba(0,255,170,0.15); }

/* hero */
.hero { position:relative; z-index:5; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:110px 56px 90px; text-align:center; animation:fadeUp .9s ease both; }
.hero-eyebrow { display:inline-flex; align-items:center; gap:14px; font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.28em; text-transform:uppercase; color:var(--green); margin-bottom:40px; }
.hero-eyebrow::before, .hero-eyebrow::after { content:''; display:block; width:40px; height:1px; background:linear-gradient(to right, transparent, var(--green)); }
.hero-eyebrow::after { background:linear-gradient(to left, transparent, var(--green)); }
.hero-title { font-family:'Syne',sans-serif; font-size:clamp(44px,7.5vw,108px); line-height:1.0; letter-spacing:-.01em; font-weight:800; color:#fff; width:100%; }
.hero-title .accent { background:linear-gradient(100deg, var(--green) 0%, var(--cyan) 50%, var(--blue) 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; filter:drop-shadow(0 0 40px rgba(0,255,170,0.3)); }
.hero-sub  { font-size:16px; font-weight:300; color:var(--muted2); max-width:580px; line-height:1.85; margin:30px auto 0; }
.hero-badges { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-top:40px; }
.hero-badge  { display:inline-flex; align-items:center; gap:8px; font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.1em; padding:5px 13px; border-radius:2px; }
.hb-live { border:1px solid rgba(0,255,170,0.25);   color:var(--green);  background:rgba(0,255,170,0.06); }
.hb-ai   { border:1px solid rgba(181,109,255,0.25); color:var(--purple); background:rgba(181,109,255,0.06); }
.hb-rt   { border:1px solid rgba(0,194,255,0.25);   color:var(--blue);   background:rgba(0,194,255,0.06); }
.live-dot { width:7px; height:7px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100% { box-shadow:0 0 0 0 rgba(0,255,170,.5); } 70% { box-shadow:0 0 0 9px rgba(0,255,170,0); } }

/* section label */
.section-label { position:relative; z-index:5; display:flex; align-items:center; gap:24px; padding:0 56px; margin-bottom:28px; margin-top:80px; }
.section-label span { font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.22em; color:var(--muted); text-transform:uppercase; white-space:nowrap; }
.section-label::after { content:''; flex:1; height:1px; background:linear-gradient(to right, var(--border), transparent); }

/* sparkline */
.sparkline { position:relative; height:32px; width:100%; margin:8px 0 12px; }
.sparkline svg { width:100%; height:100%; }

/* module cards — 6-column grid */
.modules-outer { position:relative; z-index:5; margin:0 56px; border:1px solid var(--border); border-top:none; animation:fadeUp .8s ease .3s both; }
.modules-row   { display:grid; grid-template-columns:repeat(6,1fr); gap:0; }

.mc { background:var(--bg2); padding:22px 20px 18px; position:relative; overflow:hidden; transition:background .25s, transform .2s, box-shadow .25s; cursor:pointer; border-top:2px solid transparent; }
.mc + .mc { border-left:1px solid var(--border); }
.mc:hover  { background:var(--bg3); transform:translateY(-3px); z-index:2; }

.mc-price   { border-top-color:var(--green);  box-shadow:inset 0 2px 0 0 var(--green); }
.mc-pattern { border-top-color:var(--red);    box-shadow:inset 0 2px 0 0 var(--red); }
.mc-vol     { border-top-color:var(--purple); box-shadow:inset 0 2px 0 0 var(--purple); }
.mc-paper   { border-top-color:var(--orange); box-shadow:inset 0 2px 0 0 var(--orange); }
.mc-quest   { border-top-color:var(--gold);   box-shadow:inset 0 2px 0 0 var(--gold); }
.mc-agent   { border-top-color:var(--teal);   box-shadow:inset 0 2px 0 0 var(--teal); }

.mc-price:hover   { box-shadow:inset 0 2px 0 0 var(--green),  0 8px 32px rgba(0,255,170,.1); }
.mc-pattern:hover { box-shadow:inset 0 2px 0 0 var(--red),    0 8px 32px rgba(255,77,109,.1); }
.mc-vol:hover     { box-shadow:inset 0 2px 0 0 var(--purple),  0 8px 32px rgba(181,109,255,.1); }
.mc-paper:hover   { box-shadow:inset 0 2px 0 0 var(--orange),  0 8px 32px rgba(255,123,61,.1); }
.mc-quest:hover   { box-shadow:inset 0 2px 0 0 var(--gold),    0 8px 32px rgba(255,193,69,.12); }
.mc-agent:hover   { box-shadow:inset 0 2px 0 0 var(--teal),    0 8px 32px rgba(0,212,200,.12); }

.mc-scan { position:absolute; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,.06),transparent); top:-100%; pointer-events:none; }
.mc:hover .mc-scan { animation:scanDown 2s ease-in-out infinite; }
@keyframes scanDown { from{top:-2%;} to{top:102%;} }

.mc-icon { width:36px; height:36px; border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:16px; margin-bottom:12px; }
.mc-price   .mc-icon { background:rgba(0,255,170,.09);   border:1px solid rgba(0,255,170,.25); }
.mc-pattern .mc-icon { background:rgba(255,77,109,.09);  border:1px solid rgba(255,77,109,.25); }
.mc-vol     .mc-icon { background:rgba(181,109,255,.09); border:1px solid rgba(181,109,255,.25); }
.mc-paper   .mc-icon { background:rgba(255,123,61,.09);  border:1px solid rgba(255,123,61,.25); }
.mc-quest   .mc-icon { background:rgba(255,193,69,.09);  border:1px solid rgba(255,193,69,.25); }
.mc-agent   .mc-icon { background:rgba(0,212,200,.09);   border:1px solid rgba(0,212,200,.25); }

.mc-num    { font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:.18em; color:var(--muted); text-transform:uppercase; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; }
.mc-status { font-family:'JetBrains Mono',monospace; font-size:7.5px; letter-spacing:.1em; padding:2px 7px; border-radius:2px; text-transform:uppercase; }
.mc-price   .mc-status { color:var(--green);  border:1px solid rgba(0,255,170,.3);   background:rgba(0,255,170,.07); }
.mc-pattern .mc-status { color:var(--red);    border:1px solid rgba(255,77,109,.3);  background:rgba(255,77,109,.07); }
.mc-vol     .mc-status { color:var(--purple); border:1px solid rgba(181,109,255,.3); background:rgba(181,109,255,.07); }
.mc-paper   .mc-status { color:var(--orange); border:1px solid rgba(255,123,61,.3);  background:rgba(255,123,61,.07); }
.mc-quest   .mc-status { color:var(--gold);   border:1px solid rgba(255,193,69,.3);  background:rgba(255,193,69,.07); }
.mc-agent   .mc-status { color:var(--teal);   border:1px solid rgba(0,212,200,.3);   background:rgba(0,212,200,.07); }

.mc-title { font-family:'Syne',sans-serif; font-size:14px; font-weight:700; color:#fff; margin-bottom:6px; letter-spacing:-.01em; line-height:1.2; }
.mc-desc  { font-size:10.5px; font-weight:300; color:var(--muted2); line-height:1.7; margin-bottom:12px; }

.mc-price   .spark-path { stroke:var(--green); }
.mc-pattern .spark-path { stroke:var(--red); }
.mc-vol     .spark-path { stroke:var(--purple); }
.mc-paper   .spark-path { stroke:var(--orange); }
.mc-quest   .spark-path { stroke:var(--gold); }
.mc-agent   .spark-path { stroke:var(--teal); }

.mc-kpis { display:flex; border:1px solid var(--border); margin-bottom:12px; }
.mc-kpi  { flex:1; padding:6px 4px; text-align:center; border-right:1px solid var(--border); }
.mc-kpi:last-child { border-right:none; }
.mc-kpi-val { font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600; margin-bottom:2px; }
.mc-price   .mc-kpi-val { color:var(--green); }
.mc-pattern .mc-kpi-val { color:var(--red); }
.mc-vol     .mc-kpi-val { color:var(--purple); }
.mc-paper   .mc-kpi-val { color:var(--orange); }
.mc-quest   .mc-kpi-val { color:var(--gold); }
.mc-agent   .mc-kpi-val { color:var(--teal); }
.mc-kpi-lbl { font-size:7.5px; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; }

.mc-tags { display:flex; flex-wrap:wrap; gap:3px; margin-bottom:14px; }
.mc-tag  { font-family:'JetBrains Mono',monospace; font-size:7px; letter-spacing:.08em; padding:2px 7px; border-radius:2px; background:rgba(255,255,255,.025); color:rgba(255,255,255,.3); border:1px solid rgba(255,255,255,.06); }

.mc-bgnum { position:absolute; bottom:-18px; right:10px; font-family:'Syne',sans-serif; font-size:90px; font-weight:800; color:rgba(255,255,255,.015); line-height:1; pointer-events:none; user-select:none; transition:color .3s; }
.mc:hover .mc-bgnum { color:rgba(255,255,255,.03); }

/* launch buttons — 6 columns */
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(1) button { background:rgba(0,255,170,.07) !important; border:1px solid rgba(0,255,170,.3) !important; color:var(--green) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(1) button:hover { background:rgba(0,255,170,.15) !important; box-shadow:0 0 20px rgba(0,255,170,.15) !important; }

div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(2) button { background:rgba(255,77,109,.07) !important; border:1px solid rgba(255,77,109,.3) !important; color:var(--red) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(2) button:hover { background:rgba(255,77,109,.15) !important; box-shadow:0 0 20px rgba(255,77,109,.15) !important; }

div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(3) button { background:rgba(181,109,255,.07) !important; border:1px solid rgba(181,109,255,.3) !important; color:var(--purple) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(3) button:hover { background:rgba(181,109,255,.15) !important; box-shadow:0 0 20px rgba(181,109,255,.15) !important; }

div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(4) button { background:rgba(255,123,61,.07) !important; border:1px solid rgba(255,123,61,.3) !important; color:var(--orange) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(4) button:hover { background:rgba(255,123,61,.15) !important; box-shadow:0 0 20px rgba(255,123,61,.15) !important; }

div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(5) button { background:rgba(255,193,69,.07) !important; border:1px solid rgba(255,193,69,.3) !important; color:var(--gold) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(5) button:hover { background:rgba(255,193,69,.15) !important; box-shadow:0 0 20px rgba(255,193,69,.15) !important; }

div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(6) button { background:rgba(0,212,200,.07) !important; border:1px solid rgba(0,212,200,.3) !important; color:var(--teal) !important; font-family:'JetBrains Mono',monospace !important; font-size:9px !important; letter-spacing:.13em !important; padding:10px 8px !important; border-radius:0 !important; text-transform:uppercase !important; width:100% !important; transition:all .2s !important; }
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(6) button:hover { background:rgba(0,212,200,.15) !important; box-shadow:0 0 20px rgba(0,212,200,.15) !important; }

/* stats bar */
.stats-bar  { position:relative; z-index:5; display:flex; justify-content:center; align-items:stretch; flex-wrap:wrap; margin:48px 56px 0; border:1px solid var(--border); background:var(--bg2); animation:fadeUp .8s ease .55s both; }
.stat-item  { flex:1; min-width:110px; padding:28px 20px; text-align:center; border-right:1px solid var(--border); position:relative; overflow:hidden; transition:background .3s; cursor:default; }
.stat-item:last-child { border-right:none; }
.stat-item:hover { background:var(--bg4); }
.stat-item::before { content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:0; height:2px; background:var(--green); transition:width .4s; }
.stat-item:hover::before { width:100%; }
.stat-val { font-family:'Syne',sans-serif; font-size:30px; letter-spacing:.04em; color:#fff; margin-bottom:6px; line-height:1; font-weight:700; }
.stat-lbl { font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:.18em; color:var(--muted); text-transform:uppercase; }

/* footer */
.footer      { position:relative; z-index:5; text-align:center; padding:48px 56px; margin-top:64px; border-top:1px solid var(--border); }
.footer-logo { font-family:'Syne',sans-serif; font-size:14px; font-weight:800; letter-spacing:.08em; color:rgba(255,255,255,.2); text-transform:uppercase; margin-bottom:12px; }
.footer-logo span { color:rgba(0,255,170,.4); }
.footer-text { font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.15em; color:var(--muted); text-transform:uppercase; }

.num-highlight { font-size:13px; font-weight:700; color:var(--purple); border:1px solid rgba(181,109,255,0.6); padding:1px 7px; border-radius:2px; background:rgba(181,109,255,0.12); margin-right:2px; display:inline-block; }

@keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── RENDER
# ══════════════════════════════════════════════════════════════════════════════

# background
st.markdown("""
<div class="bg-grid"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="orb orb-4"></div>
<div class="orb orb-5"></div>
""", unsafe_allow_html=True)

# ticker
st.markdown(
    f'<div class="ticker-wrap"><div class="ticker-track">{ticker_html()}</div></div>',
    unsafe_allow_html=True,
)

# nav
nav_links_html = "".join(f'<div class="nav-link">{l}</div>' for l in NAV_LINKS)
st.markdown(f"""
<div class="nav">
  <div class="nav-logo">Trade<span>Sphere</span></div>
  <div class="nav-links">
    {nav_links_html}
    <div class="nav-badge">{NAV_CTA}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# hero
hero_badges_html = "".join(
    f'<div class="hero-badge {cls}">{content}</div>'
    for cls, content in HERO_BADGES
)
st.markdown(f"""
<div class="hero">
  <div class="hero-eyebrow">Trade Sphere &nbsp;·&nbsp; AI Market Intelligence</div>
  <div class="hero-title">{HERO_TITLE[0]}<br><span class="accent">{HERO_TITLE[1]}</span></div>
  <p class="hero-sub">{HERO_SUB}</p>
  <div class="hero-badges">{hero_badges_html}</div>
</div>
""", unsafe_allow_html=True)

# module cards
st.markdown('<div class="section-label"><span>01 — Core Modules</span></div>', unsafe_allow_html=True)

cards_html = "".join(module_card_html(m) for m in MODULE_DATA)
st.markdown(
    f'<div class="modules-outer"><div class="modules-row">{cards_html}</div></div>',
    unsafe_allow_html=True,
)

# launch buttons
cols = st.columns(len(MODULE_DATA), gap="small")
for col, m in zip(cols, MODULE_DATA):
    with col:
        if st.button(m["btn_lbl"], key=m["btn_key"]):
            st.switch_page(m["page"])

# stats bar
stats_html = "".join(
    f'<div class="stat-item"><div class="stat-val">{val}</div><div class="stat-lbl">{lbl}</div></div>'
    for val, lbl in STATS_BAR_DATA
)
st.markdown(f'<div class="stats-bar">{stats_html}</div>', unsafe_allow_html=True)

# footer
st.markdown("""
<div class="footer">
  <div class="footer-logo">Trade<span>Sphere</span></div>
  <div class="footer-text">AI Market Intelligence &nbsp;·&nbsp; Price · Pattern · Volatility · Paper Trading · Daily Quests · Trading Agent</div>
</div>
""", unsafe_allow_html=True)