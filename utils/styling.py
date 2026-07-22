"""SaaS-quality dark theme — SonarQube/CodeClimate level."""
import streamlit as st

# ── Fix: prevent HTML from rendering as a literal code block ───────
# Every st.markdown(f"""...""", unsafe_allow_html=True) call in this
# project is naturally indented to match the surrounding Python code,
# and some build HTML by nesting one f-string inside another. Two
# Markdown parsing rules turn that into visible "<div ...>" text
# instead of a rendered card/badge/bar:
#   1. Any line indented 4+ spaces is read as a preformatted code
#      block, which overrides HTML parsing entirely.
#   2. A blank line inside an HTML block CLOSES that block early —
#      so content nested via f-string interpolation (which often
#      leaves a blank line where the inner string started) fragments
#      the HTML and confuses the parser.
# Patching st.markdown once here strips leading whitespace AND blank
# lines from HTML content before it reaches the renderer, so this
# can't happen anywhere in the app — not just in one spot.
if not getattr(st.markdown, "_dedents_html", False):
    _original_markdown = st.markdown

    def _markdown_dedented(body, *args, **kwargs):
        if isinstance(body, str) and kwargs.get("unsafe_allow_html"):
            lines = [line.strip() for line in body.splitlines()]
            body = "\n".join(line for line in lines if line)
        return _original_markdown(body, *args, **kwargs)

    _markdown_dedented._dedents_html = True
    st.markdown = _markdown_dedented


def apply_custom_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:        #070a10;
  --bg2:       #0c0f18;
  --bg3:       #111520;
  --bg4:       #161b27;
  --card:      #0f1319;
  --card2:     #141920;
  --border:    #1a2035;
  --border2:   #212840;
  --accent:    #6366f1;
  --accent2:   #818cf8;
  --accent3:   #a5b4fc;
  --adim:      rgba(99,102,241,.08);
  --aglow:     rgba(99,102,241,.18);
  --green:     #10b981;
  --gdim:      rgba(16,185,129,.08);
  --teal:      #14b8a6;
  --yellow:    #f59e0b;
  --ydim:      rgba(245,158,11,.08);
  --orange:    #f97316;
  --odim:      rgba(249,115,22,.08);
  --red:       #ef4444;
  --rdim:      rgba(239,68,68,.08);
  --purple:    #a855f7;
  --pdim:      rgba(168,85,247,.08);
  --sky:       #0ea5e9;
  --sdim:      rgba(14,165,233,.08);
  --t1:        #f0f4ff;
  --t2:        #8892a4;
  --t3:        #4a5568;
  --t4:        #2d3748;
  --mono:      'JetBrains Mono', monospace;
  --sans:      'Inter', sans-serif;
  --r:         12px;
  --rs:        8px;
  --rx:        16px;
  --shadow:    0 4px 24px rgba(0,0,0,.35);
  --shadow2:   0 8px 40px rgba(0,0,0,.45);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
  font-family: var(--sans) !important;
  background: var(--bg) !important;
  color: var(--t1) !important;
  -webkit-font-smoothing: antialiased;
}
.stApp { background: var(--bg) !important; }
.block-container { padding: 0 2rem 3rem !important; max-width: 1400px !important; }
#MainMenu, footer, .stDeployButton { display: none !important; }

/* The header contains the sidebar expand/collapse button — keep it,
   just strip the background so it doesn't look like Streamlit chrome */
[data-testid="stHeader"] {
  background: transparent !important;
  height: 2.75rem !important;
}

/* Hide only the specific unwanted toolbar chrome — NOT the whole
   toolbar, because the sidebar expand arrow (stExpandSidebarButton)
   lives inside that same toolbar container */
[data-testid="stMainMenu"],
[data-testid="stMainMenuButton"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stToolbarActions"] { display: none !important; }

/* Force the sidebar expand/collapse buttons to always be visible and
   readable, with their own boxed background so they're easy to spot
   regardless of icon color */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 999999 !important;
  background: var(--card) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
}
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapseButton"] * {
  color: var(--t1) !important;
  fill: var(--t1) !important;
}

