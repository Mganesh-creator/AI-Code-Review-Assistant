"""Professional SaaS sidebar."""
import streamlit as st

def render_sidebar():
    with st.sidebar:
        # ── Brand ──────────────────────────────────────
        st.markdown("""
        <div class="sb-brand">
          <div style="display:flex;align-items:center;gap:.65rem">
            <div style="width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#a855f7);
                        border-radius:9px;display:flex;align-items:center;justify-content:center;
                        font-size:.95rem;box-shadow:0 4px 12px rgba(99,102,241,.3)">🔍</div>
            <div>
              <div style="font-weight:700;font-size:.9rem;color:var(--t1);letter-spacing:-.02em">CodeReview AI</div>
              <div style="font-size:.62rem;color:var(--t3);font-family:var(--mono)">v2.0 · Groq + Llama 3.3</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Configuration ───────────────────────────────
        st.markdown('<div class="sb-section">Configuration</div>', unsafe_allow_html=True)
        current = st.session_state.get("groq_api_key", "")
        inp = st.text_input("groq_key", value=current, type="password",
                            placeholder="gsk_...", label_visibility="collapsed",
                            key="groq_key_input",
                            help="Your key stays in your own browser session — it is "
                                 "never saved to disk and never visible to other visitors.")
        if inp != current:
            st.session_state["groq_api_key"] = inp
            if inp:
                st.success("✓ Key updated")

        if st.session_state.get("groq_api_key", ""):
            st.markdown("""
            <div class="sb-key-status-ok">
              <div class="sb-key-dot-ok"></div>
              <span style="font-size:.7rem;color:var(--green)">Connected · Groq API</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="sb-key-status-err">
              <div class="sb-key-dot-err"></div>
              <span style="font-size:.7rem;color:var(--red)">No API key set</span>
            </div>
            <a href="https://console.groq.com/keys" target="_blank"
               style="font-size:.68rem;color:var(--accent2);text-decoration:none;
                      display:block;padding:.3rem .25rem">→ Get your free key at console.groq.com</a>
            """, unsafe_allow_html=True)

        # ── File Explorer ───────────────────────────────
        from storage.result_store import get_store
        store = get_store()
        if not store.is_empty():
            st.markdown('<div class="sb-section">File Explorer</div>', unsafe_allow_html=True)
            sev_icon = {"Critical":"🔴","High":"🟠","Medium":"🟡","Low":"🟢","Clean":"✅"}
            for i, r in enumerate(store.sorted_by_severity()):
                icon = sev_icon.get(r.worst_severity, "📄")
                is_sel = st.session_state.get("selected_file") == r.path
                if st.button(f"{icon}  {r.name[:21]}", key=f"fb_{i}",
                             use_container_width=True,
                             type="primary" if is_sel else "secondary",
                             help=r.path):
                    st.session_state.selected_file = r.path
                    st.rerun()

            # Session stats
            st.markdown(f"""
            <div style="margin:.75rem .25rem 0;padding:.65rem .8rem;background:var(--bg3);
                        border:1px solid var(--border);border-radius:var(--rs)">
              <div style="font-size:.62rem;color:var(--t3);margin-bottom:.4rem;font-weight:600;
                          text-transform:uppercase;letter-spacing:.07em">Session</div>
              <div style="font-family:var(--mono);font-size:.7rem;color:var(--t2)">
                {store.total_files} files · {store.total_issues} issues<br>
                <span style="color:var(--red)">{store.critical_count} critical</span> ·
                <span style="color:var(--orange)">{store.high_count} high</span>
              </div>
            </div>""", unsafe_allow_html=True)

        # ── Footer ──────────────────────────────────────
        st.markdown("""
        <div class="sb-footer">
          Powered by <span style="color:var(--accent2);font-weight:600">Llama 3.3 70B</span><br>
          via Groq Infrastructure · Free tier<br>
          <span style="color:var(--t4)">14,400 req/day · No billing</span>
        </div>""", unsafe_allow_html=True)
