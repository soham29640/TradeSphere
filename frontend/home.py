import streamlit as st
import random, math, time

st.set_page_config(
    page_title="Trade Sphere",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── seed fake "live" metrics that change on rerun ──────────────────────────────
rng = random.Random(int(time.time() // 60))          # changes every 60 s

def _chg():
    v = rng.uniform(-4.5, 5.5)
    sign = "▲" if v >= 0 else "▼"
    cls  = "up" if v >= 0 else "dn"
    return sign, cls, abs(v)

TICKERS = [
    ("AAPL", 189.42), ("TSLA", 241.87), ("MSFT", 412.65),
    ("NVDA", 875.30), ("AMZN", 184.22), ("GOOG", 162.91),
    ("META", 504.17), ("SPY",  521.44), ("BTC",  67842),
    ("ETH",  3541),   ("GOLD", 2318),   ("QQQ",  448.21),
    ("AMD",  156.78), ("NFLX", 628.55), ("CRM",  289.11),
]

def ticker_html():
    items = ""
    for sym, base in TICKERS:
        s, c, pct = _chg()
        price = base * (1 + rng.uniform(-0.03, 0.03))
        fmt = f"${price:,.2f}" if base < 10000 else f"${price:,.0f}"
        items += f'<div class="ticker-item"><span class="sym">{sym}</span><span class="val">{fmt}</span><span class="{c}">{s} {pct:.2f}%</span></div>'
    return items * 2          # duplicate for seamless loop

def heatmap_html():
    sectors = [
        ("Technology",  ["AAPL","MSFT","NVDA","AMD","ORCL"]),
        ("Financials",  ["JPM","GS","BAC","WFC","MS"]),
        ("Healthcare",  ["JNJ","PFE","UNH","ABBV","MRK"]),
        ("Energy",      ["XOM","CVX","COP","SLB","EOG"]),
        ("Consumer",    ["AMZN","TSLA","HD","MCD","SBUX"]),
        ("Comm Svcs",   ["META","GOOG","NFLX","DIS","T"]),
    ]
    cells = ""
    for sector, tickers in sectors:
        cells += f'<div class="hm-sector-label">{sector}</div>'
        for sym in tickers:
            v = rng.uniform(-4.5, 5.5)
            intensity = min(abs(v) / 5, 1)
            if v >= 0:
                r,g,b = int(0+30*intensity), int(180+60*intensity), int(100+40*intensity)
            else:
                r,g,b = int(180+60*intensity), int(40+30*intensity), int(60+20*intensity)
            bg = f"rgb({r},{g},{b})"
            txt_col = "#000" if intensity < 0.5 else "#fff"
            sign = "+" if v >= 0 else ""
            cells += f'<div class="hm-cell" style="background:{bg};color:{txt_col};"><span class="hm-sym">{sym}</span><span class="hm-val">{sign}{v:.1f}%</span></div>'
    return cells

# ─────────────────────────────── CSS ──────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

:root {{
  --green:   #00ffaa;
  --blue:    #00c2ff;
  --red:     #ff4d6d;
  --gold:    #ffc145;
  --purple:  #b56dff;
  --cyan:    #00e5ff;
  --orange:  #ff7b3d;
  --bg:      #03060a;
  --bg2:     #080d14;
  --bg3:     #0d1520;
  --bg4:     #111c2a;
  --border:  rgba(255,255,255,0.07);
  --border2: rgba(255,255,255,0.12);
  --text:    #c8d5e8;
  --muted:   #3a4d62;
  --muted2:  #5a6f85;
}}

*, *::before, *::after {{ box-sizing: border-box; margin:0; padding:0; }}

html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg) !important;
  font-family: 'Space Grotesk', sans-serif;
  color: var(--text);
}}
[data-testid="stHeader"], footer,
[data-testid="stToolbar"], #MainMenu,
[data-testid="stSidebarCollapsedControl"] {{ display:none !important; }}
[data-testid="stMainBlockContainer"] {{ padding:0 !important; max-width:100% !important; }}
section.main > div {{ padding:0 !important; }}
[data-testid="stVerticalBlock"] {{ gap:0 !important; }}

/* ── animated grid bg ── */
.bg-grid {{
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(0,255,170,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,170,0.025) 1px, transparent 1px);
  background-size:80px 80px;
  animation: gridPan 25s linear infinite;
}}
@keyframes gridPan {{ to {{ background-position:80px 80px; }} }}

