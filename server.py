"""
FastAPI backend server for the Manuscript Alert System.
Replaces the Streamlit app with a REST API that serves a React/Next.js frontend.

Usage:
    conda activate basic
    python server.py          # builds frontend if needed, then starts on http://localhost:8000
    python server.py --dev    # skip frontend build (use when running Next.js dev server separately)
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher
from services.settings_service import SettingsService
from utils.logger import Logger

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
FRONTEND_DIR: Path = BASE_DIR / "frontend"
DIST_DIR: Path = FRONTEND_DIR / "out"  # Next.js static export output

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
logger: Logger = Logger(__name__)

app: FastAPI = FastAPI(title="Manuscript Alert System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
arxiv_fetcher: ArxivFetcher = ArxivFetcher()
biorxiv_fetcher: BioRxivFetcher = BioRxivFetcher()
pubmed_fetcher: PubMedFetcher = PubMedFetcher()
keyword_matcher: KeywordMatcher = KeywordMatcher()
settings_service: SettingsService = SettingsService()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FetchRequest(BaseModel):
    data_sources: dict[str, bool]
    search_mode: str = "Brief"


class SaveSettingsRequest(BaseModel):
    settings: dict[str, Any]


class SaveModelRequest(BaseModel):
    name: str


class RestoreBackupRequest(BaseModel):
    path: str


class StatusResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helper functions (ported from app.py)
# ---------------------------------------------------------------------------


def _load_settings() -> dict[str, Any]:
    return settings_service.load_settings()


def _is_journal_excluded(journal_name: str, settings: dict[str, Any]) -> bool:
    if not journal_name:
        return False
    journal_lower: str = journal_name.lower()
    exclusion_patterns: list[str] | dict[str, list[str]] = settings.get(
        "journal_exclusions", []
    )
    if isinstance(exclusion_patterns, list):
        for pattern in exclusion_patterns:
            if pattern.lower() in journal_lower:
                return True
    else:
        for _category, patterns in exclusion_patterns.items():
            for pattern in patterns:
                if pattern.lower() in journal_lower:
                    return True
    return False


def _get_journal_match_type(
    journal_name: str, settings: dict[str, Any]
) -> str | None:
    if not journal_name:
        return None
    journal_lower: str = journal_name.lower().strip()
    if _is_journal_excluded(journal_name, settings):
        return None
    target_patterns: dict[str, list[str]] = settings.get("target_journals", {})
    for exact_match in target_patterns.get("exact_matches", []):
        if journal_lower == exact_match.lower().strip():
            return "exact"
    for family_pattern in target_patterns.get("family_matches", []):
        if journal_lower.startswith(family_pattern.lower().strip()):
            return "family"
    for specific_journal in target_patterns.get("specific_journals", []):
        if specific_journal.lower().strip() in journal_lower:
            return "specific"
    return None


def _is_high_impact_journal(journal_name: str, settings: dict[str, Any]) -> bool:
    return _get_journal_match_type(journal_name, settings) is not None


def _fetch_and_rank(
    settings: dict[str, Any],
    data_sources: dict[str, bool],
    search_mode: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Core fetch-and-rank logic (mirrors the old Streamlit cached version)."""
    keywords: list[str] = settings.get("keywords", [])
    search_settings: dict[str, Any] = settings.get("search_settings", {})
    days_back: int = search_settings.get("days_back", 7)

    end_date: datetime = datetime.now()
    start_date: datetime = end_date - timedelta(days=days_back)

    brief_mode: bool = search_mode.startswith("Brief")
    extended_mode: bool = search_mode.startswith("Extended")

    all_papers_data: list[dict[str, Any]] = []

    # ---- parallel fetch ----
    def fetch_arxiv() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("arxiv"):
            try:
                return (
                    "arxiv",
                    arxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("arxiv_error", str(e))
        return ("arxiv", [])

    def fetch_biorxiv() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("biorxiv") or data_sources.get("medrxiv"):
            try:
                papers: list[dict[str, Any]] = biorxiv_fetcher.fetch_papers(
                    start_date, end_date, keywords, brief_mode, extended_mode
                )
                filtered: list[dict[str, Any]] = [
                    p
                    for p in papers
                    if (p.get("source") == "biorxiv" and data_sources.get("biorxiv"))
                    or (p.get("source") == "medrxiv" and data_sources.get("medrxiv"))
                ]
                return ("biorxiv", filtered)
            except Exception as e:
                return ("biorxiv_error", str(e))
        return ("biorxiv", [])

    def fetch_pubmed() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("pubmed"):
            try:
                return (
                    "pubmed",
                    pubmed_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("pubmed_error", str(e))
        return ("pubmed", [])

    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fn) for fn in (fetch_arxiv, fetch_biorxiv, fetch_pubmed)
        ]
        for future in concurrent.futures.as_completed(futures):
            rtype, rdata = future.result()
            if rtype.endswith("_error"):
                errors.append(f"{rtype.replace('_error', '')}: {rdata}")
            else:
                all_papers_data.extend(rdata)  # type: ignore[arg-type]

    if not all_papers_data:
        return [], errors

    # ---- rank ----
    keyword_scoring: dict[str, Any] = settings.get("keyword_scoring", {})
    journal_scoring: dict[str, Any] = settings.get("journal_scoring", {})

    def process_paper(paper: dict[str, Any]) -> dict[str, Any]:
        relevance_score: float
        matched_keywords: list[str]
        relevance_score, matched_keywords = keyword_matcher.calculate_relevance(
            paper, keywords, keyword_scoring
        )

        if (
            paper.get("source") == "PubMed"
            and paper.get("journal")
            and journal_scoring.get("enabled", True)
        ):
            match_type: str | None = _get_journal_match_type(
                paper["journal"], settings
            )
            if match_type:
                base_boosts: dict[str, float] = {
                    "exact": 8.0,
                    "family": 6.0,
                    "specific": 5.0,
                }
                relevance_score += base_boosts.get(match_type, 0)
                boosts: dict[str, float] = journal_scoring.get(
                    "high_impact_journal_boost", {}
                )
                n: int = len(matched_keywords)
                if n >= 5:
                    relevance_score += boosts.get("5_or_more_keywords", 5.1)
                elif n >= 4:
                    relevance_score += boosts.get("4_keywords", 3.7)
                elif n >= 3:
                    relevance_score += boosts.get("3_keywords", 2.8)
                elif n >= 2:
                    relevance_score += boosts.get("2_keywords", 1.3)
                elif n >= 1:
                    relevance_score += boosts.get("1_keyword", 0.5)

        authors: list[str] | str = paper.get("authors", [])
        if isinstance(authors, list):
            authors_str: str = ", ".join(authors[:3]) + (
                "..." if len(authors) > 3 else ""
            )
        else:
            authors_str = str(authors)

        source: str = paper.get("source", "arXiv")
        source_map: dict[str, str] = {"PubMed": "PubMed", "arxiv": "arXiv"}
        source_display: str = source_map.get(source, source.capitalize())

        return {
            "title": paper["title"],
            "authors": authors_str,
            "abstract": paper["abstract"],
            "published": paper["published"],
            "url": paper.get("arxiv_url", ""),
            "source": source_display,
            "relevance_score": round(relevance_score, 1),
            "matched_keywords": matched_keywords,
            "journal": paper.get("journal", ""),
            "volume": paper.get("volume", ""),
            "issue": paper.get("issue", ""),
            "is_high_impact": (
                _is_high_impact_journal(paper.get("journal", ""), settings)
                if paper.get("source") == "PubMed"
                else False
            ),
        }

    ranked: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futs = {executor.submit(process_paper, p): p for p in all_papers_data}
        for f in concurrent.futures.as_completed(futs):
            try:
                ranked.append(f.result())
            except Exception:
                continue

    ranked.sort(key=lambda p: p["relevance_score"], reverse=True)
    return ranked, errors


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    """Return current settings."""
    return _load_settings()


