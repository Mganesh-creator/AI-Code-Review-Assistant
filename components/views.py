"""All result views with full analytics — SaaS quality."""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from storage.result_store import ResultStore
from utils.ai_analyzer import pygments_lang

_SEV_ORDER = {"Critical":0,"High":1,"Medium":2,"Low":3}
_SEV_BADGE = {
    "Critical": '<span class="badge b-critical">Critical</span>',
    "High":     '<span class="badge b-high">High</span>',
    "Medium":   '<span class="badge b-medium">Medium</span>',
    "Low":      '<span class="badge b-low">Low</span>',
}
_SEV_COLOR = {"Critical":"#ef4444","High":"#f97316","Medium":"#f59e0b","Low":"#10b981","Clean":"#4a5568"}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#8892a4", size=11),
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
)

def _score(store: ResultStore):
    """Compute quality, security, maintainability, performance scores."""
    if store.total_files == 0:
        return 100, 100, 100, 100
    ratio = store.total_issues / max(store.total_files, 1)
    crit_w = store.critical_count * 20
    high_w = store.high_count * 8
    med_w  = store.medium_count * 3
    low_w  = store.low_count * 1
    raw    = max(0, 100 - crit_w - high_w - med_w - low_w)
    quality = min(100, max(0, raw))
    security = min(100, max(0, 100 - store.critical_count * 25 - store.high_count * 10))
    maintain = min(100, max(0, 100 - store.medium_count * 5 - store.low_count * 2))
    perf     = min(100, max(0, 100 - store.high_count * 12 - store.medium_count * 4))
    return int(quality), int(security), int(maintain), int(perf)

def _grade(s: int) -> tuple:
    if s >= 90: return "A", "grade-a"
    if s >= 75: return "B", "grade-b"
    if s >= 60: return "C", "grade-c"
    if s >= 40: return "D", "grade-d"
    return "F", "grade-f"

def _score_color(s: int) -> str:
    if s >= 80: return "#10b981"
    if s >= 60: return "#f59e0b"
    if s >= 40: return "#f97316"
    return "#ef4444"