/* radial glow orbs */
.orb {{ position:fixed; border-radius:50%; filter:blur(130px); pointer-events:none; z-index:0; animation:orbDrift 10s ease-in-out infinite alternate; }}
.orb-1 {{ width:700px; height:700px; top:-200px; left:-200px; background:rgba(0,255,170,0.06); }}
.orb-2 {{ width:500px; height:500px; top:40%; right:-150px; background:rgba(0,194,255,0.05); animation-delay:-4s; }}
.orb-3 {{ width:450px; height:450px; bottom:-100px; left:35%; background:rgba(181,109,255,0.045); animation-delay:-7s; }}
.orb-4 {{ width:300px; height:300px; top:60%; left:10%; background:rgba(255,123,61,0.03); animation-delay:-2s; }}
@keyframes orbDrift {{ from {{ transform:translateY(0) scale(1); }} to {{ transform:translateY(-50px) scale(1.06); }} }}

/* ── ticker ── */
.ticker-wrap {{
  position:relative; z-index:10;
  background:linear-gradient(135deg, var(--bg2) 0%, rgba(8,13,20,0.95) 100%);
  border-bottom:1px solid var(--border);
  padding:0; overflow:hidden; height:44px; display:flex; align-items:center;
}}
.ticker-wrap::before, .ticker-wrap::after {{
  content:''; position:absolute; top:0; bottom:0; width:80px; z-index:2;
}}
.ticker-wrap::before {{ left:0; background:linear-gradient(90deg, var(--bg2), transparent); }}
.ticker-wrap::after  {{ right:0; background:linear-gradient(-90deg, var(--bg2), transparent); }}
.ticker-track {{ display:flex; animation:ticker 55s linear infinite; width:max-content; }}
.ticker-item {{
  display:inline-flex; align-items:center; gap:10px;
  padding:0 32px; font-family:'JetBrains Mono',monospace; font-size:11px;
  border-right:1px solid rgba(255,255,255,0.04); white-space:nowrap;
}}
.ticker-item .sym {{ color:rgba(255,255,255,0.35); letter-spacing:.08em; }}
.ticker-item .val {{ color:#fff; font-weight:500; }}
.ticker-item .up  {{ color:var(--green); }}
.ticker-item .dn  {{ color:var(--red); }}
@keyframes ticker {{ from {{ transform:translateX(0); }} to {{ transform:translateX(-50%); }} }}

/* ── nav bar ── */
.nav {{
  position:relative; z-index:20;
  display:flex; justify-content:space-between; align-items:center;
  padding:20px 56px; border-bottom:1px solid var(--border);
  background:rgba(3,6,10,0.7); backdrop-filter:blur(20px);
}}
.nav-logo {{
  font-family:'Syne',sans-serif; font-size:18px; font-weight:800;
  letter-spacing:0.06em; color:#fff; text-transform:uppercase;
}}
.nav-logo span {{ color:var(--green); }}
.nav-links {{ display:flex; gap:32px; align-items:center; }}
.nav-link {{
  font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.15em;
  color:var(--muted2); text-transform:uppercase; cursor:pointer;
  transition:color .2s;
}}
.nav-link:hover {{ color:var(--green); }}
.nav-badge {{
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.12em;
  padding:6px 16px; border:1px solid rgba(0,255,170,0.3); color:var(--green);
  border-radius:2px; background:rgba(0,255,170,0.06); cursor:pointer;
  transition:all .2s;
}}
.nav-badge:hover {{ background:rgba(0,255,170,0.14); box-shadow:0 0 20px rgba(0,255,170,0.15); }}

/* ── hero ── */
.hero {{
  position:relative; z-index:5;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:110px 56px 90px; text-align:center;
  animation:fadeUp .9s ease both;
}}
.hero-eyebrow {{
  display:inline-flex; align-items:center; gap:14px;
  font-family:'JetBrains Mono',monospace; font-size:10px;
  letter-spacing:.28em; text-transform:uppercase; color:var(--green);
  margin-bottom:40px;
}}
.hero-eyebrow::before, .hero-eyebrow::after {{
  content:''; display:block; width:40px; height:1px;
  background:linear-gradient(to right, transparent, var(--green));
}}
.hero-eyebrow::after {{ background:linear-gradient(to left, transparent, var(--green)); }}
.hero-title {{
  font-family:'Syne',sans-serif; font-size:clamp(36px,6vw,88px);
  line-height:1.0; letter-spacing:-.01em; font-weight:800; color:#fff;
  overflow:hidden; width:100%;
}}
.hero-title .accent {{
  background:linear-gradient(100deg, var(--green) 0%, var(--cyan) 50%, var(--blue) 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  filter:drop-shadow(0 0 40px rgba(0,255,170,0.3));
}}
.hero-sub {{
  font-size:16px; font-weight:300; color:var(--muted2);
  max-width:540px; line-height:1.85; margin:30px auto 0;
}}
.hero-badges {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-top:40px; }}
.hero-badge {{
  display:inline-flex; align-items:center; gap:8px;
  font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.1em;
  padding:8px 18px; border-radius:2px;
}}
.hb-live {{ border:1px solid rgba(0,255,170,0.25); color:var(--green); background:rgba(0,255,170,0.06); }}
.hb-ai   {{ border:1px solid rgba(181,109,255,0.25); color:var(--purple); background:rgba(181,109,255,0.06); }}
.hb-rt   {{ border:1px solid rgba(0,194,255,0.25); color:var(--blue); background:rgba(0,194,255,0.06); }}
.live-dot {{ width:7px; height:7px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }}
@keyframes pulse {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(0,255,170,.5); }} 70% {{ box-shadow:0 0 0 9px rgba(0,255,170,0); }} }}

