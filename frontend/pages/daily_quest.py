import streamlit as st
import google.generativeai as genai
import json, datetime

st.set_page_config(
    page_title="Daily Quest · Trade Sphere",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Gemini setup ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

TODAY      = datetime.date.today().strftime("%A, %B %d, %Y")
CACHE_KEY  = f"dq_questions_{datetime.date.today().isoformat()}"
ANSWERS_KEY = "dq_user_answers"
SUBMITTED_KEY = "dq_submitted"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

:root {
  --green:#00ffaa; --blue:#00c2ff; --red:#ff4d6d;
  --gold:#ffc145;  --purple:#b56dff; --orange:#ff7b3d;
  --bg:#03060a;    --bg2:#080d14; --bg3:#0d1520; --bg4:#111c2a;
  --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
  --text:#c8d5e8;  --muted:#3a4d62; --muted2:#5a6f85;
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

/* grid bg */
.bg-grid{
  position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:
    linear-gradient(rgba(255,193,69,0.018) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,193,69,0.018) 1px,transparent 1px);
  background-size:80px 80px;animation:gridPan 25s linear infinite;
}
@keyframes gridPan{to{background-position:80px 80px;}}
.orb{position:fixed;border-radius:50%;filter:blur(130px);pointer-events:none;z-index:0;}
.orb-1{width:600px;height:600px;top:-150px;left:-100px;background:rgba(255,193,69,0.05);}
.orb-2{width:450px;height:450px;bottom:-80px;right:-80px;background:rgba(255,123,61,0.04);}
.orb-3{width:350px;height:350px;top:40%;left:40%;background:rgba(181,109,255,0.03);}

/* nav */
.nav{
  position:relative;z-index:20;
  display:flex;justify-content:space-between;align-items:center;
  padding:18px 56px;border-bottom:1px solid var(--border);
  background:rgba(3,6,10,0.85);backdrop-filter:blur(20px);
}
.nav-logo{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;
  letter-spacing:.06em;color:#fff;text-transform:uppercase;}
.nav-logo span{color:var(--green);}
.nav-right{display:flex;align-items:center;gap:20px;}
.nav-badge-date{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.12em;
  color:var(--muted2);text-transform:uppercase;
}

/* page header */
.page-header{
  position:relative;z-index:5;padding:56px 56px 44px;
  border-bottom:1px solid var(--border);
  animation:fadeUp .7s ease both;
}
.page-eyebrow{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.25em;
  text-transform:uppercase;color:var(--gold);margin-bottom:14px;
  display:flex;align-items:center;gap:12px;
}
.page-eyebrow::before{content:'';width:28px;height:1px;
  background:linear-gradient(to right,transparent,var(--gold));}
.page-title{
  font-family:'Syne',sans-serif;font-size:clamp(28px,4.5vw,56px);
  font-weight:800;color:#fff;letter-spacing:-.02em;margin-bottom:10px;
}
.page-title span{color:var(--gold);}
.page-sub{font-size:13.5px;font-weight:300;color:var(--muted2);max-width:520px;line-height:1.85;}
.live-dot{width:6px;height:6px;border-radius:50%;background:var(--gold);
  animation:pulse 2s infinite;display:inline-block;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(255,193,69,.5);}70%{box-shadow:0 0 0 8px rgba(255,193,69,0);}}

/* progress bar row */
.progress-wrap{
  position:relative;z-index:5;margin:0;
  display:flex;align-items:stretch;gap:0;
  background:var(--bg2);border-bottom:1px solid var(--border);
}
.prog-item{
  flex:1;padding:20px 28px;border-right:1px solid var(--border);text-align:center;
}
.prog-item:last-child{border-right:none;}
.prog-val{
  font-family:'Syne',sans-serif;font-size:22px;font-weight:700;
  color:var(--gold);margin-bottom:3px;
}
.prog-lbl{font-family:'JetBrains Mono',monospace;font-size:8px;
  letter-spacing:.16em;color:var(--muted);text-transform:uppercase;}
.prog-bar-wrap{
  position:relative;z-index:5;height:3px;
  background:rgba(255,255,255,.04);margin:0;
}
.prog-bar-fill{
  height:100%;background:linear-gradient(90deg,var(--gold),var(--orange));
  transition:width .5s ease;
}

/* question cards */
.q-wrap{
  position:relative;z-index:5;
  padding:40px 56px 20px;
  animation:fadeUp .5s ease both;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}

.q-card{
  background:var(--bg2);border:1px solid var(--border);
  padding:32px 36px;margin-bottom:16px;
  position:relative;overflow:hidden;transition:border-color .3s,background .3s;
}
.q-card:hover{background:var(--bg3);border-color:var(--border2);}
.q-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--gold),var(--orange),transparent);
  opacity:0;transition:opacity .3s;
}
.q-card:hover::before{opacity:1;}

