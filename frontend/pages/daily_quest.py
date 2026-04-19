import streamlit as st
import google.generativeai as genai
import json, time, datetime

st.set_page_config(
    page_title="Daily Quests · Trade Sphere",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Gemini setup ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

TODAY = datetime.date.today().strftime("%A, %B %d, %Y")
QUEST_CACHE_KEY = f"quests_{datetime.date.today().isoformat()}"

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

:root {
  --green:  #00ffaa; --blue: #00c2ff; --red: #ff4d6d;
  --gold:   #ffc145; --purple:#b56dff; --orange:#ff7b3d;
  --bg:     #03060a; --bg2:#080d14; --bg3:#0d1520; --bg4:#111c2a;
  --border: rgba(255,255,255,0.07); --text:#c8d5e8;
  --muted:  #3a4d62; --muted2:#5a6f85;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"]{
  background:var(--bg) !important;
  font-family:'Space Grotesk',sans-serif; color:var(--text);
}
[data-testid="stHeader"],footer,[data-testid="stToolbar"],
#MainMenu,[data-testid="stSidebarCollapsedControl"]{display:none !important;}
[data-testid="stMainBlockContainer"]{padding:0 !important;max-width:100% !important;}
section.main>div{padding:0 !important;}
[data-testid="stVerticalBlock"]{gap:0 !important;}

.bg-grid{
  position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:
    linear-gradient(rgba(255,193,69,0.02) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,193,69,0.02) 1px,transparent 1px);
  background-size:80px 80px;animation:gridPan 25s linear infinite;
}
@keyframes gridPan{to{background-position:80px 80px;}}
.orb{position:fixed;border-radius:50%;filter:blur(130px);pointer-events:none;z-index:0;}
.orb-1{width:600px;height:600px;top:-150px;left:-100px;background:rgba(255,193,69,0.05);}
.orb-2{width:500px;height:500px;bottom:-100px;right:-100px;background:rgba(255,123,61,0.04);}

/* ── Nav ── */
.nav{
  position:relative;z-index:20;
  display:flex;justify-content:space-between;align-items:center;
  padding:18px 56px;border-bottom:1px solid var(--border);
  background:rgba(3,6,10,0.8);backdrop-filter:blur(20px);
}
.nav-logo{font-family:'Syne',sans-serif;font-size:16px;font-weight:800;
  letter-spacing:.06em;color:#fff;text-transform:uppercase;}
.nav-logo span{color:var(--green);}
.nav-back{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.15em;
  color:var(--muted2);text-transform:uppercase;cursor:pointer;
  border:1px solid var(--border);padding:6px 14px;border-radius:2px;
  background:rgba(255,255,255,.02);transition:all .2s;
}
.nav-back:hover{color:var(--gold);border-color:rgba(255,193,69,.3);}

/* ── Page header ── */
.page-header{
  position:relative;z-index:5;padding:64px 56px 48px;
  border-bottom:1px solid var(--border);
}
.page-eyebrow{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.25em;
  text-transform:uppercase;color:var(--gold);margin-bottom:16px;
  display:flex;align-items:center;gap:12px;
}
.page-eyebrow::before{content:'';width:32px;height:1px;
  background:linear-gradient(to right,transparent,var(--gold));}
.page-title{
  font-family:'Syne',sans-serif;font-size:clamp(32px,5vw,60px);
  font-weight:800;color:#fff;letter-spacing:-.02em;margin-bottom:12px;
}
.page-title span{color:var(--gold);}
.page-sub{font-size:14px;font-weight:300;color:var(--muted2);max-width:500px;line-height:1.8;}
.date-badge{
  display:inline-flex;align-items:center;gap:8px;margin-top:20px;
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.12em;
  padding:6px 14px;border:1px solid rgba(255,193,69,.2);
  color:var(--gold);background:rgba(255,193,69,.05);border-radius:2px;
}
.live-dot{width:6px;height:6px;border-radius:50%;background:var(--gold);
  animation:pulse 2s infinite;}
@keyframes pulse{
  0%,100%{box-shadow:0 0 0 0 rgba(255,193,69,.5);}
  70%{box-shadow:0 0 0 8px rgba(255,193,69,0);}
}

/* ── Quest cards ── */
.quests-wrap{
  position:relative;z-index:5;padding:48px 56px;
  display:grid;grid-template-columns:1fr 1fr;gap:1px;
  background:var(--border);border:1px solid var(--border);
  margin:40px 56px;animation:fadeUp .6s ease both;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
.qcard{
  background:var(--bg2);padding:40px 44px;position:relative;overflow:hidden;
  transition:background .3s;
}
.qcard:hover{background:var(--bg3);}
.qcard::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  opacity:0;transition:opacity .4s;
  background:linear-gradient(90deg,transparent,var(--gold),var(--orange),transparent);
}
.qcard:hover::before{opacity:1;}
.qcard-scan{
  position:absolute;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,193,69,0.08),transparent);
  top:-100%;pointer-events:none;
}
.qcard:hover .qcard-scan{animation:scanDown 2s ease-in-out infinite;}
@keyframes scanDown{from{top:-2%;}to{top:102%;}}

