"""GitHub repository cloning and file scanning."""

from __future__ import annotations
import re, shutil, tempfile
from pathlib import Path
from typing import List, Dict, Tuple

IGNORE_DIRS = {
    ".git", "node_modules", "build", "dist", "target", "__pycache__",
    "venv", ".venv", "env", ".env", ".idea", ".vscode", "coverage",
    ".nyc_output", "vendor", "bower_components", ".next", ".nuxt",
    "out", "tmp", ".tmp", "logs", ".pytest_cache", ".mypy_cache",
    "htmlcov", "site-packages", ".tox",
}

SUPPORTED_EXT = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c",
    ".h", ".hpp", ".html", ".css", ".scss", ".sql", ".go", ".rs",
    ".rb", ".php", ".swift", ".kt", ".scala", ".cs", ".vue",
}

MAX_FILE_SIZE = 150_000   # 150 KB
MAX_FILES     = 40        # max files per session


def clone_repo(repo_url: str) -> Tuple[str, str]:
    from git import Repo
    repo_url = repo_url.strip().rstrip("/")
    m = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if not m:
        raise ValueError("Invalid GitHub URL — expected https://github.com/owner/repo")

    owner, repo_name = m.group(1), m.group(2)
    tmp = tempfile.mkdtemp(prefix="aicr_")
    try:
        Repo.clone_from(f"https://github.com/{owner}/{repo_name}.git", tmp, depth=1)
        return tmp, repo_name
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        msg = str(e).lower()
        if "not found" in msg or "repository" in msg:
            raise ValueError(f"Repository not found: {owner}/{repo_name}. Is it public?")
        if "auth" in msg:
            raise ValueError("Authentication required — only public repositories supported.")
        raise ValueError(f"Clone failed: {e}")


def get_source_files(directory: str) -> List[Dict]:
    """Return list of {name, path, content} dicts, skipping ignored paths."""
    root  = Path(directory)
    files = []

    for fp in sorted(root.rglob("*")):
        if len(files) >= MAX_FILES:
            break
        if any(p in IGNORE_DIRS for p in fp.parts):
            continue
        if not fp.is_file():
            continue
        if fp.suffix.lower() not in SUPPORTED_EXT:
            continue
        try:
            sz = fp.stat().st_size
            if sz == 0 or sz > MAX_FILE_SIZE:
                continue
            content = fp.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                continue
        except OSError:
            continue

        files.append({
            "name":    fp.name,
            "path":    str(fp.relative_to(root)),
            "content": content,
            "size":    sz,
        })

    return files