/* correct / wrong states after submit */
.q-card.correct{border-color:rgba(0,255,170,.3);background:rgba(0,255,170,.03);}
.q-card.correct::before{opacity:1;background:linear-gradient(90deg,transparent,var(--green),transparent);}
.q-card.wrong{border-color:rgba(255,77,109,.3);background:rgba(255,77,109,.03);}
.q-card.wrong::before{opacity:1;background:linear-gradient(90deg,transparent,var(--red),transparent);}
.q-card.skipped{border-color:rgba(255,123,61,.25);background:rgba(255,123,61,.02);}

.q-num{
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.2em;
  color:var(--gold);text-transform:uppercase;margin-bottom:10px;
}
.q-text{
  font-family:'Space Grotesk',sans-serif;font-size:15.5px;font-weight:500;
  color:#fff;line-height:1.6;margin-bottom:20px;
}
.q-result-badge{
  display:inline-flex;align-items:center;gap:6px;
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.14em;
  padding:4px 10px;border-radius:2px;margin-bottom:14px;text-transform:uppercase;
}
.badge-correct{color:var(--green);border:1px solid rgba(0,255,170,.25);background:rgba(0,255,170,.07);}
.badge-wrong{color:var(--red);border:1px solid rgba(255,77,109,.25);background:rgba(255,77,109,.07);}
.badge-skipped{color:var(--orange);border:1px solid rgba(255,123,61,.25);background:rgba(255,123,61,.07);}
.correct-answer-note{
  font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--green);
  margin-top:10px;padding:8px 12px;
  border-left:2px solid rgba(0,255,170,.4);background:rgba(0,255,170,.04);
}

/* radio overrides */
div[data-testid="stRadio"] label{
  font-size:13px !important;color:var(--text) !important;
  padding:2px 0 !important;cursor:pointer !important;
}
div[data-testid="stRadio"] > div{gap:4px !important;}

/* submit / retry buttons */
.btn-row{
  position:relative;z-index:5;
  padding:8px 56px 48px;display:flex;gap:16px;
}
div[data-testid="stButton"] > button{
  background:rgba(255,193,69,.08) !important;
  border:1px solid rgba(255,193,69,.3) !important;
  color:var(--gold) !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:10px !important;letter-spacing:.15em !important;
  padding:13px 32px !important;border-radius:2px !important;
  text-transform:uppercase !important;transition:all .2s !important;
}
div[data-testid="stButton"] > button:hover{
  background:rgba(255,193,69,.18) !important;
  box-shadow:0 0 28px rgba(255,193,69,.2) !important;
}

/* score screen */
.score-wrap{
  position:relative;z-index:5;
  margin:48px 56px;
  animation:fadeUp .6s ease both;
}
.score-hero{
  background:var(--bg2);border:1px solid var(--border);
  padding:60px 40px;text-align:center;margin-bottom:1px;
  position:relative;overflow:hidden;
}
.score-hero::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,transparent,var(--gold),var(--orange),var(--purple),transparent);
}
.score-trophy{font-size:56px;margin-bottom:24px;display:block;}
.score-label{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.25em;
  color:var(--muted);text-transform:uppercase;margin-bottom:14px;
}
.score-big{
  font-family:'Syne',sans-serif;font-size:clamp(56px,10vw,100px);
  font-weight:800;line-height:1;margin-bottom:8px;
}
.score-grade{
  font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.2em;
  padding:6px 18px;border-radius:2px;text-transform:uppercase;
  display:inline-block;margin-bottom:20px;
}
.score-message{font-size:14px;color:var(--muted2);font-weight:300;line-height:1.7;}