/* ─── Scrollbar ──────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--t3); }

/* ─── Sidebar ────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
  min-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* ─── Tabs ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
  padding: 4px !important;
  gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--t3) !important;
  border-radius: var(--rs) !important;
  font-family: var(--sans) !important;
  font-weight: 500 !important;
  font-size: 0.83rem !important;
  padding: 0.48rem 1.2rem !important;
  border: none !important;
  transition: all 0.18s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--t2) !important; background: var(--bg4) !important; }
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: 0 0 16px var(--aglow) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.75rem !important; }

/* ─── Buttons ────────────────────────────────────── */
.stButton > button {
  font-family: var(--sans) !important;
  font-weight: 500 !important;
  font-size: 0.82rem !important;
  border-radius: var(--rs) !important;
  transition: all 0.18s ease !important;
  border: 1px solid var(--border2) !important;
  background: var(--bg4) !important;
  color: var(--t2) !important;
  padding: 0.42rem 1rem !important;
}
.stButton > button:hover {
  border-color: var(--accent) !important;
  color: var(--t1) !important;
  background: var(--adim) !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), #7c3aed) !important;
  border-color: transparent !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 14px var(--aglow) !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px var(--aglow) !important;
  filter: brightness(1.1) !important;
}

/* ─── Download button ────────────────────────────── */
.stDownloadButton > button {
  font-family: var(--sans) !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  border-radius: var(--rs) !important;
  border: 1px solid var(--border2) !important;
  background: var(--bg4) !important;
  color: var(--t2) !important;
  transition: all 0.18s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--green) !important;
  color: var(--green) !important;
  transform: translateY(-1px) !important;
}

/* ─── Text inputs ────────────────────────────────── */
.stTextInput > div > div > input {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--rs) !important;
  color: var(--t1) !important;
  font-family: var(--mono) !important;
  font-size: 0.83rem !important;
  padding: 0.62rem 1rem !important;
  transition: all 0.18s !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--aglow) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--t3) !important; }
.stTextInput label { display: none !important; }

/* ─── Selectbox ──────────────────────────────────── */
.stSelectbox label { display: none !important; }
.stSelectbox [data-baseweb="select"] > div {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--rs) !important;
  color: var(--t1) !important;
  font-size: 0.82rem !important;
}

/* ─── File uploader ──────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--bg3) !important;
  border: 1.5px dashed var(--border2) !important;
  border-radius: var(--r) !important;
  padding: 1.2rem !important;
  transition: border-color 0.18s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
[data-testid="stFileUploader"] label { color: var(--t2) !important; font-size: 0.82rem !important; }

/* ─── Expander ───────────────────────────────────── */
.streamlit-expanderHeader {
  background: var(--card2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--rs) !important;
  color: var(--t1) !important;
  font-family: var(--sans) !important;
  font-size: 0.84rem !important;
  font-weight: 500 !important;
  transition: all 0.18s !important;
}
.streamlit-expanderHeader:hover { border-color: var(--border2) !important; background: var(--bg4) !important; }
.streamlit-expanderContent {
  background: var(--card2) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--rs) var(--rs) !important;
}

/* ─── Progress ───────────────────────────────────── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), var(--purple), var(--teal)) !important;
  border-radius: 4px !important;
  transition: width 0.4s ease !important;
}
.stProgress > div > div { background: var(--bg3) !important; border-radius: 4px !important; height: 4px !important; }

/* ─── Code blocks ────────────────────────────────── */
.stCodeBlock { border-radius: var(--r) !important; overflow: hidden !important; }
.stCodeBlock > div { border-radius: var(--r) !important; border: 1px solid var(--border) !important; }
pre { font-family: var(--mono) !important; font-size: 0.77rem !important; line-height: 1.65 !important; }

/* ─── Plotly charts ──────────────────────────────── */
.js-plotly-plot { border-radius: var(--r) !important; }

/* ══════════════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════════════ */

