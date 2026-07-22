"""
Groq Analyzer — one API call per file, chunking for large files.
Uses Groq's free tier: llama-3.3-70b-versatile
Free tier: 14,400 requests/day, 6,000 tokens/min — much more generous than Gemini.
"""

from __future__ import annotations
import os, json, re, time
from typing import Dict, Any, List, Callable, Optional

from groq import Groq, RateLimitError, AuthenticationError
from storage.result_store import ResultStore, FileResult, Issue
from utils.chunker import chunk_code, merge_chunk_results

# Groq free tier is generous — small delay is enough
DELAY_BETWEEN_FILES = 2
MAX_RETRIES         = 3
RETRY_BASE_WAIT     = 20

REVIEW_PROMPT = """You are a senior code reviewer. Analyze the source code below and return ONLY a valid JSON object — no markdown fences, no explanation, no extra text.

File : {filename}
Lang : {language}

```
{code}
```

Return exactly this JSON structure and nothing else:
{{
  "issues": [
    {{
      "title":       "concise issue title",
      "description": "what is wrong and why it matters",
      "severity":    "Critical|High|Medium|Low",
      "fix":         "exact steps or code snippet to fix it",
      "line":        null
    }}
  ],
  "optimized_code": "complete rewritten file with every issue resolved",
  "summary": "2-3 sentences on overall code quality"
}}

Detect:
- Bugs: logic errors, off-by-one, null deref, infinite loops
- Security: SQL injection, XSS, CSRF, hardcoded secrets
- Performance: N+1 queries, blocking I/O, memory leaks
- Code smells: dead code, magic numbers, duplicated logic
- Maintainability: missing error handling, poor naming, no docs
- Best practices: language-specific anti-patterns

Return ONLY the JSON object. No other text."""

# ── Language maps ─────────────────────────────────────────────────
_EXT_LANG = {
    ".py":"Python",".js":"JavaScript",".ts":"TypeScript",
    ".jsx":"React JSX",".tsx":"React TSX",".java":"Java",
    ".cpp":"C++",".c":"C",".h":"C/C++ Header",".hpp":"C++ Header",
    ".html":"HTML",".css":"CSS",".scss":"SCSS",".sql":"SQL",
    ".go":"Go",".rs":"Rust",".rb":"Ruby",".php":"PHP",
    ".swift":"Swift",".kt":"Kotlin",".scala":"Scala",".cs":"C#",".vue":"Vue",
}
_EXT_PYGMENTS = {
    ".py":"python",".js":"javascript",".ts":"typescript",
    ".jsx":"jsx",".tsx":"tsx",".java":"java",
    ".cpp":"cpp",".c":"c",".h":"c",".hpp":"cpp",
    ".html":"html",".css":"css",".scss":"scss",".sql":"sql",
    ".go":"go",".rs":"rust",".rb":"ruby",".php":"php",
    ".swift":"swift",".kt":"kotlin",".scala":"scala",".cs":"csharp",".vue":"html",
}

