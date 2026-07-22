"""
Result Store — single in-memory database for all analysis results.

All tabs (Summary, Issues, Optimized Code) read from here.
Groq (Llama 3.3 70B) is NEVER called again after the initial per-file analysis.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json, time
import streamlit as st


@dataclass
class Issue:
    title:       str
    description: str
    severity:    str          # Critical | High | Medium | Low
    fix:         str
    line:        Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title, "description": self.description,
            "severity": self.severity, "fix": self.fix, "line": self.line,
        }


@dataclass
class FileResult:
    name:           str
    path:           str
    language:       str
    original_code:  str
    optimized_code: str
    summary:        str
    issues:         List[Issue] = field(default_factory=list)
    analyzed_at:    float       = field(default_factory=time.time)
    error:          Optional[str] = None

    # ── Computed counts ──────────────────────────────────────────
    @property
    def critical_count(self): return sum(1 for i in self.issues if i.severity == "Critical")
    @property
    def high_count(self):     return sum(1 for i in self.issues if i.severity == "High")
    @property
    def medium_count(self):   return sum(1 for i in self.issues if i.severity == "Medium")
    @property
    def low_count(self):      return sum(1 for i in self.issues if i.severity == "Low")
    @property
    def total_issues(self):   return len(self.issues)

    @property
    def worst_severity(self) -> str:
        if self.critical_count: return "Critical"
        if self.high_count:     return "High"
        if self.medium_count:   return "Medium"
        if self.total_issues:   return "Low"
        return "Clean"

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "path": self.path, "language": self.language,
            "original_code": self.original_code, "optimized_code": self.optimized_code,
            "summary": self.summary, "issues": [i.to_dict() for i in self.issues],
            "analyzed_at": self.analyzed_at, "error": self.error,
        }


class ResultStore:
    """
    Central in-memory store.
    Written once during analysis, read many times by all tabs.
    """

    def __init__(self):
        self._results:  Dict[str, FileResult] = {}   # path → FileResult
        self.repo_name: str  = ""
        self.started_at: float = 0.0
        self.finished_at: float = 0.0

    # ── Write ─────────────────────────────────────────────────────
    def start_session(self, repo_name: str):
        self._results  = {}
        self.repo_name = repo_name
        self.started_at = time.time()
        self.finished_at = 0.0

    def store(self, result: FileResult):
        self._results[result.path] = result

    def finish_session(self):
        self.finished_at = time.time()

    # ── Read ──────────────────────────────────────────────────────
    def all(self) -> List[FileResult]:
        return list(self._results.values())

    def get(self, path: str) -> Optional[FileResult]:
        return self._results.get(path)

    def count(self) -> int:
        return len(self._results)

    def is_empty(self) -> bool:
        return len(self._results) == 0

    # ── Aggregates ────────────────────────────────────────────────
    @property
    def total_files(self):    return len(self._results)
    @property
    def total_issues(self):   return sum(r.total_issues   for r in self._results.values())
    @property
    def critical_count(self): return sum(r.critical_count for r in self._results.values())
    @property
    def high_count(self):     return sum(r.high_count     for r in self._results.values())
    @property
    def medium_count(self):   return sum(r.medium_count   for r in self._results.values())
    @property
    def low_count(self):      return sum(r.low_count      for r in self._results.values())
    @property
    def clean_files(self):    return sum(1 for r in self._results.values() if r.total_issues == 0)

    @property
    def elapsed_seconds(self) -> float:
        if self.finished_at and self.started_at:
            return round(self.finished_at - self.started_at, 1)
        return 0.0

    def languages(self) -> Dict[str, int]:
        langs: Dict[str, int] = {}
        for r in self._results.values():
            langs[r.language] = langs.get(r.language, 0) + 1
        return langs

    def sorted_by_severity(self) -> List[FileResult]:
        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Clean": 4}
        return sorted(self._results.values(), key=lambda r: order.get(r.worst_severity, 4))

    # ── Export ────────────────────────────────────────────────────
    def to_json(self) -> str:
        return json.dumps(
            {"repo": self.repo_name, "files": [r.to_dict() for r in self.all()]},
            indent=2,
        )


# ── Per-session store ──────────────────────────────────────────────
# IMPORTANT: this used to be a single module-level object shared by the
# whole Python process. On a shared deployment (Streamlit Community Cloud,
# a Docker container serving multiple visitors, etc.) that meant every
# visitor read and wrote the *same* ResultStore — one person's uploaded
# code, AI-generated review, and optimized code were visible to everyone
# else who opened the app. Storing it in st.session_state instead gives
# each browser session its own private, isolated store.
def get_store() -> "ResultStore":
    if "result_store" not in st.session_state:
        st.session_state["result_store"] = ResultStore()
    return st.session_state["result_store"]