@app.put("/api/settings")
def save_settings(req: SaveSettingsRequest) -> StatusResponse:
    """Save settings."""
    ok: bool = settings_service.save_settings(req.settings)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return StatusResponse(status="ok")


@app.post("/api/papers/fetch")
def fetch_papers(req: FetchRequest) -> dict[str, Any]:
    """Fetch, rank, and filter papers."""
    settings: dict[str, Any] = _load_settings()
    papers: list[dict[str, Any]]
    errors: list[str]
    papers, errors = _fetch_and_rank(settings, req.data_sources, req.search_mode)

    # Apply filters
    must_have: list[str] = settings.get("must_have_keywords", [])
    filtered: list[dict[str, Any]] = []
    for p in papers:
        if len(p["matched_keywords"]) < 2:
            continue
        if must_have:
            if not any(mk in p["matched_keywords"] for mk in must_have):
                continue
        filtered.append(p)

    return {
        "papers": filtered[:50],
        "total_before_filter": len(papers),
        "total_after_filter": len(filtered),
        "errors": errors,
        "must_have_keywords": must_have,
    }


@app.post("/api/papers/export")
def export_papers(req: FetchRequest) -> StreamingResponse:
    """Export papers as CSV."""
    import io

    import pandas as pd

    settings: dict[str, Any] = _load_settings()
    papers: list[dict[str, Any]]
    papers, _ = _fetch_and_rank(settings, req.data_sources, req.search_mode)

    # Same filter
    must_have: list[str] = settings.get("must_have_keywords", [])
    filtered: list[dict[str, Any]] = [
        p
        for p in papers
        if len(p["matched_keywords"]) >= 2
        and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
    ]

    df: pd.DataFrame = pd.DataFrame(filtered)
    buf: io.StringIO = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=papers_{datetime.now().strftime('%Y%m%d')}.csv"
            )
        },
    )


# --- Models ---

MODELS_DIR: str = "config/models"


