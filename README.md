# AI Code Review Assistant

**Architecture: Fetch → Chunk → Store → Display**

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1  Fetch all files from GitHub repo or file upload    │
│  STEP 2  Chunk large files (> 6 000 chars) at boundaries    │
│  STEP 3  Send ONE Groq request per file (or chunk)          │
│  STEP 4  Store each FileResult in ResultStore immediately   │
│  STEP 5  All tabs read from ResultStore — zero re-calls     │
└─────────────────────────────────────────────────────────────┘
```

This reduces Groq API calls by **70–90%** compared to calling per-tab or per-user-action.

Model: **Llama 3.3 70B via Groq** — free tier: 14,400 requests/day, 6,000 tokens/min.

---

## Get Your FREE Groq API Key

1. Go to **https://console.groq.com/keys**
2. Sign in / create an account
3. Click **Create API Key**
4. Copy it (starts with `gsk_...`)

Free tier: 14,400 requests/day · no credit card needed.

---

## Configure the key — built for multiple people using the same app

This app is set up so that **every visitor pastes their own Groq key** into
the sidebar's password field. Each key is kept only in that visitor's own
browser session (`st.session_state`) — it is never written to disk, never
logged, and never visible to or reused by anyone else who opens the app.
Nothing to configure ahead of time; each person just pastes their key once
per session.

Why per-person keys instead of one shared key: Groq's free tier is
14,400 requests/day *per key*. If everyone shared one hardcoded key, the
whole team would compete for that single daily quota. With each person
using their own key, everyone gets their own full quota.

---

## Run

```bash
cd AI-Code-Review-Assistant-main

pip install -r requirements.txt

streamlit run app.py
```

Opens at **http://localhost:8501**. Paste your key in the sidebar
under "Configuration" and you're ready to analyze.

---

## Project Structure

```
AI-Code-Review-Assistant-main/
│
├── app.py                     # Main entry · 3-phase state machine
│                              #   input → analyzing → results
│
├── storage/
│   └── result_store.py        # ★ Per-session in-memory store
│                              #   One ResultStore per browser session
│                              #   FileResult + Issue dataclasses
│
├── utils/
│   ├── ai_analyzer.py         # Groq calls (one per file)
│   │                          # analyze_and_store() fills ResultStore
│   ├── chunker.py             # Splits large files at boundaries
│   ├── github_utils.py        # Clone repo + recursive file scan
│   ├── file_utils.py          # Supported extension list
│   ├── report_generator.py    # Markdown + JSON export from store
│   └── styling.py             # Dark-theme CSS
│
└── components/
    ├── sidebar.py             # API key config + file explorer
    └── views.py               # Dashboard, Summary, Issues,
                               # Optimized Code — all read from store
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| One Groq call per file | Avoids batch token limits, easier to retry individually |
| Chunking at code boundaries | Preserves context; merges results after |
| ResultStore per session | Each visitor gets an isolated store; tabs never re-call Groq |
| API key kept in `st.session_state` | Never shared between visitors, never persisted to disk |
| Per-file progress updates | User sees live status as each file completes |
| Store written immediately | If analysis crashes mid-way, completed files are not lost |
| JSON + Markdown + HTML export | Human-readable and machine-processable formats |

---

## Security notes

- **API key isolation**: each visitor's Groq key lives in their own
  `st.session_state`, scoped to their browser session only. It is never
  written to an environment variable, never saved to disk, and Streamlit
  guarantees one visitor's session_state is never visible to another —
  so keys can't leak between users of a shared deployment.
- **Multi-user by design**: because each person supplies their own key,
  everyone gets Groq's full free-tier quota (14,400 req/day) independently,
  instead of competing over one shared key.
- **Data isolation**: analysis results (`ResultStore`) are also created
  per-session via `get_store()`, so one visitor's uploaded code and AI
  review never appears in another visitor's browser.
- Only public GitHub repositories are supported for the "Analyze Repository"
  flow — no auth tokens are requested or stored.