/* ── section label ── */
.section-label {{
  position:relative; z-index:5;
  display:flex; align-items:center; gap:24px;
  padding:0 56px; margin-bottom:28px; margin-top:80px;
}}
.section-label span {{
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.22em;
  color:var(--muted); text-transform:uppercase; white-space:nowrap;
}}
.section-label::after {{ content:''; flex:1; height:1px; background:linear-gradient(to right, var(--border), transparent); }}

/* ── mini sparkline ── */
.sparkline {{ position:relative; height:50px; width:100%; margin:16px 0; }}
.sparkline svg {{ width:100%; height:100%; }}

/* ── module cards ── */
.cards-wrapper {{
  position:relative; z-index:5;
  display:grid; grid-template-columns:repeat(2,1fr);
  gap:1px; margin:0 56px;
  background:var(--border); border:1px solid var(--border);
  animation:fadeUp .8s ease .3s both;
}}
.card {{
  background:var(--bg2); padding:48px 40px 36px; position:relative; overflow:hidden;
  transition:background .3s ease;
}}
.card:hover {{ background:var(--bg3); }}

/* top accent line */
.card::before {{
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  opacity:0; transition:opacity .4s;
}}
.card:hover::before {{ opacity:1; }}
.card-price::before    {{ background:linear-gradient(90deg,transparent,var(--green),var(--cyan),transparent); }}
.card-pattern::before  {{ background:linear-gradient(90deg,transparent,var(--red),var(--gold),transparent); }}
.card-vol::before      {{ background:linear-gradient(90deg,transparent,var(--purple),var(--blue),transparent); }}
.card-paper::before    {{ background:linear-gradient(90deg,transparent,var(--orange),var(--gold),transparent); }}

/* scan-line sweep on hover */
.scan-line {{
  position:absolute; left:0; right:0; height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.07),transparent);
  top:-100%; pointer-events:none;
}}
.card:hover .scan-line {{ animation:scanDown 1.8s ease-in-out infinite; }}
@keyframes scanDown {{ from {{ top:-2%; }} to {{ top:102%; }} }}

/* corner glow */
.card::after {{
  content:''; position:absolute; top:0; right:0; width:120px; height:120px;
  border-radius:0 0 0 120px; opacity:0; transition:opacity .4s;
}}
.card:hover::after {{ opacity:.08; }}
.card-price::after    {{ background:var(--green); }}
.card-pattern::after  {{ background:var(--red); }}
.card-vol::after      {{ background:var(--purple); }}
.card-paper::after    {{ background:var(--orange); }}

.card-meta {{
  display:flex; justify-content:space-between; align-items:center; margin-bottom:28px;
}}
.card-num {{ font-family:'JetBrains Mono',monospace; font-size:9px; color:var(--muted); letter-spacing:.15em; }}
.card-status {{
  font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:.12em;
  padding:4px 10px; border-radius:2px;
}}
.card-price   .card-status {{ color:var(--green);  border:1px solid rgba(0,255,170,.2);  background:rgba(0,255,170,.05); }}
.card-pattern .card-status {{ color:var(--red);    border:1px solid rgba(255,77,109,.2); background:rgba(255,77,109,.05); }}
.card-vol     .card-status {{ color:var(--purple); border:1px solid rgba(181,109,255,.2);background:rgba(181,109,255,.05); }}
.card-paper   .card-status {{ color:var(--orange); border:1px solid rgba(255,123,61,.2); background:rgba(255,123,61,.05); }}