.score-stats{
  display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
  background:var(--border);border:1px solid var(--border);
  margin-bottom:32px;
}
.score-stat{
  background:var(--bg2);padding:28px 20px;text-align:center;
  transition:background .2s;
}
.score-stat:hover{background:var(--bg3);}
.ss-val{
  font-family:'Syne',sans-serif;font-size:28px;font-weight:700;
  margin-bottom:4px;
}
.ss-lbl{font-family:'JetBrains Mono',monospace;font-size:8px;
  letter-spacing:.16em;color:var(--muted);text-transform:uppercase;}

/* loading */
.loading-wrap{
  position:relative;z-index:5;margin:60px 56px;
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;padding:80px 40px;
  border:1px solid var(--border);background:var(--bg2);
}
.loading-icon{font-size:36px;margin-bottom:20px;animation:spin 2s linear infinite;}
@keyframes spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
.loading-text{
  font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.2em;
  color:var(--gold);text-transform:uppercase;margin-bottom:8px;
}
.loading-sub{font-size:12px;color:var(--muted2);}

/* error */
.err-box{
  margin:0 56px 40px;padding:28px 36px;
  border:1px solid rgba(255,77,109,.2);background:rgba(255,77,109,.04);
}
.err-box p{font-size:13px;color:var(--muted2);line-height:1.7;margin-bottom:8px;}
.err-box code{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--red);background:rgba(255,77,109,.08);padding:2px 6px;
}

/* section divider */
.section-sep{
  position:relative;z-index:5;
  display:flex;align-items:center;gap:20px;
  padding:0 56px;margin:32px 0 0;
}
.section-sep span{
  font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.2em;
  color:var(--muted);text-transform:uppercase;white-space:nowrap;
}
.section-sep::after{content:'';flex:1;height:1px;background:linear-gradient(to right,var(--border),transparent);}
</style>

<div class="bg-grid"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
""", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="nav">
  <div class="nav-logo">Trade<span>Sphere</span></div>
  <div class="nav-right">
    <div class="nav-badge-date">✦ {datetime.date.today().strftime("%b %d, %Y")}</div>
  </div>
</div>
""", unsafe_allow_html=True)

col_back, _ = st.columns([1, 8])
with col_back:
    if st.button("← HOME", key="back_home"):
        st.switch_page("home.py")

# ── Gemini prompt ──────────────────────────────────────────────────────────────
def build_prompt():
    return f"""
You are a financial markets education AI for TradeSphere.
Today is {TODAY}.

Generate exactly 10 multiple-choice questions about trading, investing, and financial markets.
Mix difficulty: 3 easy, 4 medium, 3 hard.
Topics: technical analysis, fundamental analysis, options, risk management, market mechanics, trading psychology, chart patterns, economic indicators.

Return ONLY valid JSON, no markdown, no preamble:
{{
  "questions": [
    {{
      "question": "<clear question text>",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "<1-sentence explanation of why the answer is correct>"
    }}
  ]
}}

Rules:
- answer must be exactly one of: "A", "B", "C", "D"
- options must always have exactly 4 items starting with A. B. C. D.
- questions should be practical and relevant to today's market context
- vary topics, don't repeat similar questions
- explanations must be concise (max 20 words)
"""

# ── Generate questions ─────────────────────────────────────────────────────────
def generate_questions():
    if not GEMINI_API_KEY:
        return None, "no_key"
    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content(build_prompt())
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return data.get("questions", []), None
    except json.JSONDecodeError as e:
        return None, f"parse_error: {e}"
    except Exception as e:
        return None, f"api_error: {e}"

# ── Score helpers ──────────────────────────────────────────────────────────────
def grade(score, total):
    pct = score / total * 100
    if pct == 100:  return "S",  "var(--gold)",   "Perfect. Legendary trader energy. 🏆"
    if pct >= 80:   return "A",  "var(--green)",  "Excellent! Sharp market instincts. 🎯"
    if pct >= 60:   return "B",  "var(--blue)",   "Solid. Keep refining your edge. 📈"
    if pct >= 40:   return "C",  "var(--orange)", "Decent. More study needed. 📚"
    return              "D",  "var(--red)",    "Rough session. Review the basics. 💪"