.qcard-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}
.qcard-type{
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.18em;
  text-transform:uppercase;padding:4px 10px;border-radius:2px;
}
.qt-analysis {color:var(--blue);  border:1px solid rgba(0,194,255,.2); background:rgba(0,194,255,.06);}
.qt-trade    {color:var(--green); border:1px solid rgba(0,255,170,.2); background:rgba(0,255,170,.06);}
.qt-research {color:var(--purple);border:1px solid rgba(181,109,255,.2);background:rgba(181,109,255,.06);}
.qt-challenge{color:var(--gold);  border:1px solid rgba(255,193,69,.2);background:rgba(255,193,69,.06);}
.qcard-xp{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--gold);letter-spacing:.06em;font-weight:500;
}
.qcard-num{
  position:absolute;bottom:-20px;right:16px;
  font-family:'Syne',sans-serif;font-size:110px;font-weight:800;
  color:rgba(255,193,69,0.03);line-height:1;pointer-events:none;
}
.qcard:hover .qcard-num{color:rgba(255,193,69,0.055);}

.qcard-title{
  font-family:'Syne',sans-serif;font-size:20px;font-weight:700;
  color:#fff;margin-bottom:10px;letter-spacing:-.01em;
}
.qcard-desc{font-size:12.5px;font-weight:300;color:var(--muted2);line-height:1.9;margin-bottom:24px;}
.qcard-steps{margin-bottom:24px;}
.qcard-step{
  display:flex;gap:12px;align-items:flex-start;
  font-size:12px;color:var(--muted2);margin-bottom:8px;line-height:1.6;
}
.step-num{
  font-family:'JetBrains Mono',monospace;font-size:9px;
  color:var(--gold);background:rgba(255,193,69,.1);
  border:1px solid rgba(255,193,69,.2);
  width:20px;height:20px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;margin-top:1px;
}
.qcard-footer{display:flex;gap:20px;align-items:center;flex-wrap:wrap;}
.qcard-diff{display:flex;gap:3px;align-items:center;}
.qdot{width:7px;height:7px;border-radius:50%;}
.qdot.on{background:var(--gold);}
.qdot.off{background:rgba(255,193,69,.15);}
.qcard-time,.qcard-reward{
  font-family:'JetBrains Mono',monospace;font-size:9px;
  color:var(--muted2);letter-spacing:.06em;
}
.qcard-reward{color:var(--gold);}

/* ── Streaks & XP ── */
.xp-bar{
  position:relative;z-index:5;margin:0 56px;
  background:var(--bg2);border:1px solid var(--border);
  display:flex;align-items:center;gap:0;
}
.xp-item{
  flex:1;padding:24px 28px;border-right:1px solid var(--border);
  text-align:center;transition:background .2s;
}
.xp-item:last-child{border-right:none;}
.xp-item:hover{background:var(--bg3);}
.xp-val{
  font-family:'Syne',sans-serif;font-size:26px;font-weight:700;
  color:var(--gold);margin-bottom:4px;
}
.xp-lbl{font-family:'JetBrains Mono',monospace;font-size:8px;
  letter-spacing:.15em;color:var(--muted);text-transform:uppercase;}

/* ── Loading state ── */
.loading-wrap{
  position:relative;z-index:5;margin:60px 56px;
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;padding:80px 40px;
  border:1px solid var(--border);background:var(--bg2);
}
.loading-icon{font-size:40px;margin-bottom:24px;animation:spin 2s linear infinite;}
@keyframes spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
.loading-text{
  font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.2em;
  color:var(--gold);text-transform:uppercase;margin-bottom:8px;
}
.loading-sub{font-size:12px;color:var(--muted2);}

