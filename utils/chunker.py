"""
File chunker — splits large source files into manageable chunks
before sending to Groq, then merges the results back.

Strategy:
  • Files ≤ CHUNK_SIZE  → sent as-is (1 Groq call)
  • Files  > CHUNK_SIZE → split at function/class boundaries when
                          possible, otherwise at line boundaries
"""

from __future__ import annotations
import re
from typing import List, Tuple

CHUNK_SIZE   = 6_000   # characters per chunk sent to Groq
OVERLAP_LINES = 5      # lines of overlap so context isn't lost at boundaries


def needs_chunking(code: str) -> bool:
    return len(code) > CHUNK_SIZE


def chunk_code(code: str, filename: str) -> List[Tuple[int, str]]:
    """
    Split code into chunks.
    Returns list of (chunk_index, chunk_text).
    chunk_text includes a small header so Groq knows context.
    """
    if not needs_chunking(code):
        return [(0, code)]

    lines      = code.splitlines(keepends=True)
    chunks     = []
    chunk_idx  = 0
    start      = 0

    while start < len(lines):
        # Accumulate lines until we hit CHUNK_SIZE
        end    = start
        length = 0
        while end < len(lines) and length < CHUNK_SIZE:
            length += len(lines[end])
            end    += 1

        # Try to break at a clean boundary (def/class/function/{)
        if end < len(lines):
            for look_back in range(min(30, end - start)):
                candidate = end - look_back - 1
                line      = lines[candidate]
                if re.match(r'^\s*(def |class |function |async def |public |private |protected |void |int |static )', line):
                    end = candidate
                    break

        chunk_lines = lines[start:end]
        chunk_text  = (
            f"# ── CHUNK {chunk_idx + 1} of {filename} "
            f"(lines {start + 1}–{start + len(chunk_lines)}) ──\n"
            + "".join(chunk_lines)
        )
        chunks.append((chunk_idx, chunk_text))
        chunk_idx += 1

        # Next chunk starts with a small overlap
        start = max(end - OVERLAP_LINES, end)

    return chunks


def merge_chunk_results(chunk_results: List[dict], original_code: str) -> dict:
    """
    Merge issues from multiple chunks into one FileResult-compatible dict.
    For optimized_code we take the last chunk's full version (most complete).
    """
    all_issues = []
    summary_parts = []
    optimized_code = original_code

    seen_titles: set = set()

    for r in chunk_results:
        for issue in r.get("issues", []):
            key = issue.get("title", "").strip().lower()
            if key not in seen_titles:          # deduplicate
                seen_titles.add(key)
                all_issues.append(issue)

        if r.get("summary"):
            summary_parts.append(r["summary"])

        if r.get("optimized_code", "").strip():
            optimized_code = r["optimized_code"]

    return {
        "issues":         all_issues,
        "optimized_code": optimized_code,
        "summary":        " ".join(summary_parts),
    }