/* ── Topbar ──────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 1.25rem;
  margin-bottom: 0.25rem;
  border-bottom: 1px solid var(--border);
}
.topbar-brand { display: flex; align-items: center; gap: 0.7rem; }
.topbar-icon {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  box-shadow: 0 4px 12px var(--aglow);
}
.topbar-title { font-size: 1rem; font-weight: 700; color: var(--t1); letter-spacing: -0.02em; }
.topbar-sub   { font-size: 0.65rem; color: var(--t3); font-family: var(--mono); }
.topbar-right { display: flex; align-items: center; gap: 0.6rem; }
.topbar-pill {
  font-size: 0.67rem; font-weight: 600; font-family: var(--mono);
  padding: 3px 10px; border-radius: 20px;
  background: var(--gdim); color: var(--green);
  border: 1px solid rgba(16,185,129,.2);
}
.topbar-pill-v {
  font-size: 0.67rem; font-weight: 600; font-family: var(--mono);
  padding: 3px 10px; border-radius: 20px;
  background: var(--adim); color: var(--accent2);
  border: 1px solid rgba(99,102,241,.2);
}

/* ── Hero ────────────────────────────────────────── */
.hero-wrap {
  position: relative;
  padding: 4rem 2rem 3rem;
  text-align: center;
  overflow: hidden;
}
.hero-glow-1 {
  position: absolute; top: -60px; left: 20%; width: 500px; height: 300px;
  background: radial-gradient(ellipse, rgba(99,102,241,.12) 0%, transparent 70%);
  pointer-events: none;
}
.hero-glow-2 {
  position: absolute; top: -40px; right: 15%; width: 400px; height: 250px;
  background: radial-gradient(ellipse, rgba(168,85,247,.08) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em;
  text-transform: uppercase; font-family: var(--mono);
  padding: 5px 14px; border-radius: 20px;
  background: var(--adim); color: var(--accent2);
  border: 1px solid rgba(99,102,241,.22);
  margin-bottom: 1.4rem;
}
.hero-badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); display: inline-block; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.85)} }

.hero-title {
  font-size: clamp(2rem, 4vw, 3rem) !important;
  font-weight: 900 !important;
  line-height: 1.1 !important;
  letter-spacing: -0.04em !important;
  color: var(--t1) !important;
  margin: 0 0 1.1rem !important;
}
.hero-title .hl {
  background: linear-gradient(135deg, var(--accent2), var(--purple), var(--teal));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  font-size: 1.02rem;
  color: var(--t2);
  line-height: 1.7;
  max-width: 580px;
  margin: 0 auto 2.5rem;
  font-weight: 400;
}

/* ── Input card ──────────────────────────────────── */
.input-card {
  background: var(--card);
  border: 1px solid var(--border2);
  border-radius: var(--rx);
  padding: 1.75rem;
  max-width: 620px;
  margin: 0 auto;
  box-shadow: var(--shadow);
  position: relative;
}
.input-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), var(--purple), transparent);
  border-radius: var(--rx) var(--rx) 0 0;
}
.inp-lbl {
  font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--t3); margin-bottom: 0.45rem;
}
.inp-divider {
  display: flex; align-items: center; gap: 0.75rem;
  color: var(--t4); font-size: 0.7rem;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin: 1.1rem 0;
}
.inp-divider::before, .inp-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}
.inp-hint { font-size: 0.7rem; color: var(--t3); font-family: var(--mono); margin-top: 0.3rem; }