# ── Dashboard ─────────────────────────────────────────────────────
def render_dashboard(store: ResultStore):
    elapsed = f" · {store.elapsed_seconds}s" if store.elapsed_seconds else ""
    st.markdown(f"""
    <div class="repo-bar">
      <div class="repo-bar-dot"></div>
      <span class="repo-bar-name">{store.repo_name}</span>
      <span class="repo-bar-meta">{store.total_files} files analyzed{elapsed}</span>
      <span class="repo-tag">✓ Complete</span>
    </div>
    <div class="metrics-row">
      <div class="metric-card mc-files">
        <div class="metric-val">{store.total_files}</div>
        <div class="metric-lbl">Files</div>
      </div>
      <div class="metric-card mc-total">
        <div class="metric-val">{store.total_issues}</div>
        <div class="metric-lbl">Total Issues</div>
      </div>
      <div class="metric-card mc-critical">
        <div class="metric-val">{store.critical_count}</div>
        <div class="metric-lbl">Critical</div>
      </div>
      <div class="metric-card mc-high">
        <div class="metric-val">{store.high_count}</div>
        <div class="metric-lbl">High</div>
      </div>
      <div class="metric-card mc-medium">
        <div class="metric-val">{store.medium_count}</div>
        <div class="metric-lbl">Medium</div>
      </div>
      <div class="metric-card mc-low">
        <div class="metric-val">{store.low_count}</div>
        <div class="metric-lbl">Low</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Score cards
    q, sec, mnt, perf = _score(store)
    def sc(val, label):
        g, gc = _grade(val)
        col = _score_color(val)
        return f"""
        <div class="score-card">
          <div class="score-title">{label}</div>
          <div class="score-val-row">
            <span class="score-val" style="color:{col}">{val}</span>
            <span class="score-grade {gc}">{g}</span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width:{val}%;background:{col}"></div>
          </div>
        </div>"""
    st.markdown(f"""
    <div class="score-row">
      {sc(q,   "Code Quality")}
      {sc(sec, "Security")}
      {sc(mnt, "Maintainability")}
      {sc(perf,"Performance")}
    </div>""", unsafe_allow_html=True)


# ── Summary tab ───────────────────────────────────────────────────
def render_summary_tab(store: ResultStore):
    # Repo Insights
    files   = store.all()
    total_lines = sum(len(r.original_code.splitlines()) for r in files)
    avg_issues  = round(store.total_issues / max(store.total_files, 1), 1)
    worst       = max(files, key=lambda r: r.total_issues, default=None)
    worst_name  = worst.name if worst else "—"
    langs       = store.languages()
    lang_str    = ", ".join(list(langs.keys())[:3]) + ("…" if len(langs) > 3 else "")
    elapsed     = f"{store.elapsed_seconds}s" if store.elapsed_seconds else "—"

    st.markdown(f"""
    <div class="insights-grid">
      <div class="insight-card">
        <div class="ins-lbl">Total Files</div>
        <div class="ins-val">{store.total_files}</div>
        <div class="ins-sub">{store.clean_files} clean · {store.total_files - store.clean_files} with issues</div>
      </div>
      <div class="insight-card">
        <div class="ins-lbl">Lines of Code</div>
        <div class="ins-val">{total_lines:,}</div>
        <div class="ins-sub">across {store.total_files} files</div>
      </div>
      <div class="insight-card">
        <div class="ins-lbl">Languages</div>
        <div class="ins-val">{len(langs)}</div>
        <div class="ins-sub">{lang_str}</div>
      </div>
      <div class="insight-card">
        <div class="ins-lbl">Avg Issues / File</div>
        <div class="ins-val">{avg_issues}</div>
        <div class="ins-sub">per source file</div>
      </div>
      <div class="insight-card">
        <div class="ins-lbl">Most Problematic</div>
        <div class="ins-val" style="font-size:.85rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{worst_name}</div>
        <div class="ins-sub">{worst.total_issues if worst else 0} issues</div>
      </div>
      <div class="insight-card">
        <div class="ins-lbl">Analysis Time</div>
        <div class="ins-val">{elapsed}</div>
        <div class="ins-sub">via Groq · Llama 3.3 70B</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        # Pie chart — severity distribution
        st.markdown('<div class="chart-card"><div class="chart-title">Severity Distribution</div>', unsafe_allow_html=True)
        if store.total_issues > 0:
            labels = ["Critical","High","Medium","Low"]
            values = [store.critical_count, store.high_count, store.medium_count, store.low_count]
            colors = ["#ef4444","#f97316","#f59e0b","#10b981"]
            fig = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color="#070a10", width=2)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value} issues<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=200)
            fig.add_annotation(
                text=f"<b>{store.total_issues}</b><br><span style='font-size:10px'>issues</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="#f0f4ff"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-title">No Issues</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Bar chart — issues by file
        st.markdown('<div class="chart-card"><div class="chart-title">Issues by File</div>', unsafe_allow_html=True)
        top_files = sorted(store.all(), key=lambda r: r.total_issues, reverse=True)[:8]
        if any(r.total_issues > 0 for r in top_files):
            names  = [r.name[:18] for r in top_files]
            counts = [r.total_issues for r in top_files]
            bar_colors = [
                "#ef4444" if r.critical_count > 0 else
                "#f97316" if r.high_count > 0 else
                "#f59e0b" if r.medium_count > 0 else
                "#10b981" for r in top_files
            ]
            fig2 = go.Figure(go.Bar(
                y=names, x=counts, orientation="h",
                marker=dict(color=bar_colors, line=dict(width=0)),
                hovertemplate="<b>%{y}</b><br>%{x} issues<extra></extra>",
            ))
            fig2.update_layout(
                **PLOTLY_LAYOUT, height=200,
                xaxis=dict(showgrid=True, gridcolor="#1a2035", zeroline=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=False, tickfont=dict(size=9, family="JetBrains Mono")),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-title">All Clean</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Second row
    col3, col4 = st.columns([1, 1], gap="medium")

    with col3:
        st.markdown('<div class="sum-card"><p class="sec-hd">File Health Overview</p>', unsafe_allow_html=True)
        tf = store.total_files
        for r in sorted(store.all(), key=lambda x: x.total_issues, reverse=True)[:10]:
            color = _SEV_COLOR.get(r.worst_severity, "#4a5568")
            bar_w = min(100, r.total_issues * 12) if r.total_issues > 0 else 2
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:.5rem;padding:.38rem 0;border-bottom:1px solid var(--border)">
              <span style="font-family:var(--mono);font-size:.73rem;color:var(--t2);flex:1;
                           overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{r.path}">{r.name}</span>
              <div style="width:60px;height:4px;background:var(--bg3);border-radius:2px;overflow:hidden">
                <div style="height:100%;width:{bar_w}%;background:{color};border-radius:2px"></div>
              </div>
              <span style="font-family:var(--mono);font-size:.67rem;color:{color};width:18px;text-align:right">{r.total_issues}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="sum-card"><p class="sec-hd">Language Breakdown</p>', unsafe_allow_html=True)
        if langs:
            lang_colors = ["#6366f1","#a855f7","#14b8a6","#f59e0b","#10b981","#0ea5e9","#f97316"]
            for i, (lang, cnt) in enumerate(sorted(langs.items(), key=lambda x: x[1], reverse=True)):
                pct = cnt / tf * 100 if tf else 0
                col = lang_colors[i % len(lang_colors)]
                st.markdown(f"""
                <div class="bar-row">
                  <div class="bar-lbl">{lang[:8]}</div>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:{pct:.1f}%;background:{col}"></div>
                  </div>
                  <div class="bar-cnt">{cnt}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ── Issues tab ────────────────────────────────────────────────────
def render_issues_tab(store: ResultStore):
    if store.total_issues == 0:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">✅</div>
          <div class="empty-title">No Issues Found</div>
          <div class="empty-sub">All reviewed files are clean — excellent code quality!</div>
        </div>""", unsafe_allow_html=True)
        return

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        q = st.text_input("s", placeholder="Search issues…", label_visibility="collapsed", key="iq")
    with c2:
        sev_f = st.selectbox("sv", ["All Severities","Critical","High","Medium","Low"],
                             label_visibility="collapsed", key="isf")
    with c3:
        sort_f = st.selectbox("so", ["By Severity","By File"],
                              label_visibility="collapsed", key="isort")

    sev_filter = sev_f if sev_f != "All Severities" else "All"
    shown = 0

    results = store.sorted_by_severity() if sort_f == "By Severity" else sorted(store.all(), key=lambda r: r.name)

    for r in results:
        issues = r.issues
        if sev_filter != "All":
            issues = [i for i in issues if i.severity == sev_filter]
        if q:
            ql = q.lower()
            issues = [i for i in issues if ql in i.title.lower() or ql in i.description.lower()]
        if not issues:
            continue

        color = _SEV_COLOR.get(r.worst_severity, "#4a5568")
        st.markdown(f"""
        <div class="file-grp">
          <span style="font-size:.8rem;color:var(--t3)">📄</span>
          <span class="file-grp-name">{r.path}</span>
          <span style="font-family:var(--mono);font-size:.68rem;
                       color:{color};background:rgba(0,0,0,.2);padding:1px 7px;border-radius:4px">
            {len(issues)} issue{'s' if len(issues)!=1 else ''}
          </span>
        </div>""", unsafe_allow_html=True)

        for issue in sorted(issues, key=lambda i: _SEV_ORDER.get(i.severity, 3)):
            is_error = issue.title in ("Analysis Failed","Skipped — Daily Limit Reached",
                                       "Analysis Error","Chunk Analysis Error")
            if is_error:
                is_quota = any(k in issue.description.lower() for k in ("daily","quota","limit","exhausted"))
                with st.expander(f"⚠  {issue.title}", expanded=True):
                    st.markdown(f"""
                    <div class="err-box">
                      <div class="err-title">{'Daily Limit Reached' if is_quota else 'API Error'}</div>
                      <div class="err-msg">{issue.description}</div>
                    </div>
                    <div class="fix-box" style="margin-top:.6rem">
                      <div class="fix-lbl">How to Fix</div>
                      <div class="fix-txt">{issue.fix}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                badge = _SEV_BADGE.get(issue.severity, "")
                exp_open = issue.severity in ("Critical","High")
                with st.expander(f"{issue.severity[0]}  {issue.title}", expanded=exp_open):
                    st.markdown(f"""
                    <div style="margin-bottom:.65rem">{badge}</div>
                    <p style="font-size:.82rem;color:var(--t2);line-height:1.65;margin:0 0 .5rem">{issue.description}</p>
                    """, unsafe_allow_html=True)
                    if issue.fix:
                        st.markdown(f"""
                        <div class="fix-box">
                          <div class="fix-lbl">Suggested Fix</div>
                          <div class="fix-txt">{issue.fix}</div>
                        </div>""", unsafe_allow_html=True)
            shown += 1

    if shown == 0:
        st.markdown('<p style="text-align:center;padding:2rem;color:var(--t3);font-size:.82rem">No issues match your filters.</p>', unsafe_allow_html=True)


# ── Optimized Code tab ────────────────────────────────────────────
def render_optimized_code_tab(store: ResultStore):
    if store.is_empty():
        st.info("No files analyzed yet.")
        return

    files   = store.sorted_by_severity()
    paths   = [r.path for r in files]
    names   = {r.path: r.name for r in files}
    sel     = st.session_state.get("selected_file")
    default = paths.index(sel) if sel and sel in paths else 0

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        chosen = st.selectbox("file", paths, index=default,
                              format_func=lambda p: names[p],
                              label_visibility="collapsed", key="ofc")
    r = store.get(chosen)
    if not r:
        return

    with c2:
        orig_l = len(r.original_code.splitlines())
        opt_l  = len(r.optimized_code.splitlines())
        diff   = opt_l - orig_l
        diff_s = f"+{diff}" if diff > 0 else str(diff)
        st.markdown(f"""
        <div style="padding:.55rem .8rem;background:var(--bg3);border:1px solid var(--border);
                    border-radius:var(--rs);font-family:var(--mono);font-size:.7rem;color:var(--t3)">
          {orig_l} → {opt_l} lines &nbsp;
          <span style="color:{'var(--green)' if diff <= 0 else 'var(--yellow)'}">{diff_s}</span>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div style="padding:.55rem .8rem;background:var(--bg3);border:1px solid var(--border);
                    border-radius:var(--rs);font-family:var(--mono);font-size:.7rem">
          <span style="color:var(--t3)">{r.language} · </span>
          <span style="color:var(--{'red' if r.critical_count else 'orange' if r.high_count else 'yellow' if r.medium_count else 'green'})">
            {r.total_issues} issue{'s' if r.total_issues!=1 else ''} fixed
          </span>
        </div>""", unsafe_allow_html=True)

    if r.summary:
        st.markdown(f"""
        <div class="ai-summary">
          <div class="ai-summary-lbl">AI Summary</div>
          <div class="ai-summary-txt">{r.summary}</div>
        </div>""", unsafe_allow_html=True)

    lang = pygments_lang(r.name)
    col_o, col_n = st.columns(2)

    with col_o:
        st.markdown(f"""
        <div class="code-hd code-hd-orig">
          <span>📄 Original — {r.name}</span>
          <span>{orig_l} lines</span>
        </div>""", unsafe_allow_html=True)
        st.code(r.original_code, language=lang, line_numbers=True)

    with col_n:
        st.markdown(f"""
        <div class="code-hd code-hd-opt">
          <span>✨ Optimized — {r.name}</span>
          <span>{opt_l} lines</span>
        </div>""", unsafe_allow_html=True)
        st.code(r.optimized_code, language=lang, line_numbers=True)

    st.markdown("<br>", unsafe_allow_html=True)
    dc, _ = st.columns([1, 4])
    with dc:
        st.download_button("⬇  Download Optimized", data=r.optimized_code,
                           file_name=f"optimized_{r.name}",
                           mime="text/plain", use_container_width=True)
