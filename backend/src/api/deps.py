"""FastAPI dependency injection — provides services to route handlers."""

from __future__ import annotations

from pathlib import Path

from backend.src.config import (
    ARCHIVE_DIR,
    MODELS_DIR,
    AppConfig,
    get_app_config,
)
from backend.src.fetchers.arxiv_fetcher import ArxivFetcher
from backend.src.fetchers.biorxiv_fetcher import BioRxivFetcher
from backend.src.fetchers.pubmed_fetcher import PubMedFetcher
from backend.src.processors.keyword_matcher import KeywordMatcher
from backend.src.services.settings_service import SettingsService


# Module-level singletons (created once, reused by Depends())
_settings_service = SettingsService()
_keyword_matcher = KeywordMatcher()
_arxiv_fetcher = ArxivFetcher()
_biorxiv_fetcher = BioRxivFetcher()
_pubmed_fetcher = PubMedFetcher()


def get_config() -> AppConfig:
    return get_app_config()


def get_settings_service() -> SettingsService:
    return _settings_service


def get_keyword_matcher() -> KeywordMatcher:
    return _keyword_matcher


def get_arxiv_fetcher() -> ArxivFetcher:
    return _arxiv_fetcher


def get_biorxiv_fetcher() -> BioRxivFetcher:
    return _biorxiv_fetcher


def get_pubmed_fetcher() -> PubMedFetcher:
    return _pubmed_fetcher


def get_models_dir() -> Path:
    return MODELS_DIR


def get_archive_dir() -> Path:
    return ARCHIVE_DIR