/* ── Generate button ── */
div[data-testid="stButton"] > button {
  background:rgba(255,193,69,.08) !important;
  border:1px solid rgba(255,193,69,.3) !important;
  color:var(--gold) !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important;letter-spacing:.15em !important;
  padding:14px 32px !important;border-radius:2px !important;
  text-transform:uppercase !important;width:100% !important;
  transition:all .2s !important;
}
div[data-testid="stButton"] > button:hover {
  background:rgba(255,193,69,.16) !important;
  box-shadow:0 0 30px rgba(255,193,69,.2) !important;
}

/* ── Error / empty ── */
.err-box{
  margin:0 56px 40px;padding:32px 40px;
  border:1px solid rgba(255,77,109,.2);background:rgba(255,77,109,.05);
  border-radius:2px;
}
.err-box p{font-size:13px;color:var(--muted2);line-height:1.7;}
.err-box code{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--red);background:rgba(255,77,109,.08);
  padding:2px 6px;border-radius:2px;
}
</style>

<div class="bg-grid"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav">
  <div class="nav-logo">Trade<span>Sphere</span></div>
  <div class="nav-back" onclick="history.back()">← BACK TO HOME</div>
</div>
""", unsafe_allow_html=True)

# Back button (Streamlit native)
if st.button("← Home", key="back_home"):
    st.switch_page("home.py")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-eyebrow">Section 03 — Gamified Learning</div>
  <div class="page-title">Daily <span>Quests</span></div>
  <p class="page-sub">AI-generated trading challenges refreshed every day. Complete quests to build skill, earn XP, and develop a consistent market edge.</p>
  <div class="date-badge"><div class="live-dot"></div>{TODAY}</div>
</div>
""", unsafe_allow_html=True)

# ── XP / streak bar ────────────────────────────────────────────────────────────
streak = st.session_state.get("streak", 3)
total_xp = st.session_state.get("total_xp", 870)
completed = st.session_state.get("completed_today", 1)