.card-icon-wrap {{
  width:56px; height:56px; border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  font-size:24px; margin-bottom:22px;
}}
.card-price   .card-icon-wrap {{ background:rgba(0,255,170,.08);  border:1px solid rgba(0,255,170,.18); }}
.card-pattern .card-icon-wrap {{ background:rgba(255,77,109,.08); border:1px solid rgba(255,77,109,.18); }}
.card-vol     .card-icon-wrap {{ background:rgba(181,109,255,.08);border:1px solid rgba(181,109,255,.18); }}
.card-paper   .card-icon-wrap {{ background:rgba(255,123,61,.08); border:1px solid rgba(255,123,61,.18); }}

.card-title {{ font-family:'Syne',sans-serif; font-size:22px; font-weight:700; color:#fff; margin-bottom:12px; letter-spacing:-.02em; }}
.card-desc  {{ font-size:12.5px; font-weight:300; color:var(--muted2); line-height:1.9; margin-bottom:24px; }}

/* sparkline accent color */
.card-price   .spark-path {{ stroke:var(--green); }}
.card-pattern .spark-path {{ stroke:var(--red); }}
.card-vol     .spark-path {{ stroke:var(--purple); }}
.card-paper   .spark-path {{ stroke:var(--orange); }}

.card-kpis {{ display:flex; gap:0; margin-bottom:24px; border:1px solid var(--border); }}
.card-kpi {{ flex:1; padding:12px 14px; border-right:1px solid var(--border); text-align:center; }}
.card-kpi:last-child {{ border-right:none; }}
.card-kpi-val {{
  font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:500; margin-bottom:4px;
}}
.card-price   .card-kpi-val {{ color:var(--green); }}
.card-pattern .card-kpi-val {{ color:var(--red); }}
.card-vol     .card-kpi-val {{ color:var(--purple); }}
.card-paper   .card-kpi-val {{ color:var(--orange); }}
.card-kpi-lbl {{ font-size:9px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }}

.card-tags {{ display:flex; flex-wrap:wrap; gap:5px; margin-bottom:32px; }}
.tag {{
  font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:.1em;
  padding:3px 9px; border-radius:2px;
  background:rgba(255,255,255,0.025); color:rgba(255,255,255,0.28);
  border:1px solid rgba(255,255,255,0.06);
}}

.card-bg-num {{
  position:absolute; bottom:-24px; right:16px;
  font-family:'Syne',sans-serif; font-size:130px; font-weight:800;
  color:rgba(255,255,255,0.018); line-height:1;
  pointer-events:none; user-select:none; transition:color .4s;
}}
.card:hover .card-bg-num {{ color:rgba(255,255,255,0.032); }}

/* ── Buttons per column ── */
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(1) button {{
  background:rgba(0,255,170,.07) !important; border:1px solid rgba(0,255,170,.28) !important;
  color:var(--green) !important; font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important; letter-spacing:.14em !important; padding:13px 28px !important;
  border-radius:2px !important; text-transform:uppercase !important;
  box-shadow:0 0 20px rgba(0,255,170,.04) !important; transition:all .2s !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(1) button:hover {{
  background:rgba(0,255,170,.14) !important; box-shadow:0 0 30px rgba(0,255,170,.18) !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(2) button {{
  background:rgba(255,77,109,.07) !important; border:1px solid rgba(255,77,109,.28) !important;
  color:var(--red) !important; font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important; letter-spacing:.14em !important; padding:13px 28px !important;
  border-radius:2px !important; text-transform:uppercase !important;
  box-shadow:0 0 20px rgba(255,77,109,.04) !important; transition:all .2s !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(2) button:hover {{
  background:rgba(255,77,109,.14) !important; box-shadow:0 0 30px rgba(255,77,109,.18) !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(3) button {{
  background:rgba(181,109,255,.07) !important; border:1px solid rgba(181,109,255,.28) !important;
  color:var(--purple) !important; font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important; letter-spacing:.14em !important; padding:13px 28px !important;
  border-radius:2px !important; text-transform:uppercase !important;
  box-shadow:0 0 20px rgba(181,109,255,.04) !important; transition:all .2s !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(3) button:hover {{
  background:rgba(181,109,255,.14) !important; box-shadow:0 0 30px rgba(181,109,255,.18) !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(4) button {{
  background:rgba(255,123,61,.07) !important; border:1px solid rgba(255,123,61,.28) !important;
  color:var(--orange) !important; font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important; letter-spacing:.14em !important; padding:13px 28px !important;
  border-radius:2px !important; text-transform:uppercase !important;
  box-shadow:0 0 20px rgba(255,123,61,.04) !important; transition:all .2s !important;
}}
div[data-testid="stColumns"] [data-testid="stColumn"]:nth-child(4) button:hover {{
  background:rgba(255,123,61,.14) !important; box-shadow:0 0 30px rgba(255,123,61,.18) !important;
}}

/* ── Heatmap CSS removed ── */

/* ── Stats bar ── */
.stats-bar {{
  position:relative; z-index:5;
  display:flex; justify-content:center; align-items:stretch; flex-wrap:wrap;
  margin:48px 56px 0; border:1px solid var(--border); background:var(--bg2);
  animation:fadeUp .8s ease .55s both;
}}
.stat-item {{
  flex:1; min-width:110px; padding:28px 20px;
  text-align:center; border-right:1px solid var(--border);
  position:relative; overflow:hidden; transition:background .3s; cursor:default;
}}
.stat-item:last-child {{ border-right:none; }}
.stat-item:hover {{ background:var(--bg4); }}
.stat-item::before {{
  content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
  width:0; height:2px; background:var(--green); transition:width .4s;
}}
.stat-item:hover::before {{ width:100%; }}
.stat-val {{
  font-family:'Syne',sans-serif; font-size:30px; letter-spacing:.04em;
  color:#fff; margin-bottom:6px; line-height:1; font-weight:700;
}}
.stat-lbl {{
  font-family:'JetBrains Mono',monospace; font-size:8px;
  letter-spacing:.18em; color:var(--muted); text-transform:uppercase;
}}

/* ── Market Pulse row ── */
.pulse-row {{
  position:relative; z-index:5; margin:48px 56px 0;
  display:grid; grid-template-columns:1fr 1fr 1fr; gap:1px;
  background:var(--border); border:1px solid var(--border);
  animation:fadeUp .8s ease .6s both;
}}
.pulse-card {{ background:var(--bg2); padding:32px 36px; }}
.pulse-title {{
  font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:.2em;
  text-transform:uppercase; color:var(--muted); margin-bottom:20px;
}}
.fear-gauge {{
  display:flex; align-items:center; gap:20px;
}}
.gauge-ring {{
  width:80px; height:80px; border-radius:50%; flex-shrink:0;
  background:conic-gradient(var(--orange) 0% 28%, var(--bg3) 28% 100%);
  display:flex; align-items:center; justify-content:center;
  position:relative;
}}
.gauge-ring::before {{
  content:''; position:absolute; inset:8px; border-radius:50%; background:var(--bg2);
}}
.gauge-val {{
  position:relative; z-index:1; font-family:'Syne',sans-serif;
  font-size:22px; font-weight:700; color:var(--orange);
}}
.gauge-labels {{ flex:1; }}
.gauge-name {{ font-size:18px; font-weight:600; color:var(--orange); margin-bottom:4px; }}
.gauge-sub {{ font-size:11px; color:var(--muted2); }}

.index-list {{ display:flex; flex-direction:column; gap:12px; }}
.index-row {{ display:flex; justify-content:space-between; align-items:center; padding-bottom:12px; border-bottom:1px solid var(--border); }}
.index-row:last-child {{ border-bottom:none; padding-bottom:0; }}
.index-name {{ font-size:13px; color:var(--text); font-weight:500; }}
.index-val {{ font-family:'JetBrains Mono',monospace; font-size:12px; color:#fff; }}
.index-chg-up {{ font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--green); }}
.index-chg-dn {{ font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--red); }}

.vol-bars {{ display:flex; flex-direction:column; gap:12px; }}
.vol-row {{ display:flex; align-items:center; gap:12px; }}
.vol-label {{ font-family:'JetBrains Mono',monospace; font-size:10px; color:var(--muted2); width:45px; flex-shrink:0; }}
.vol-track {{ flex:1; height:4px; background:rgba(255,255,255,.06); border-radius:2px; overflow:hidden; }}
.vol-fill {{ height:100%; border-radius:2px; }}
.vol-pct {{ font-family:'JetBrains Mono',monospace; font-size:10px; width:36px; text-align:right; }}

/* ── footer ── */
.footer {{
  position:relative; z-index:5; text-align:center; padding:48px 56px;
  margin-top:64px; border-top:1px solid var(--border);
}}
.footer-logo {{
  font-family:'Syne',sans-serif; font-size:14px; font-weight:800;
  letter-spacing:.08em; color:rgba(255,255,255,.2); text-transform:uppercase;
  margin-bottom:12px;
}}
.footer-logo span {{ color:rgba(0,255,170,.4); }}
.footer-text {{
  font-family:'JetBrains Mono',monospace; font-size:9px;
  letter-spacing:.15em; color:var(--muted); text-transform:uppercase;
}}

@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(20px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
</style>
""", unsafe_allow_html=True)

# ── build sparkline SVG paths ─────────────────────────────────────────────────
def sparkline_svg(seed, color_cls, up=True):
    r2 = random.Random(seed)
    pts = []
    y = 30
    for i in range(30):
        y += r2.uniform(-4, 4.5) * (1 if up else -1)
        y = max(5, min(45, y))
        pts.append((i * (200/29), y))
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    # area fill
    area = path + f" L {pts[-1][0]:.1f},50 L 0,50 Z"
    return f'''<svg viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
  <defs><linearGradient id="sg{seed}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" class="spark-stop-top"/>
    <stop offset="100%" stop-color="transparent"/>
  </linearGradient></defs>
  <path d="{area}" fill="rgba(255,255,255,0.03)"/>
  <path d="{path}" fill="none" class="spark-path" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# ── background structure ───────────────────────────────────────────────────────
st.markdown("""
<div class="bg-grid"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="orb orb-4"></div>
""", unsafe_allow_html=True)

# ── ticker ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ticker-wrap">
  <div class="ticker-track">{ticker_html()}</div>
</div>
""", unsafe_allow_html=True)

# ── nav ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav">
  <div class="nav-logo">Trade<span>Sphere</span></div>
  <div class="nav-links">
    <div class="nav-link">Markets</div>
    <div class="nav-link">Models</div>
    <div class="nav-link">Research</div>
    <div class="nav-link">Docs</div>
    <div class="nav-badge">→ OPEN PLATFORM</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">Trade Sphere &nbsp;·&nbsp; AI Market Intelligence</div>
  <div class="hero-title">MARKETS,<br><span class="accent">DECODED.</span></div>
  <p class="hero-sub">Four AI-powered modules. One unified platform. Predict prices, detect chart patterns, forecast volatility, and simulate live paper trading — all in real-time.</p>
  <div class="hero-badges">
    <div class="hero-badge hb-live"><div class="live-dot"></div>LIVE DATA · DAILY REFRESH</div>
    <div class="hero-badge hb-ai">⬡ &nbsp;4 AI MODELS ACTIVE</div>
    <div class="hero-badge hb-rt">◈ &nbsp;REAL-TIME EXECUTION</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Market Pulse ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label"><span>01 — Market Pulse</span></div>', unsafe_allow_html=True)

# generate live-ish index data
def idx_row(name, base, rng2=None):
    if rng2 is None:
        rng2 = rng
    s,c,pct = _chg()
    val = base*(1+rng2.uniform(-.015,.015))
    chg_cls = "index-chg-up" if c=="up" else "index-chg-dn"
    return f'''<div class="index-row">
      <div class="index-name">{name}</div>
      <div style="display:flex;gap:14px;align-items:center;">
        <div class="index-val">{val:,.2f}</div>
        <div class="{chg_cls}">{s} {pct:.2f}%</div>
      </div>
    </div>'''

indices_html = (
    idx_row("S&P 500",    5234.18) +
    idx_row("NASDAQ",    16421.44) +
    idx_row("DOW JONES", 39112.10) +
    idx_row("VIX",          18.74) +
    idx_row("10Y YIELD",     4.31)
)

def vol_bar(label, pct, color):
    return f'''<div class="vol-row">
      <div class="vol-label">{label}</div>
      <div class="vol-track"><div class="vol-fill" style="width:{pct}%;background:{color};"></div></div>
      <div class="vol-pct" style="color:{color};">{pct:.0f}%</div>
    </div>'''

vix = rng.uniform(14,28)
vol_bars_html = (
    vol_bar("Tech",    rng.uniform(30,90), "var(--blue)") +
    vol_bar("Finance", rng.uniform(20,75), "var(--green)") +
    vol_bar("Energy",  rng.uniform(25,80), "var(--gold)") +
    vol_bar("Crypto",  rng.uniform(50,95), "var(--purple)") +
    vol_bar("Bonds",   rng.uniform(10,45), "var(--cyan)")
)

fear_val = int(rng.uniform(22, 72))
fear_pct = fear_val
if fear_val < 35:   fear_name, fear_col = "FEAR", "var(--red)"
elif fear_val < 55: fear_name, fear_col = "NEUTRAL", "var(--gold)"
else:               fear_name, fear_col = "GREED", "var(--green)"

st.markdown(f"""
<div class="pulse-row">
  <div class="pulse-card">
    <div class="pulse-title">◈ Fear &amp; Greed Index</div>
    <div class="fear-gauge">
      <div class="gauge-ring" style="background:conic-gradient({fear_col} 0% {fear_pct}%, rgba(255,255,255,0.05) {fear_pct}% 100%);">
        <div class="gauge-val" style="color:{fear_col};">{fear_val}</div>
      </div>
      <div class="gauge-labels">
        <div class="gauge-name" style="color:{fear_col};">{fear_name}</div>
        <div class="gauge-sub">Current market sentiment<br>Updated daily · CNN model</div>
      </div>
    </div>
  </div>
  <div class="pulse-card">
    <div class="pulse-title">◈ Global Indices</div>
    <div class="index-list">{indices_html}</div>
  </div>
  <div class="pulse-card">
    <div class="pulse-title">◈ Sector Volatility</div>
    <div class="vol-bars">{vol_bars_html}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Module cards 2×2 ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label"><span>02 — Core Modules</span></div>', unsafe_allow_html=True)

row1_col1, row1_col2 = st.columns(2, gap="small")
row2_col1, row2_col2 = st.columns(2, gap="small")

with row1_col1:
    st.markdown(f"""
    <div class="card card-price">
      <div class="scan-line"></div>
      <div class="card-meta"><span class="card-num">MODULE 01/04</span><span class="card-status">ACTIVE</span></div>
      <div class="card-icon-wrap">📈</div>
      <div class="card-title">Price Predictor</div>
      <p class="card-desc">3-layer LSTM on 5-minute OHLCV bars. Multi-step price forecasts with live Yahoo Finance data and 24-hour auto-retraining.</p>
      <div class="sparkline">{sparkline_svg(101,"green", True)}</div>
      <div class="card-kpis">
        <div class="card-kpi"><div class="card-kpi-val">60</div><div class="card-kpi-lbl">Window</div></div>
        <div class="card-kpi"><div class="card-kpi-val">30</div><div class="card-kpi-lbl">Horizon</div></div>
        <div class="card-kpi"><div class="card-kpi-val">5m</div><div class="card-kpi-lbl">Bars</div></div>
      </div>
      <div class="card-tags">
        <span class="tag">LSTM · 3-LAYER</span><span class="tag">BATCH NORM</span>
        <span class="tag">EARLY STOP</span><span class="tag">LIVE DATA</span>
      </div>
      <div class="card-bg-num">01</div>
    </div>
    <div style="padding:0 40px 40px;background:#080d14;">
    """, unsafe_allow_html=True)
    if st.button("→ LAUNCH DASHBOARD", key="price_btn"):
        st.switch_page("pages/price_app.py")
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col2:
    st.markdown(f"""
    <div class="card card-pattern">
      <div class="scan-line"></div>
      <div class="card-meta"><span class="card-num">MODULE 02/04</span><span class="card-status">ACTIVE</span></div>
      <div class="card-icon-wrap">🔍</div>
      <div class="card-title">Pattern Detector</div>
      <p class="card-desc">CNN multi-label classifier for 20 classical chart patterns. Upload a candlestick image and get per-class confidence scores in milliseconds.</p>
      <div class="sparkline">{sparkline_svg(202,"red", False)}</div>
      <div class="card-kpis">
        <div class="card-kpi"><div class="card-kpi-val">20</div><div class="card-kpi-lbl">Patterns</div></div>
        <div class="card-kpi"><div class="card-kpi-val">224</div><div class="card-kpi-lbl">Input px</div></div>
        <div class="card-kpi"><div class="card-kpi-val">TOP3</div><div class="card-kpi-lbl">Results</div></div>
      </div>
      <div class="card-tags">
        <span class="tag">CNN · RESNET</span><span class="tag">MULTI-LABEL</span>
        <span class="tag">SIGMOID</span><span class="tag">UPLOAD</span>
      </div>
      <div class="card-bg-num">02</div>
    </div>
    <div style="padding:0 40px 40px;background:#080d14;">
    """, unsafe_allow_html=True)
    if st.button("→ LAUNCH DETECTOR", key="pattern_btn"):
        st.switch_page("pages/pattern_app.py")
    st.markdown("</div>", unsafe_allow_html=True)

with row2_col1:
    st.markdown(f"""
    <div class="card card-vol">
      <div class="scan-line"></div>
      <div class="card-meta"><span class="card-num">MODULE 03/04</span><span class="card-status">ACTIVE</span></div>
      <div class="card-icon-wrap">🌊</div>
      <div class="card-title">Volatility Forecast</div>
      <p class="card-desc">Three-model ensemble — GARCH, LSTM, Attention-LSTM — forecasting next-day volatility with risk classification at the 75th percentile.</p>
      <div class="sparkline">{sparkline_svg(303,"purple", True)}</div>
      <div class="card-kpis">
        <div class="card-kpi"><div class="card-kpi-val">3</div><div class="card-kpi-lbl">Models</div></div>
        <div class="card-kpi"><div class="card-kpi-val">75%</div><div class="card-kpi-lbl">Threshold</div></div>
        <div class="card-kpi"><div class="card-kpi-val">1D</div><div class="card-kpi-lbl">Horizon</div></div>
      </div>
      <div class="card-tags">
        <span class="tag">GARCH</span><span class="tag">LSTM</span>
        <span class="tag">ATTENTION</span><span class="tag">RISK</span>
      </div>
      <div class="card-bg-num">03</div>
    </div>
    <div style="padding:0 40px 40px;background:#080d14;">
    """, unsafe_allow_html=True)
    if st.button("→ LAUNCH FORECAST", key="vol_btn"):
        st.switch_page("pages/volatility_app.py")
    st.markdown("</div>", unsafe_allow_html=True)

with row2_col2:
    st.markdown(f"""
    <div class="card card-paper">
      <div class="scan-line"></div>
      <div class="card-meta"><span class="card-num">MODULE 04/04</span><span class="card-status">LIVE</span></div>
      <div class="card-icon-wrap">💹</div>
      <div class="card-title">Paper Trading</div>
      <p class="card-desc">Real-time simulated trading powered by LSTM predictions. 5-min retraining, live buy/sell signals, and controlled trade window execution.</p>
      <div class="sparkline">{sparkline_svg(404,"orange", True)}</div>
      <div class="card-kpis">
        <div class="card-kpi"><div class="card-kpi-val">5m</div><div class="card-kpi-lbl">Refresh</div></div>
        <div class="card-kpi"><div class="card-kpi-val">1m</div><div class="card-kpi-lbl">Window</div></div>
        <div class="card-kpi"><div class="card-kpi-val">SIM</div><div class="card-kpi-lbl">Mode</div></div>
      </div>
      <div class="card-tags">
        <span class="tag">LSTM</span><span class="tag">REAL-TIME</span>
        <span class="tag">SIMULATION</span><span class="tag">AUTO-TRAIN</span>
      </div>
      <div class="card-bg-num">04</div>
    </div>
    <div style="padding:0 40px 40px;background:#080d14;">
    """, unsafe_allow_html=True)
    if st.button("→ LAUNCH TRADING", key="paper_btn"):
        st.switch_page("pages/paper_app.py")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Stats bar ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stats-bar">
  <div class="stat-item"><div class="stat-val">4</div><div class="stat-lbl">AI Modules</div></div>
  <div class="stat-item"><div class="stat-val">20</div><div class="stat-lbl">Chart Patterns</div></div>
  <div class="stat-item"><div class="stat-val">5M</div><div class="stat-lbl">Bar Resolution</div></div>
  <div class="stat-item"><div class="stat-val">LSTM</div><div class="stat-lbl">Price Model</div></div>
  <div class="stat-item"><div class="stat-val">CNN</div><div class="stat-lbl">Pattern Model</div></div>
  <div class="stat-item"><div class="stat-val">GARCH</div><div class="stat-lbl">Vol Model</div></div>
  <div class="stat-item"><div class="stat-val">24H</div><div class="stat-lbl">Retrain Cycle</div></div>
  <div class="stat-item"><div class="stat-val">∞</div><div class="stat-lbl">Paper Trades</div></div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  <div class="footer-logo">Trade<span>Sphere</span></div>
  <div class="footer-text">AI Market Intelligence &nbsp;·&nbsp; Price · Pattern · Volatility · Paper Trading</div>
</div>
""", unsafe_allow_html=True)