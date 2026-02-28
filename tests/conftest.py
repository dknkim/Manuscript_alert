"""Shared test fixtures — TestClient, mock settings, temp directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Sample settings dict used across tests
# ---------------------------------------------------------------------------
MOCK_SETTINGS: dict[str, Any] = {
    "keywords": ["Alzheimer's disease", "PET", "MRI", "dementia", "amyloid", "tau"],
    "journal_scoring": {
        "enabled": True,
        "high_impact_journal_boost": {
            "5_or_more_keywords": 5.1,
            "4_keywords": 3.7,
            "3_keywords": 2.8,
            "2_keywords": 1.3,
            "1_keyword": 0.5,
        },
    },
    "target_journals": {
        "exact_matches": ["jama", "nature", "science", "radiology"],
        "family_matches": ["jama ", "nature ", "science "],
        "specific_journals": [
            "alzheimer's & dementia",
            "alzheimers dement",
            "journal of magnetic resonance imaging",
        ],
    },
    "journal_exclusions": [
        "abdominal",
        "pediatric",
        "case reports",
    ],
    "keyword_scoring": {
        "high_priority": {
            "keywords": ["Alzheimer's disease", "dementia", "amyloid", "tau"],
            "boost": 1.5,
        },
        "medium_priority": {
            "keywords": ["PET", "MRI"],
            "boost": 1.2,
        },
        "low_priority": {
            "keywords": ["neuroimaging"],
            "boost": 1.0,
        },
    },
    "search_settings": {
        "days_back": 7,
        "search_mode": "Brief",
        "min_keyword_matches": 2,
        "max_results_display": 50,
        "default_sources": {
            "pubmed": True,
            "arxiv": False,
            "biorxiv": False,
            "medrxiv": False,
        },
        "journal_quality_filter": False,
    },
    "ui_settings": {
        "theme": "light",
        "show_abstracts": True,
        "show_keywords": True,
        "show_relevance_scores": True,
        "papers_per_page": 50,
    },
    "must_have_keywords": [],
}


# ---------------------------------------------------------------------------
# Sample paper dicts
# ---------------------------------------------------------------------------
SAMPLE_PAPER: dict[str, Any] = {
    "title": "Amyloid PET imaging in Alzheimer's disease: a systematic review",
    "authors": ["Smith J", "Doe A", "Lee K"],
    "abstract": (
        "Background: Amyloid PET imaging is a key tool for diagnosing Alzheimer's "
        "disease. This review summarizes recent advances in tau and amyloid tracers "
        "for dementia diagnosis using PET and MRI."
    ),
    "published": "2026-02-20",
    "arxiv_url": "",
    "source": "PubMed",
    "journal": "Nature Medicine",
    "pmid": "12345678",
    "volume": "32",
    "issue": "2",
    "categories": [],
}

SAMPLE_PAPER_ARXIV: dict[str, Any] = {
    "title": "Deep learning for brain MRI segmentation",
    "authors": ["Wang X", "Chen Y"],
    "abstract": (
        "We propose a novel deep learning approach for brain MRI segmentation "
        "that improves dementia detection accuracy."
    ),
    "published": "2026-02-18",
    "arxiv_url": "https://arxiv.org/abs/2602.12345",
    "source": "arxiv",
    "arxiv_id": "2602.12345",
    "categories": ["cs.CV", "q-bio.NC"],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_settings() -> dict[str, Any]:
    """Return a copy of the mock settings dict."""
    return json.loads(json.dumps(MOCK_SETTINGS))


@pytest.fixture()
def sample_paper() -> dict[str, Any]:
    return json.loads(json.dumps(SAMPLE_PAPER))


@pytest.fixture()
def sample_paper_arxiv() -> dict[str, Any]:
    return json.loads(json.dumps(SAMPLE_PAPER_ARXIV))


@pytest.fixture()
def tmp_models_dir(tmp_path: Path) -> Path:
    """Temporary models directory."""
    d = tmp_path / "models"
    d.mkdir()
    return d


@pytest.fixture()
def tmp_archive_dir(tmp_path: Path) -> Path:
    """Temporary archive directory."""
    d = tmp_path / "archive"
    d.mkdir()
    return d


@pytest.fixture()
def tmp_settings_file(tmp_path: Path, mock_settings: dict[str, Any]) -> Path:
    """Write a temporary settings.py file and return its path."""
    f = tmp_path / "settings.py"
    # Generate a minimal valid settings.py
    content = f"""\
DEFAULT_KEYWORDS = {mock_settings["keywords"]!r}
JOURNAL_SCORING = {mock_settings["journal_scoring"]!r}
TARGET_JOURNALS = {mock_settings["target_journals"]!r}
JOURNAL_EXCLUSIONS = {mock_settings["journal_exclusions"]!r}
KEYWORD_SCORING = {mock_settings["keyword_scoring"]!r}
MUST_HAVE_KEYWORDS = {mock_settings["must_have_keywords"]!r}
DEFAULT_SEARCH_SETTINGS = {mock_settings["search_settings"]!r}
UI_SETTINGS = {mock_settings["ui_settings"]!r}
"""
    f.write_text(content)
    return f


@pytest.fixture()
def tmp_backup_dir(tmp_path: Path) -> Path:
    """Temporary backup directory."""
    d = tmp_path / "backups"
    d.mkdir()
    return d


@pytest.fixture()
def patched_settings_service(tmp_settings_file: Path, tmp_backup_dir: Path) -> Any:
    """A SettingsService whose paths point at temp files."""
    from backend.src.services.settings_service import SettingsService

    svc = SettingsService()
    svc.settings_file = str(tmp_settings_file)
    svc.backup_dir = str(tmp_backup_dir)
    return svc


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch,
    patched_settings_service: Any,
    tmp_models_dir: Path,
    tmp_archive_dir: Path,
) -> TestClient:
    """
    TestClient with config module monkeypatched to use temp dirs
    and a mock settings service.
    """
    import backend.src.api.backups as api_backups
    import backend.src.api.models as api_models
    import backend.src.api.settings as api_settings
    import backend.src.config as cfg
    import backend.src.services.archive_service as arch_svc

    # Patch config-level singletons / paths
    monkeypatch.setattr(cfg, "settings_service", patched_settings_service)
    monkeypatch.setattr(cfg, "MODELS_DIR", tmp_models_dir)
    monkeypatch.setattr(cfg, "ARCHIVE_DIR", tmp_archive_dir)

    # Patch per-module references that were imported at module load time
    monkeypatch.setattr(api_settings, "settings_service", patched_settings_service)
    monkeypatch.setattr(api_models, "settings_service", patched_settings_service)
    monkeypatch.setattr(api_models, "MODELS_DIR", tmp_models_dir)
    monkeypatch.setattr(api_backups, "settings_service", patched_settings_service)
    monkeypatch.setattr(arch_svc, "ARCHIVE_DIR", tmp_archive_dir)

    # Null the fetch cache
    monkeypatch.setattr(cfg, "_fetch_cache", None)

    from backend.src.main import app

    return TestClient(app)