def trophy(score, total):
    pct = score / total * 100
    if pct == 100: return "🏆"
    if pct >= 80:  return "🥇"
    if pct >= 60:  return "🥈"
    if pct >= 40:  return "🥉"
    return "📉"

# ── State init ─────────────────────────────────────────────────────────────────
if ANSWERS_KEY not in st.session_state:
    st.session_state[ANSWERS_KEY] = {}
if SUBMITTED_KEY not in st.session_state:
    st.session_state[SUBMITTED_KEY] = False

submitted = st.session_state[SUBMITTED_KEY]
questions = st.session_state.get(CACHE_KEY, None)

# ── Page header ────────────────────────────────────────────────────────────────
answered_count = len(st.session_state[ANSWERS_KEY])
total_q = len(questions) if questions else 10

st.markdown(f"""
<div class="page-header">
  <div class="page-eyebrow">Module 05/05 — Gamified Learning</div>
  <div class="page-title">Daily <span>Quest</span></div>
  <p class="page-sub">10 AI-generated trading questions, refreshed every day. Answer all MCQs and see how sharp your market knowledge really is.</p>
</div>
""", unsafe_allow_html=True)

# ── Progress bar (only during quiz) ───────────────────────────────────────────
if questions and not submitted:
    pct_done = int(answered_count / total_q * 100)
    st.markdown(f"""
    <div class="progress-wrap">
      <div class="prog-item"><div class="prog-val">{answered_count}/{total_q}</div><div class="prog-lbl">Answered</div></div>
      <div class="prog-item"><div class="prog-val">{total_q - answered_count}</div><div class="prog-lbl">Remaining</div></div>
      <div class="prog-item"><div class="prog-val">{pct_done}%</div><div class="prog-lbl">Progress</div></div>
    </div>
    <div class="prog-bar-wrap">
      <div class="prog-bar-fill" style="width:{pct_done}%;"></div>
    </div>
    """, unsafe_allow_html=True)

