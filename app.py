"""AI Code Review Assistant — SaaS-quality UI."""

import streamlit as st
import os, time

st.set_page_config(
    page_title="CodeReview AI — Powered by Groq",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.styling          import apply_custom_styles
from utils.github_utils     import clone_repo, get_source_files
from utils.file_utils       import get_supported_extensions
from utils.ai_analyzer      import analyze_and_store
from utils.report_generator import generate_report
from storage.result_store   import get_store
from components.sidebar     import render_sidebar
from components.views       import (render_dashboard, render_summary_tab,
                                     render_issues_tab, render_optimized_code_tab)

apply_custom_styles()

def _init():
    for k, v in {"phase":"input","selected_file":None,"files_pending":[],"repo_name":""}.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "groq_api_key" not in st.session_state:
        st.session_state["groq_api_key"] = ""
_init()


def main():
    store = get_store()
    render_sidebar()

    # Top bar
    st.markdown("""
    <div class="topbar">
      <div class="topbar-brand">
        <div style="width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#a855f7);
                    border-radius:9px;display:flex;align-items:center;justify-content:center;
                    font-size:.95rem;box-shadow:0 4px 12px rgba(99,102,241,.3)">🔍</div>
        <div>
          <div class="topbar-title">CodeReview AI</div>
          <div class="topbar-sub">Analyze · Detect · Optimize</div>
        </div>
      </div>
      <div class="topbar-right">
        <span class="topbar-pill-v">Llama 3.3 70B</span>
        <span class="topbar-pill">Free</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    p = st.session_state.phase
    if   p == "input":     _page_input()
    elif p == "analyzing": _page_analysis(store)
    elif p == "results":   _page_results(store)


# ═══════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════
def _page_input():
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-glow-1"></div>
      <div class="hero-glow-2"></div>
      <div class="hero-badge">✦ AI-Powered Static Analysis</div>
      <h1 class="hero-title">
        AI-Powered Code Review<br>
        <span class="hl">Assistant</span>
      </h1>
      <p class="hero-desc">
        Analyze repositories and source files using LLMs. Detect bugs, security
        vulnerabilities, performance bottlenecks, and receive optimized code
        suggestions instantly.
      </p>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)

        st.markdown('<div class="inp-lbl">GitHub Repository URL</div>', unsafe_allow_html=True)
        url = st.text_input("url", placeholder="https://github.com/owner/repository",
                            label_visibility="collapsed", key="repo_url")
        st.markdown('<div class="inp-hint">Supports public GitHub repositories · max 40 files</div>', unsafe_allow_html=True)

        if st.button("🚀  Analyze Repository", key="btn_repo",
                     use_container_width=True, type="primary"):
            _start_repo(url)

        st.markdown('<div class="inp-divider">or upload files directly</div>', unsafe_allow_html=True)

        st.markdown('<div class="inp-lbl">Upload Source Files</div>', unsafe_allow_html=True)
        uploads = st.file_uploader("files", type=get_supported_extensions(),
                                   accept_multiple_files=True,
                                   label_visibility="collapsed", key="uploads")
        if uploads:
            st.markdown(f'<div class="inp-hint" style="color:var(--green)">✓ {len(uploads)} file{"s" if len(uploads)!=1 else ""} ready to analyze</div>', unsafe_allow_html=True)

        if st.button("🚀  Analyze Files", key="btn_files",
                     use_container_width=True, type="primary"):
            _start_files(uploads)

        st.markdown('</div>', unsafe_allow_html=True)

    # Feature cards
    _, mid2, _ = st.columns([1, 3, 1])
    with mid2:
        st.markdown("""
        <div class="feature-grid">
          <div class="feature-card">
            <div class="fc-icon fc-icon-bug">🐛</div>
            <div class="fc-title">Bug Detection</div>
            <div class="fc-desc">Logic errors, null dereferences, off-by-one errors, infinite loops</div>
          </div>
          <div class="feature-card">
            <div class="fc-icon fc-icon-sec">🔒</div>
            <div class="fc-title">Security Analysis</div>
            <div class="fc-desc">SQL injection, XSS, CSRF, hardcoded secrets, open redirects</div>
          </div>
          <div class="feature-card">
            <div class="fc-icon fc-icon-perf">⚡</div>
            <div class="fc-title">Performance</div>
            <div class="fc-desc">N+1 queries, blocking I/O, memory leaks, redundant computations</div>
          </div>
          <div class="feature-card">
            <div class="fc-icon fc-icon-qual">✨</div>
            <div class="fc-title">Code Quality</div>
            <div class="fc-desc">Dead code, magic numbers, naming issues, missing documentation</div>
          </div>
        </div>
        <div class="trusted-strip">
          <span>Comparable to</span>
          <span class="trusted-tag">SonarQube</span>
          <span class="trusted-tag">CodeClimate</span>
          <span class="trusted-tag">Snyk</span>
          <span class="trusted-tag">GitHub Insights</span>
        </div>
        """, unsafe_allow_html=True)


def _start_repo(url):
    if not url.strip():
        st.error("Please enter a GitHub URL.")
        return
    if not st.session_state.get("groq_api_key","").strip():
        st.error("Add your Groq API key in the sidebar.")
        return
    with st.spinner("Cloning repository…"):
        try:
            repo_dir, repo_name = clone_repo(url.strip())
        except Exception as e:
            st.error(str(e)); return
    with st.spinner("Scanning source files…"):
        files = get_source_files(repo_dir)
    if not files:
        st.error("No supported source files found.")
        return
    st.session_state.files_pending = files
    st.session_state.repo_name     = repo_name
    st.session_state.phase         = "analyzing"
    st.rerun()


def _start_files(uploads):
    if not uploads:
        st.error("Please upload at least one file.")
        return
    if not st.session_state.get("groq_api_key","").strip():
        st.error("Add your Groq API key in the sidebar.")
        return
    files = [{"name":f.name,"path":f.name,
               "content":f.read().decode("utf-8",errors="replace"),
               "size":f.size} for f in uploads]
    st.session_state.files_pending = files
    st.session_state.repo_name     = "Uploaded Files"
    st.session_state.phase         = "analyzing"
    st.rerun()


# ═══════════════════════════════════════════
# ANALYSIS
# ═══════════════════════════════════════════
def _page_analysis(store):
    files     = st.session_state.files_pending
    repo_name = st.session_state.repo_name
    total     = len(files)

    stages = [
        "Repository Scanning",
        "Security Analysis",
        "Performance Analysis",
        "Bug Detection",
        "Optimization Suggestions",
    ]

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(f"""
        <div class="prog-wrap">
          <div class="prog-card">
            <div class="prog-title">Analyzing {repo_name}</div>
            <div class="prog-sub">Running AI review on {total} file{"s" if total!=1 else ""}…</div>
        """, unsafe_allow_html=True)

        prog    = st.progress(0)
        cur_lbl = st.empty()
        stages_box = st.empty()
        file_box   = st.empty()
        st.markdown('</div></div>', unsafe_allow_html=True)

    statuses   = {f["name"]: "pending" for f in files}
    stage_done = 0

    def _render_stages(active_stage):
        rows = []
        for i, s in enumerate(stages):
            if i < active_stage:
                rows.append(f'<div class="prog-stage"><div class="ps-dot-done"></div><span class="ps-lbl-done">✓ {s}</span></div>')
            elif i == active_stage:
                rows.append(f'<div class="prog-stage"><div class="ps-dot-active"></div><span class="ps-lbl-active">{s}</span></div>')
            else:
                rows.append(f'<div class="prog-stage"><div class="ps-dot-idle"></div><span class="ps-lbl-idle">{s}</span></div>')
        stages_box.markdown("".join(rows), unsafe_allow_html=True)

    def on_progress(done, total, current):
        pct = int(done / total * 100) if total else 0
        prog.progress(pct)
        stage_idx = min(4, int(done / max(total,1) * 5))
        _render_stages(stage_idx)
        cur_lbl.markdown(
            f'<p style="font-family:var(--mono);font-size:.7rem;color:var(--accent2);margin:.3rem 0">{current}</p>',
            unsafe_allow_html=True)
        if done > 0 and done <= len(files):
            statuses[files[done-1]["name"]] = "done"
        if done < len(files):
            statuses[files[done]["name"]] = "active"
        rows = []
        for f in files:
            s   = statuses[f["name"]]
            ico = {"done":"✓","active":"›","pending":"·"}.get(s,"·")
            cls = {"done":"pf-done","active":"pf-active","pending":"pf-pending"}.get(s,"pf-pending")
            rows.append(f'<div class="pf-row {cls}"><span>{ico}</span><span>{f["name"]}</span></div>')
        file_box.markdown(f'<div class="prog-file-list">{"".join(rows)}</div>', unsafe_allow_html=True)

    _render_stages(0)
    api_key = st.session_state.get("groq_api_key", "")
    analyze_and_store(files=files, store=store, repo_name=repo_name, api_key=api_key,
                      on_progress=on_progress, on_warning=lambda _: None)

    prog.progress(100)
    _render_stages(5)
    cur_lbl.markdown(
        f'<p style="font-family:var(--mono);font-size:.7rem;color:var(--green);margin:.3rem 0">'
        f'✓ Completed in {store.elapsed_seconds}s</p>',
        unsafe_allow_html=True)
    time.sleep(0.8)
    st.session_state.phase         = "results"
    st.session_state.files_pending = []
    st.rerun()


# ═══════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════
def _page_results(store):
    render_dashboard(store)

    # Action bar
    c1, c2, c3, c4, _ = st.columns([1.2, 1, 1, 1, 3])
    with c1:
        if st.button("← New Analysis"):
            store.start_session("")
            st.session_state.phase         = "input"
            st.session_state.selected_file = None
            st.rerun()
    with c2:
        st.download_button("📄 Markdown",
            data=generate_report(store),
            file_name=f"review_{store.repo_name.replace(' ','_')}.md",
            mime="text/markdown")
    with c3:
        st.download_button("{ } JSON",
            data=store.to_json(),
            file_name=f"review_{store.repo_name.replace(' ','_')}.json",
            mime="application/json")
    with c4:
        # PDF-style HTML report
        html_report = _build_html_report(store)
        st.download_button("🖨 HTML Report",
            data=html_report,
            file_name=f"review_{store.repo_name.replace(' ','_')}.html",
            mime="text/html")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊  Repository Summary", "🐛  Issues", "✨  Optimized Code"])
    with tab1: render_summary_tab(store)
    with tab2: render_issues_tab(store)
    with tab3: render_optimized_code_tab(store)

    st.markdown(f"""
    <div class="store-strip">
      <span>💾</span>
      <span><b>{store.total_files} files</b> cached in memory ·
            switching tabs makes <b>zero</b> additional API calls ·
            powered by <b>Llama 3.3 70B via Groq</b></span>
    </div>""", unsafe_allow_html=True)


def _build_html_report(store) -> str:
    from datetime import datetime
    now = datetime.now().strftime("%B %d, %Y %H:%M")
    q, sec, mnt, perf = _scores(store)
    rows = ""
    for r in store.sorted_by_severity():
        for issue in r.issues:
            color = {"Critical":"#ef4444","High":"#f97316","Medium":"#f59e0b","Low":"#10b981"}.get(issue.severity,"#10b981")
            rows += f"""<tr>
              <td style="font-family:monospace;font-size:12px;color:#94a3b8">{r.name}</td>
              <td><span style="background:{color}22;color:{color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">{issue.severity}</span></td>
              <td style="font-size:12px;color:#e2e8f0">{issue.title}</td>
              <td style="font-size:12px;color:#94a3b8">{issue.description[:100]}{'...' if len(issue.description)>100 else ''}</td>
            </tr>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Code Review Report — {store.repo_name}</title>
<style>
  body{{font-family:Inter,sans-serif;background:#070a10;color:#f0f4ff;margin:0;padding:2rem}}
  h1{{font-size:1.8rem;font-weight:900;letter-spacing:-.03em;margin-bottom:.25rem}}
  .meta{{color:#4a5568;font-size:.8rem;margin-bottom:2rem;font-family:monospace}}
  .scores{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}}
  .sc{{background:#0f1319;border:1px solid #1a2035;border-radius:10px;padding:1rem;text-align:center}}
  .sc-val{{font-size:1.8rem;font-weight:700;font-family:monospace}}
  .sc-lbl{{font-size:.65rem;color:#4a5568;text-transform:uppercase;letter-spacing:.08em}}
  table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  th{{background:#0f1319;padding:.65rem 1rem;text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.07em;color:#4a5568;border-bottom:1px solid #1a2035}}
  td{{padding:.6rem 1rem;border-bottom:1px solid #0f1319;vertical-align:top}}
  tr:hover td{{background:#0f1319}}
  .footer{{margin-top:2rem;color:#2d3748;font-size:.72rem;text-align:center}}
</style></head><body>
<h1>Code Review Report</h1>
<div class="meta">{store.repo_name} · {now} · {store.total_files} files · {store.total_issues} issues</div>
<div class="scores">
  <div class="sc"><div class="sc-val" style="color:#10b981">{q}</div><div class="sc-lbl">Code Quality</div></div>
  <div class="sc"><div class="sc-val" style="color:#6366f1">{sec}</div><div class="sc-lbl">Security</div></div>
  <div class="sc"><div class="sc-val" style="color:#a855f7">{mnt}</div><div class="sc-lbl">Maintainability</div></div>
  <div class="sc"><div class="sc-val" style="color:#14b8a6">{perf}</div><div class="sc-lbl">Performance</div></div>
</div>
<table><thead><tr><th>File</th><th>Severity</th><th>Issue</th><th>Description</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="footer">Generated by CodeReview AI · Powered by Llama 3.3 70B via Groq</div>
</body></html>"""

def _scores(s):
    q   = min(100, max(0, 100 - s.critical_count*20 - s.high_count*8 - s.medium_count*3 - s.low_count))
    sec = min(100, max(0, 100 - s.critical_count*25 - s.high_count*10))
    mnt = min(100, max(0, 100 - s.medium_count*5  - s.low_count*2))
    prf = min(100, max(0, 100 - s.high_count*12   - s.medium_count*4))
    return int(q), int(sec), int(mnt), int(prf)


if __name__ == "__main__":
    main()