/* ── Feature cards ───────────────────────────────── */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.85rem;
  margin-top: 2.5rem;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
}
.feature-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.4rem 1.2rem;
  text-align: center;
  transition: all 0.22s ease;
  position: relative;
  overflow: hidden;
  cursor: default;
}
.feature-card::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(135deg, var(--adim), transparent);
  opacity: 0;
  transition: opacity 0.22s;
}
.feature-card:hover { border-color: var(--accent); transform: translateY(-3px); box-shadow: 0 8px 28px var(--aglow); }
.feature-card:hover::before { opacity: 1; }
.fc-icon {
  width: 44px; height: 44px; margin: 0 auto 0.9rem;
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem;
}
.fc-icon-bug    { background: linear-gradient(135deg,#ef444422,#ef444408); }
.fc-icon-sec    { background: linear-gradient(135deg,#f9731622,#f9731608); }
.fc-icon-perf   { background: linear-gradient(135deg,#6366f122,#6366f108); }
.fc-icon-qual   { background: linear-gradient(135deg,#10b98122,#10b98108); }
.fc-title { font-size: 0.85rem; font-weight: 700; color: var(--t1); margin-bottom: 0.35rem; }
.fc-desc  { font-size: 0.73rem; color: var(--t3); line-height: 1.5; }

/* ── Trusted-by strip ────────────────────────────── */
.trusted-strip {
  display: flex; align-items: center; justify-content: center;
  gap: 1.5rem; margin-top: 2rem;
  font-size: 0.7rem; color: var(--t4);
}
.trusted-tag {
  padding: 3px 10px; border-radius: 5px;
  background: var(--bg3); border: 1px solid var(--border);
  font-family: var(--mono); font-size: 0.68rem; color: var(--t3);
}

/* ── Metrics row ─────────────────────────────────── */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.7rem;
  margin-bottom: 1.25rem;
}
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.1rem 0.9rem;
  text-align: center;
  transition: all 0.22s ease;
  position: relative;
  overflow: hidden;
  cursor: default;
}
.metric-card:hover { transform: translateY(-2px); border-color: var(--border2); box-shadow: var(--shadow); }
.metric-card::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  border-radius: 0 0 var(--r) var(--r);
}
.mc-files   ::after { background: var(--accent); }
.mc-total   .metric-card::after, .mc-total::after   { background: var(--purple); }
.mc-critical::after { background: var(--red); }
.mc-high    ::after { background: var(--orange); }
.mc-medium  ::after { background: var(--yellow); }
.mc-low     ::after { background: var(--green); }
/* simpler top-border approach */
.mc-files    { border-top: 2px solid var(--accent) !important; }
.mc-total    { border-top: 2px solid var(--purple) !important; }
.mc-critical { border-top: 2px solid var(--red) !important; }
.mc-high     { border-top: 2px solid var(--orange) !important; }
.mc-medium   { border-top: 2px solid var(--yellow) !important; }
.mc-low      { border-top: 2px solid var(--green) !important; }

.metric-val {
  font-family: var(--mono);
  font-size: 1.9rem; font-weight: 700; line-height: 1;
  margin-bottom: 0.25rem; letter-spacing: -0.03em;
}
.mc-files    .metric-val { color: var(--accent); }
.mc-total    .metric-val { color: var(--purple); }
.mc-critical .metric-val { color: var(--red); }
.mc-high     .metric-val { color: var(--orange); }
.mc-medium   .metric-val { color: var(--yellow); }
.mc-low      .metric-val { color: var(--green); }
.metric-lbl { font-size: 0.63rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); }

/* ── Score cards ─────────────────────────────────── */
.score-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.7rem;
  margin-bottom: 1.25rem;
}
.score-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.1rem;
  transition: all 0.22s;
  position: relative; overflow: hidden;
}
.score-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); border-color: var(--border2); }
.score-title { font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); margin-bottom: 0.5rem; }
.score-val-row { display: flex; align-items: flex-end; gap: 0.5rem; }
.score-val {
  font-family: var(--mono);
  font-size: 1.7rem; font-weight: 700; line-height: 1; letter-spacing: -0.03em;
}
.score-grade {
  font-size: 0.72rem; font-weight: 700; padding: 2px 7px;
  border-radius: 5px; margin-bottom: 0.15rem;
  font-family: var(--mono);
}
.grade-a { background: var(--gdim); color: var(--green); }
.grade-b { background: var(--sdim); color: var(--sky); }
.grade-c { background: var(--ydim); color: var(--yellow); }
.grade-d { background: var(--odim); color: var(--orange); }
.grade-f { background: var(--rdim); color: var(--red); }
.score-bar-track { height: 3px; background: var(--bg3); border-radius: 2px; margin-top: 0.65rem; overflow: hidden; }
.score-bar-fill  { height: 100%; border-radius: 2px; transition: width 0.6s ease; }