st.markdown(f"""
<div class="xp-bar">
  <div class="xp-item"><div class="xp-val">{total_xp}</div><div class="xp-lbl">Total XP</div></div>
  <div class="xp-item"><div class="xp-val">{streak} 🔥</div><div class="xp-lbl">Day Streak</div></div>
  <div class="xp-item"><div class="xp-val">{completed}/4</div><div class="xp-lbl">Today's Progress</div></div>
  <div class="xp-item"><div class="xp-val">820 XP</div><div class="xp-lbl">Today Available</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Gemini quest generation ────────────────────────────────────────────────────
def build_prompt():
    return f"""
You are a financial markets education AI for a platform called TradeSphere.
Today is {TODAY}.

Generate exactly 4 daily trading quests in JSON format. Each quest should be actionable, educational, and relevant to today's market environment.

Return ONLY valid JSON — no markdown, no preamble. Format:
{{
  "quests": [
    {{
      "type": "ANALYSIS" | "PAPER TRADE" | "RESEARCH" | "CHALLENGE",
      "xp": <integer 100-400>,
      "title": "<short punchy title>",
      "description": "<2-3 sentence engaging description of the quest>",
      "steps": ["<step 1>", "<step 2>", "<step 3>"],
      "difficulty": <integer 1-5>,
      "time_estimate": "<e.g. ~15 min>",
      "reward_badge": "<badge name>"
    }}
  ]
}}

Rules:
- Quest types: one ANALYSIS, one PAPER TRADE, one RESEARCH, one CHALLENGE
- CHALLENGE should be hardest (difficulty 4-5), highest XP (300-400)
- Steps should be concrete and specific to TradeSphere's modules (Price Predictor, Pattern Detector, Volatility Forecast, Paper Trading)
- Make descriptions feel exciting and market-relevant to {TODAY}
- Vary difficulty: 1-2, 2-3, 3-4, 4-5 range
"""

def difficulty_dots(level):
    dots = ""
    for i in range(5):
        cls = "on" if i < level else "off"
        dots += f'<div class="qdot {cls}"></div>'
    return dots

def type_class(qtype):
    mapping = {
        "ANALYSIS": "qt-analysis",
        "PAPER TRADE": "qt-trade",
        "RESEARCH": "qt-research",
        "CHALLENGE": "qt-challenge",
    }
    return mapping.get(qtype.upper(), "qt-analysis")

def render_quests(quests):
    html = '<div class="quests-wrap">'
    for i, q in enumerate(quests):
        qtype = q.get("type", "ANALYSIS")
        tc = type_class(qtype)
        xp = q.get("xp", 100)
        title = q.get("title", "Quest")
        desc = q.get("description", "")
        steps = q.get("steps", [])
        diff = q.get("difficulty", 2)
        time_est = q.get("time_estimate", "~20 min")
        badge = q.get("reward_badge", "Explorer")

        steps_html = ""
        for j, step in enumerate(steps):
            steps_html += f'<div class="qcard-step"><div class="step-num">{j+1}</div><span>{step}</span></div>'

        html += f"""
        <div class="qcard">
          <div class="qcard-scan"></div>
          <div class="qcard-head">
            <span class="qcard-type {tc}">{qtype}</span>
            <span class="qcard-xp">+{xp} XP</span>
          </div>
          <div class="qcard-title">{title}</div>
          <p class="qcard-desc">{desc}</p>
          <div class="qcard-steps">{steps_html}</div>
          <div class="qcard-footer">
            <div class="qcard-diff">{difficulty_dots(diff)}</div>
            <span class="qcard-time">⏱ {time_est}</span>
            <span class="qcard-reward">🏆 {badge}</span>
          </div>
          <div class="qcard-num">0{i+1}</div>
        </div>
        """
    html += "</div>"
    return html

# ── Main logic ─────────────────────────────────────────────────────────────────
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    generate = st.button("✦ GENERATE TODAY'S QUESTS WITH GEMINI", key="gen_quests")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Use cached quests for the day, or generate fresh
if generate or QUEST_CACHE_KEY not in st.session_state:
    if not GEMINI_API_KEY:
        st.markdown("""
        <div class="err-box">
          <p>⚠️ No Gemini API key found. Add <code>GEMINI_API_KEY</code> to your <code>.streamlit/secrets.toml</code> file:</p>
          <p><code>[secrets]<br>GEMINI_API_KEY = "your-key-here"</code></p>
          <p>Get your free API key at <strong>aistudio.google.com</strong></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner(""):
            st.markdown("""
            <div class="loading-wrap">
              <div class="loading-icon">✦</div>
              <div class="loading-text">Gemini is crafting your quests...</div>
              <div class="loading-sub">Analyzing today's market conditions</div>
            </div>
            """, unsafe_allow_html=True)
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(build_prompt())
                raw = response.text.strip()
                # Strip markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
                quests = data.get("quests", [])
                st.session_state[QUEST_CACHE_KEY] = quests
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse Gemini response: {e}")
            except Exception as e:
                st.error(f"Gemini API error: {e}")

# Render cached quests
if QUEST_CACHE_KEY in st.session_state:
    quests = st.session_state[QUEST_CACHE_KEY]
    st.markdown(render_quests(quests), unsafe_allow_html=True)

    # Completion checkboxes
    st.markdown('<div style="margin:0 56px 40px;display:flex;gap:16px;flex-wrap:wrap;">', unsafe_allow_html=True)
    completed_count = 0
    cols = st.columns(4)
    for i, q in enumerate(quests):
        key = f"quest_done_{i}_{datetime.date.today().isoformat()}"
        with cols[i]:
            done = st.checkbox(f"✓ Mark Quest {i+1} Complete", key=key)
            if done:
                completed_count += 1
                xp_earned = q.get("xp", 100)
    st.markdown("</div>", unsafe_allow_html=True)

    if completed_count > 0:
        st.success(f"🏆 {completed_count} quest(s) completed today! Great work.")

else:
    # Show placeholder cards before generation
    st.markdown("""
    <div class="quests-wrap" style="opacity:0.4;pointer-events:none;">
      <div class="qcard"><div class="qcard-title" style="color:var(--muted);">Quest 01</div>
        <p class="qcard-desc">Click Generate to load today's AI-powered quests.</p></div>
      <div class="qcard"><div class="qcard-title" style="color:var(--muted);">Quest 02</div>
        <p class="qcard-desc">Gemini will craft personalized market challenges.</p></div>
      <div class="qcard"><div class="qcard-title" style="color:var(--muted);">Quest 03</div>
        <p class="qcard-desc">Each quest targets a specific trading skill.</p></div>
      <div class="qcard"><div class="qcard-title" style="color:var(--muted);">Quest 04</div>
        <p class="qcard-desc">Daily refresh keeps the challenges fresh.</p></div>
    </div>
    """, unsafe_allow_html=True)