def language_name(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_LANG.get(ext, "Unknown")

def pygments_lang(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_PYGMENTS.get(ext, "text")


# ── Client ────────────────────────────────────────────────────────
def get_client(api_key: str) -> Groq:
    key = (api_key or "").strip()
    if not key:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Get a free key at https://console.groq.com/keys"
        )
    return Groq(api_key=key)


# ── Error classifier ──────────────────────────────────────────────
def _classify_error(err: str) -> str:
    e = err.lower()
    if "invalid_api_key" in e or "authentication" in e or "401" in e:
        return (
            "Invalid API key. Check your key at "
            "https://console.groq.com/keys and paste it in the sidebar."
        )
    if "rate_limit" in e or "429" in e:
        if "day" in e or "daily" in e:
            return (
                "Daily request limit reached. "
                "Groq free tier: 14,400 requests/day. "
                "Wait until tomorrow or create a new key at https://console.groq.com/keys"
            )
        return (
            "Per-minute rate limit hit. "
            "The app will automatically retry after a short wait."
        )
    if "context_length" in e or "tokens" in e:
        return (
            "File too large for a single API call. "
            "The chunker will split it and retry automatically."
        )
    if "network" in e or "connection" in e or "timeout" in e:
        return "Network error — check your internet connection and try again."
    return err.split("\n")[0][:200]

def _is_daily_limit(err: str) -> bool:
    e = err.lower()
    return ("rate_limit" in e or "429" in e) and ("day" in e or "daily" in e)

def _is_rate_limit(err: str) -> bool:
    e = err.lower()
    return ("rate_limit" in e or "429" in e) and not _is_daily_limit(e)


# ── Single Groq call with retry ───────────────────────────────────
def _call_groq(filename: str, language: str, code: str, api_key: str,
               on_wait: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    prompt = REVIEW_PROMPT.format(filename=filename, language=language, code=code)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = get_client(api_key)
            resp   = client.chat.completions.create(
                model    = "llama-3.3-70b-versatile",
                messages = [{"role": "user", "content": prompt}],
                max_tokens      = 4096,
                temperature     = 0.1,
                response_format = {"type": "json_object"},
            )
            text = resp.choices[0].message.content.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$",           "", text)
            return json.loads(text.strip())

        except json.JSONDecodeError:
            return {"issues": [], "optimized_code": code, "summary": ""}

        except AuthenticationError:
            raise RuntimeError(
                "Invalid API key. Get a free key at https://console.groq.com/keys"
            )

        except RateLimitError as e:
            err = str(e)
            if _is_daily_limit(err):
                raise RuntimeError(_classify_error(err))
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_WAIT * attempt
                if on_wait:
                    on_wait(f"⏳ Rate limit — waiting {wait}s (retry {attempt}/{MAX_RETRIES - 1})…")
                time.sleep(wait)
                continue
            raise RuntimeError(_classify_error(err))

        except Exception as e:
            err = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(DELAY_BETWEEN_FILES * 2)
                continue
            raise RuntimeError(_classify_error(err))

    raise RuntimeError("Max retries exceeded.")


def _normalize_issues(raw_issues: list) -> List[Issue]:
    issues = []
    for i in raw_issues:
        sev = i.get("severity", "Low").strip().title()
        if sev not in ("Critical", "High", "Medium", "Low"):
            sev = "Low"
        issues.append(Issue(
            title       = i.get("title", "Unnamed Issue")[:120],
            description = i.get("description", ""),
            severity    = sev,
            fix         = i.get("fix", ""),
            line        = i.get("line"),
        ))
    return issues


# ── Analyze one file (with chunking) ─────────────────────────────
def analyze_file(
    name:     str,
    path:     str,
    content:  str,
    api_key:  str,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> FileResult:
    lang    = language_name(name)
    chunks  = chunk_code(content, name)
    total_ch = len(chunks)
    chunk_results = []

    for idx, chunk_text in chunks:
        label = f"chunk {idx+1}/{total_ch}" if total_ch > 1 else "full file"
        if on_chunk:
            on_chunk(f"  ↳ {name} ({label})")

        raw = _call_groq(name, lang, chunk_text, api_key, on_wait=on_chunk)
        chunk_results.append(raw)

        if idx < total_ch - 1:
            time.sleep(DELAY_BETWEEN_FILES)

    merged = merge_chunk_results(chunk_results, content)
    return FileResult(
        name           = name,
        path           = path,
        language       = lang,
        original_code  = content,
        optimized_code = merged["optimized_code"],
        summary        = merged["summary"],
        issues         = _normalize_issues(merged["issues"]),
    )


# ── Analyze all files → fill ResultStore ─────────────────────────
def analyze_and_store(
    files:       List[Dict],
    store:       ResultStore,
    repo_name:   str,
    api_key:     str,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    on_warning:  Optional[Callable[[str], None]] = None,
):
    store.start_session(repo_name)
    total          = len(files)
    daily_exceeded = False

    for i, f in enumerate(files):
        name    = f["name"]
        path    = f.get("path", name)
        content = f.get("content", "")

        if on_progress:
            on_progress(i, total, name)

        if daily_exceeded:
            store.store(FileResult(
                name=name, path=path, language=language_name(name),
                original_code=content, optimized_code=content,
                summary="Skipped — daily API limit was reached during this session.",
                issues=[Issue(
                    title="Skipped — Daily Limit Reached",
                    description="This file was not analyzed because the daily Groq API limit was reached.",
                    severity="Low",
                    fix="Wait until tomorrow or create a new API key at https://console.groq.com/keys",
                )],
                error="daily_limit",
            ))
            continue

        def chunk_cb(msg):
            if on_warning and ("⏳" in msg or "Rate" in msg):
                on_warning(msg)
            elif on_progress:
                on_progress(i, total, msg)

        try:
            result = analyze_file(name, path, content, api_key, on_chunk=chunk_cb)
            if i < total - 1:
                time.sleep(DELAY_BETWEEN_FILES)

        except RuntimeError as e:
            clean = str(e)
            if "daily" in clean.lower() or "wait until tomorrow" in clean.lower():
                daily_exceeded = True
                if on_warning:
                    on_warning("🚫 Daily limit reached. Remaining files will be skipped.")
            result = FileResult(
                name=name, path=path, language=language_name(name),
                original_code=content, optimized_code=content,
                summary=f"Analysis failed: {clean}",
                issues=[Issue(
                    title="Analysis Failed",
                    description=clean,
                    severity="Low",
                    fix="Check your GROQ_API_KEY or get a new key at https://console.groq.com/keys",
                )],
                error=clean,
            )
        except Exception as e:
            clean = _classify_error(str(e))
            result = FileResult(
                name=name, path=path, language=language_name(name),
                original_code=content, optimized_code=content,
                summary=f"Analysis failed: {clean}",
                issues=[Issue(
                    title="Analysis Failed",
                    description=clean,
                    severity="Low",
                    fix="Check your API key and internet connection.",
                )],
                error=clean,
            )

        store.store(result)

    store.finish_session()
    if on_progress:
        on_progress(total, total, "Done")