/* ── Repo bar ─────────────────────────────────────── */
.repo-bar {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 0.85rem 1.2rem;
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); margin-bottom: 1.1rem;
}
.repo-bar-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
.repo-bar-name { font-weight: 600; font-size: 0.92rem; color: var(--t1); }
.repo-bar-meta { font-family: var(--mono); font-size: 0.7rem; color: var(--t3); margin-left: 0.2rem; }
.repo-tag { margin-left: auto; font-size: 0.67rem; font-weight: 600; font-family: var(--mono); padding: 2px 9px; border-radius: 20px; background: var(--gdim); color: var(--green); border: 1px solid rgba(16,185,129,.2); }

/* ── Action bar ───────────────────────────────────── */
.action-bar { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.25rem; }

/* ── Insights grid ────────────────────────────────── */
.insights-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem; margin-bottom: 1.1rem;
}
.insight-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); padding: 1rem 1.1rem;
  transition: all 0.2s;
}
.insight-card:hover { border-color: var(--border2); transform: translateY(-1px); }
.ins-lbl { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); margin-bottom: 0.35rem; }
.ins-val { font-family: var(--mono); font-size: 1.1rem; font-weight: 700; color: var(--t1); }
.ins-sub { font-size: 0.7rem; color: var(--t3); margin-top: 0.15rem; }

/* ── Chart card ───────────────────────────────────── */
.chart-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); padding: 1.25rem;
  margin-bottom: 0.75rem;
}
.chart-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); margin-bottom: 0.9rem; }

/* ── Summary card ─────────────────────────────────── */
.sum-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--r); padding: 1.25rem; height: 100%; }
.sec-hd { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--t3); margin-bottom: 0.8rem; padding-bottom: 0.55rem; border-bottom: 1px solid var(--border); }

/* ── Bar chart ────────────────────────────────────── */
.bar-row { display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.5rem; }
.bar-lbl { width: 60px; font-size: 0.68rem; color: var(--t3); text-align: right; font-family: var(--mono); }
.bar-track { flex: 1; height: 7px; background: var(--bg3); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.bar-cnt { width: 22px; font-size: 0.68rem; color: var(--t2); font-family: var(--mono); }

/* ── Issue cards ──────────────────────────────────── */
.file-grp {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.6rem 0.9rem;
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--rs); margin: 1.1rem 0 0.5rem;
}
.file-grp-name { font-family: var(--mono); font-size: 0.78rem; font-weight: 600; color: var(--t1); flex: 1; }
.file-grp-cnt  { font-family: var(--mono); font-size: 0.67rem; color: var(--t3); }

.badge { display: inline-block; font-family: var(--mono); font-size: 0.63rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 2px 8px; border-radius: 4px; }
.b-critical { background: var(--rdim); color: var(--red); border: 1px solid rgba(239,68,68,.2); }
.b-high     { background: var(--odim); color: var(--orange); border: 1px solid rgba(249,115,22,.2); }
.b-medium   { background: var(--ydim); color: var(--yellow); border: 1px solid rgba(245,158,11,.2); }
.b-low      { background: var(--gdim); color: var(--green); border: 1px solid rgba(16,185,129,.2); }

.fix-box { background: var(--bg3); border-left: 2px solid var(--green); border-radius: 0 var(--rs) var(--rs) 0; padding: 0.75rem 1rem; margin-top: 0.65rem; }
.fix-lbl { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--green); margin-bottom: 0.3rem; font-family: var(--mono); }
.fix-txt { font-size: 0.8rem; color: var(--t2); line-height: 1.55; }

.err-box { background: var(--rdim); border: 1px solid rgba(239,68,68,.18); border-radius: var(--rs); padding: 0.9rem 1rem; }
.err-title { font-size: 0.7rem; font-weight: 700; color: var(--red); font-family: var(--mono); margin-bottom: 0.35rem; text-transform: uppercase; }
.err-msg { font-size: 0.8rem; color: var(--t2); line-height: 1.5; }

