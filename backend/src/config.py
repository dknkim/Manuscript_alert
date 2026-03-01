"""App configuration — env-based settings, paths, and singletons."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Environment-based configuration (reads from .env)
# ---------------------------------------------------------------------------
class AppConfig(BaseSettings):
    """Cloud service keys — all optional until their migration steps."""

    database_url: str = ""
    anthropic_api_key: str = ""
    pinecone_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return AppConfig()


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
# Singletons (lazy imports preserved for backward compatibility)
# ---------------------------------------------------------------------------
from backend.src.fetchers.arxiv_fetcher import ArxivFetcher  # noqa: E402
from backend.src.fetchers.biorxiv_fetcher import BioRxivFetcher  # noqa: E402
from backend.src.fetchers.pubmed_fetcher import PubMedFetcher  # noqa: E402
from backend.src.processors.keyword_matcher import KeywordMatcher  # noqa: E402
from backend.src.services.settings_service import SettingsService  # noqa: E402


arxiv_fetcher: ArxivFetcher = ArxivFetcher()
biorxiv_fetcher: BioRxivFetcher = BioRxivFetcher()
pubmed_fetcher: PubMedFetcher = PubMedFetcher()
keyword_matcher: KeywordMatcher = KeywordMatcher()
settings_service: SettingsService = SettingsService()

# Cache for the last fetch result so export doesn't re-fetch
_fetch_cache: dict[str, Any] | None = None