# ── Generate button (first load) ───────────────────────────────────────────────
if questions is None:
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✦ GENERATE TODAY'S QUESTIONS", key="gen_btn"):
            with st.spinner(""):
                st.markdown("""
                <div class="loading-wrap">
                  <div class="loading-icon">✦</div>
                  <div class="loading-text">Gemini is crafting your questions...</div>
                  <div class="loading-sub">Pulling from today's market context</div>
                </div>
                """, unsafe_allow_html=True)
                qs, err = generate_questions()
                if err == "no_key":
                    st.markdown("""
                    <div class="err-box">
                      <p>⚠️ No Gemini API key found. Add to <code>.streamlit/secrets.toml</code>:</p>
                      <p><code>GEMINI_API_KEY = "your-key-here"</code></p>
                      <p>Get a free key at <strong>aistudio.google.com</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                elif err:
                    st.error(f"Error: {err}")
                elif qs:
                    st.session_state[CACHE_KEY] = qs
                    st.session_state[ANSWERS_KEY] = {}
                    st.session_state[SUBMITTED_KEY] = False
                    st.rerun()

# ── Score screen ───────────────────────────────────────────────────────────────
elif submitted and questions:
    user_ans = st.session_state[ANSWERS_KEY]
    score = sum(
        1 for i, q in enumerate(questions)
        if user_ans.get(i, "").startswith(q["answer"] + ".")
        or user_ans.get(i, "") == q["answer"]
    )
    total = len(questions)
    wrong = sum(1 for i in range(total) if i in user_ans and not (
        user_ans[i].startswith(questions[i]["answer"] + ".") or user_ans[i] == questions[i]["answer"]
    ))
    skipped = total - len(user_ans)
    g_letter, g_color, g_msg = grade(score, total)
    trophyIcon = trophy(score, total)
    xp_earned = score * 50

    st.markdown(f"""
    <div class="score-wrap">
      <div class="score-hero">
        <span class="score-trophy">{trophyIcon}</span>
        <div class="score-label">Quest Complete · {TODAY}</div>
        <div class="score-big" style="color:{g_color};">{score}<span style="font-size:40%;color:var(--muted2);">/{total}</span></div>
        <div class="score-grade" style="color:{g_color};border:1px solid {g_color}33;background:{g_color}11;">
          GRADE {g_letter} &nbsp;·&nbsp; +{xp_earned} XP
        </div>
        <div class="score-message">{g_msg}</div>
      </div>
      <div class="score-stats">
        <div class="score-stat"><div class="ss-val" style="color:var(--green);">{score}</div><div class="ss-lbl">Correct</div></div>
        <div class="score-stat"><div class="ss-val" style="color:var(--red);">{wrong}</div><div class="ss-lbl">Wrong</div></div>
        <div class="score-stat"><div class="ss-val" style="color:var(--orange);">{skipped}</div><div class="ss-lbl">Skipped</div></div>
        <div class="score-stat"><div class="ss-val" style="color:var(--gold);">{xp_earned}</div><div class="ss-lbl">XP Earned</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Review section
    st.markdown('<div class="section-sep"><span>◈ Review Answers</span></div>', unsafe_allow_html=True)
    st.markdown("<div class='q-wrap'>", unsafe_allow_html=True)
    for i, q in enumerate(questions):
        user_choice = user_ans.get(i, None)
        correct_letter = q["answer"]
        correct_option = next((o for o in q["options"] if o.startswith(correct_letter + ".")), correct_letter)

        if user_choice is None:
            card_cls = "skipped"
            badge_html = '<span class="q-result-badge badge-skipped">⊘ SKIPPED</span>'
        elif user_choice.startswith(correct_letter + ".") or user_choice == correct_letter:
            card_cls = "correct"
            badge_html = '<span class="q-result-badge badge-correct">✓ CORRECT</span>'
        else:
            card_cls = "wrong"
            badge_html = '<span class="q-result-badge badge-wrong">✗ WRONG</span>'

        explanation = q.get("explanation", "")
        show_answer = "" if card_cls == "correct" else f'<div class="correct-answer-note">✓ Correct answer: {correct_option}</div>'

        st.markdown(f"""
        <div class="q-card {card_cls}">
          <div class="q-num">Question {i+1:02d} / 10</div>
          {badge_html}
          <div class="q-text">{q['question']}</div>
          {show_answer}
          {"" if not explanation else f'<div style="font-size:11.5px;color:var(--muted2);margin-top:10px;font-style:italic;">{explanation}</div>'}
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Retry / Home buttons
    st.markdown("<div class='btn-row'>", unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns([1, 1, 4])
    with col_r1:
        if st.button("↺ RETRY TODAY", key="retry_btn"):
            st.session_state[ANSWERS_KEY] = {}
            st.session_state[SUBMITTED_KEY] = False
            st.rerun()
    with col_r2:
        if st.button("← HOME", key="home_btn"):
            st.switch_page("home.py")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Quiz screen ────────────────────────────────────────────────────────────────
elif questions:
    st.markdown("<div class='q-wrap'>", unsafe_allow_html=True)
    for i, q in enumerate(questions):
        current_answer = st.session_state[ANSWERS_KEY].get(i, None)
        st.markdown(f"""
        <div class="q-card">
          <div class="q-num">Question {i+1:02d} / 10</div>
          <div class="q-text">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        options = q.get("options", [])
        choice = st.radio(
            label=f"q{i}",
            options=options,
            index=options.index(current_answer) if current_answer in options else None,
            key=f"radio_{i}",
            label_visibility="collapsed"
        )
        if choice:
            st.session_state[ANSWERS_KEY][i] = choice

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Submit button
    answered_now = len(st.session_state[ANSWERS_KEY])
    st.markdown("<div class='btn-row'>", unsafe_allow_html=True)
    col_s1, col_s2, col_s3 = st.columns([1, 1, 4])
    with col_s1:
        label = f"✦ SUBMIT ({answered_now}/10)" if answered_now < 10 else "✦ SUBMIT ALL ANSWERS"
        if st.button(label, key="submit_btn"):
            st.session_state[SUBMITTED_KEY] = True
            st.rerun()
    with col_s2:
        if st.button("↺ RESET", key="reset_btn"):
            st.session_state[ANSWERS_KEY] = {}
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)