/* ── Code comparison ──────────────────────────────── */
.code-hd {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.65rem 1rem;
  border-radius: var(--rs) var(--rs) 0 0;
  border: 1px solid var(--border); border-bottom: none;
  font-family: var(--mono); font-size: 0.72rem;
}
.code-hd-orig { background: var(--bg3); color: var(--t3); }
.code-hd-opt  { background: rgba(16,185,129,.04); border-color: rgba(16,185,129,.2); color: var(--green); }

/* ── AI summary box ───────────────────────────────── */
.ai-summary { background: var(--adim); border: 1px solid rgba(99,102,241,.18); border-radius: var(--r); padding: 1rem 1.2rem; margin-bottom: 1rem; }
.ai-summary-lbl { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent2); font-family: var(--mono); margin-bottom: 0.4rem; }
.ai-summary-txt { font-size: 0.82rem; color: var(--t2); line-height: 1.65; }

/* ── Progress screen ──────────────────────────────── */
.prog-wrap { max-width: 520px; margin: 3rem auto; }
.prog-card { background: var(--card); border: 1px solid var(--border2); border-radius: var(--rx); padding: 2.25rem 2.5rem; box-shadow: var(--shadow2); position: relative; overflow: hidden; }
.prog-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, var(--accent), var(--purple), var(--teal)); }
.prog-title { font-size: 1.05rem; font-weight: 700; color: var(--t1); text-align: center; margin-bottom: 0.3rem; }
.prog-sub { font-size: 0.77rem; color: var(--t3); text-align: center; margin-bottom: 1.5rem; }
.prog-stage { display: flex; align-items: center; gap: 0.65rem; padding: 0.45rem 0; font-size: 0.78rem; }
.ps-dot-active { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent); animation: pulse 1s infinite; flex-shrink: 0; }
.ps-dot-done   { width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
.ps-dot-idle   { width: 8px; height: 8px; border-radius: 50%; background: var(--t4); flex-shrink: 0; }
.ps-lbl-active { color: var(--t1); font-weight: 500; }
.ps-lbl-done   { color: var(--green); }
.ps-lbl-idle   { color: var(--t4); }
.prog-file-list { background: var(--bg3); border: 1px solid var(--border); border-radius: var(--rs); padding: 0.8rem; max-height: 190px; overflow-y: auto; margin-top: 1rem; }
.pf-row { font-family: var(--mono); font-size: 0.7rem; padding: 0.18rem 0; display: flex; align-items: center; gap: 0.45rem; }
.pf-done    { color: var(--green); }
.pf-active  { color: var(--accent2); }
.pf-pending { color: var(--t4); }

/* ── Empty state ──────────────────────────────────── */
.empty-state { text-align: center; padding: 3rem 1rem; }
.empty-icon  { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-title { font-size: 0.95rem; font-weight: 600; color: var(--green); margin-bottom: 0.3rem; }
.empty-sub   { font-size: 0.78rem; color: var(--t3); }

/* ── Store strip ──────────────────────────────────── */
.store-strip { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 1rem; background: var(--gdim); border: 1px solid rgba(16,185,129,.14); border-radius: var(--rs); margin-top: 1.5rem; font-size: 0.73rem; color: var(--t3); }
.store-strip b { color: var(--t2); }

/* ── Sidebar nav ──────────────────────────────────── */
.sb-brand { padding: 1.25rem 1rem 1rem; border-bottom: 1px solid var(--border); margin-bottom: 0.5rem; }
.sb-section { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--t4); padding: 0.75rem 1rem 0.3rem; }
.sb-key-status-ok  { display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.75rem; background: var(--gdim); border: 1px solid rgba(16,185,129,.18); border-radius: var(--rs); margin: 0.35rem 0; }
.sb-key-status-err { display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.75rem; background: var(--rdim); border: 1px solid rgba(239,68,68,.18); border-radius: var(--rs); margin: 0.35rem 0; }
.sb-key-dot-ok  { width: 6px; height: 6px; border-radius: 50%; background: var(--green); }
.sb-key-dot-err { width: 6px; height: 6px; border-radius: 50%; background: var(--red); }
.sb-footer { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.65rem; color: var(--t4); line-height: 1.7; }
</style>
""", unsafe_allow_html=True)
