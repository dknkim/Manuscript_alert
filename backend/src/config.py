"""Shared paths, singletons, and mutable state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.src.fetchers.arxiv_fetcher import ArxivFetcher
from backend.src.fetchers.biorxiv_fetcher import BioRxivFetcher
from backend.src.fetchers.pubmed_fetcher import PubMedFetcher
from backend.src.processors.keyword_matcher import KeywordMatcher
from backend.src.services.settings_service import SettingsService


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR: Path = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR: Path = PROJECT_DIR / "backend"
FRONTEND_DIR: Path = PROJECT_DIR / "frontend"
DIST_DIR: Path = FRONTEND_DIR / "out"
ARCHIVE_DIR: Path = BACKEND_DIR / "data" / "archive"
MODELS_DIR: Path = BACKEND_DIR / "config" / "models"

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
arxiv_fetcher: ArxivFetcher = ArxivFetcher()
biorxiv_fetcher: BioRxivFetcher = BioRxivFetcher()
pubmed_fetcher: PubMedFetcher = PubMedFetcher()
keyword_matcher: KeywordMatcher = KeywordMatcher()
settings_service: SettingsService = SettingsService()

# Cache for the last fetch result so export doesn't re-fetch
_fetch_cache: dict[str, Any] | None = None
