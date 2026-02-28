# Tests

Backend test suite using [pytest](https://docs.pytest.org/).

## Running tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Single file
pytest tests/test_papers.py

# Single test
pytest tests/test_papers.py::test_archive_and_list

# With coverage (if pytest-cov is installed)
pytest --cov=backend
```

## Structure

```
tests/
├── conftest.py              # Shared fixtures (auto-discovered by pytest)
├── test_health.py           # GET /api/health
├── test_settings.py         # GET/PUT /api/settings
├── test_papers.py           # Fetch, archive, export endpoints
├── test_models.py           # Model preset CRUD
├── test_backups.py          # Backup CRUD
├── test_keyword_matcher.py  # KeywordMatcher scoring & search
└── test_journal_utils.py    # Journal name matching utilities
```

## About conftest.py

`conftest.py` is a special pytest filename — fixtures defined here are automatically available to all test files without importing them. It provides:

- **`client`** — FastAPI `TestClient` with monkeypatched config (temp dirs for models, archive, backups)
- **`mock_settings`** — Sample settings dict
- **`sample_paper` / `sample_paper_arxiv`** — Sample paper dicts for archive and scoring tests
- **`patched_settings_service`** — `SettingsService` pointing at temp files

All file I/O in tests uses `tmp_path` (pytest's built-in temp directory fixture), so tests never touch real data.