@app.get("/api/models")
def list_models() -> list[dict[str, str]]:
    """List saved model presets."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    models: list[dict[str, str]] = []
    for f in sorted(os.listdir(MODELS_DIR)):
        if f.endswith(".json"):
            path: str = os.path.join(MODELS_DIR, f)
            mod_time: float = os.path.getmtime(path)
            models.append(
                {
                    "name": f.replace(".json", "").replace("_", " "),
                    "filename": f,
                    "modified": datetime.fromtimestamp(mod_time).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )
    return models


@app.post("/api/models")
def save_model(req: SaveModelRequest) -> dict[str, str]:
    """Save current settings as a named model."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    clean: str = "".join(
        c for c in req.name if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid model name")
    path: str = os.path.join(MODELS_DIR, f"{clean.replace(' ', '_')}.json")
    settings: dict[str, Any] = _load_settings()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
    return {"status": "ok", "filename": os.path.basename(path)}


@app.post("/api/models/{filename}/load")
def load_model(filename: str) -> StatusResponse:
    """Load a model preset as current settings."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    ok: bool = settings_service.save_settings(loaded)
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to apply model settings"
        )
    return StatusResponse(status="ok")


@app.get("/api/models/{filename}/preview")
def preview_model(filename: str) -> dict[str, Any]:
    """Preview a model preset."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@app.delete("/api/models/{filename}")
def delete_model(filename: str) -> StatusResponse:
    """Delete a model preset."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    os.remove(path)
    return StatusResponse(status="ok")


# --- Backups ---


@app.get("/api/backups")
def list_backups() -> list[dict[str, str]]:
    """List available settings backups."""
    backups: list[str] = settings_service.list_backups()
    result: list[dict[str, str]] = []
    for bp in backups[:10]:
        name: str = os.path.basename(bp)
        date_str: str = name.replace("settings_backup_", "").replace(".py", "")
        result.append({"path": bp, "name": name, "date": date_str})
    return result


@app.post("/api/backups/restore")
def restore_backup(data: RestoreBackupRequest) -> StatusResponse:
    """Restore a backup."""
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    ok: bool = settings_service.restore_backup(data.path)
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to restore backup"
        )
    return StatusResponse(status="ok")


@app.post("/api/backups/create")
def create_backup() -> StatusResponse:
    """Create a manual backup."""
    settings: dict[str, Any] = _load_settings()
    ok: bool = settings_service.save_settings(settings)
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to create backup"
        )
    return StatusResponse(status="ok")


@app.delete("/api/backups")
def delete_backup(data: RestoreBackupRequest) -> StatusResponse:
    """Delete a backup."""
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    os.remove(data.path)
    return StatusResponse(status="ok")


# ---------------------------------------------------------------------------
# Serve Next.js frontend (static files from frontend/out)
# ---------------------------------------------------------------------------

# Mount static assets (JS/CSS/images) — only if the out folder exists.
if DIST_DIR.exists():
    next_static: Path = DIST_DIR / "_next"
    if next_static.exists():
        app.mount(
            "/_next", StaticFiles(directory=str(next_static)), name="next_static"
        )


@app.get("/{full_path:path}", response_model=None)
async def serve_frontend(request: Request, full_path: str) -> FileResponse | dict[str, str]:
    """Serve the Next.js SPA — any non-API route returns index.html."""
    # If the exact file exists in out, serve it (e.g. favicon, manifest)
    file_path: Path = DIST_DIR / full_path
    if file_path.is_file():
        return FileResponse(str(file_path))
    # Otherwise fall back to index.html (SPA client-side routing)
    index: Path = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"detail": "Frontend not built. Run: cd frontend && npm run build"}


# ---------------------------------------------------------------------------
# Auto-build & Run
# ---------------------------------------------------------------------------


def _build_frontend() -> None:
    """Build the Next.js frontend if out/ is missing or outdated."""
    node_modules: Path = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies …")
        subprocess.check_call(["npm", "install"], cwd=str(FRONTEND_DIR))

    # Rebuild if out/ doesn't exist or if src/ is newer than out/
    needs_build: bool = not DIST_DIR.exists()
    if not needs_build:
        index_file: Path = DIST_DIR / "index.html"
        dist_mtime: float = index_file.stat().st_mtime if index_file.exists() else 0
        src_dir: Path = FRONTEND_DIR / "src"
        for f in src_dir.rglob("*"):
            if f.stat().st_mtime > dist_mtime:
                needs_build = True
                break

    if needs_build:
        print("🔨 Building Next.js frontend …")
        subprocess.check_call(["npm", "run", "build"], cwd=str(FRONTEND_DIR))
        print("✅ Frontend built successfully.")
    else:
        print("✅ Frontend already up to date.")


if __name__ == "__main__":
    import uvicorn

    dev_mode: bool = "--dev" in sys.argv

    if not dev_mode:
        _build_frontend()

    port: int = 8000
    print(f"\n🚀 Manuscript Alert System running at  http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
