# Product Requirements Document: Manuscript Alert System

## Document Information
- **Document Type**: Product Requirements Document (PRD)
- **Version**: 2.0
- **Date**: February 19, 2026
- **Project**: Manuscript Alert System
- **Team**: 김태호, 김동훈

---

## 1. Executive Summary

### Overview
The Manuscript Alert System is a local web application that helps researchers stay updated with the latest papers in Alzheimer's disease and neuroimaging. It fetches papers from multiple academic databases, scores them by relevance using configurable keyword matching and journal quality metrics, and presents them in a modern web interface.

### Technology Stack
- **Frontend**: Next.js 15 + React 19 + TypeScript 5.7 + Tailwind CSS 3.4
- **Backend**: FastAPI (Python 3.10+) with type hints, Pydantic models, and REST API
- **Data Sources**: PubMed, arXiv, bioRxiv, and medRxiv (concurrent API fetching)
- **Serving**: Single-command launch — `python server.py` auto-builds the frontend and serves everything on port 8000

### Key Capabilities
- Smart keyword matching with multi-factor relevance scoring
- Journal quality filtering and scoring (PubMed)
- Configurable search parameters, model presets, and CSV export
- Auto-fetch on startup with persistent results across tab switches
- Save/load settings as named model presets for different research topics
- Settings backup and restore

---

## 2. System Architecture

### 2.1 Technology Stack

| Layer      | Technology                                                    |
|------------|---------------------------------------------------------------|
| Frontend   | Next.js 15, React 19, TypeScript 5.7, Tailwind CSS 3.4       |
| Build      | Next.js static export (`output: "export"`) → `frontend/out/` |
| Backend    | FastAPI 0.115+, Uvicorn, Python 3.10+ with type hints        |
| Linting    | Ruff (Python), TypeScript strict mode                         |
| Data       | JSON file storage, Python `config/settings.py`                |
| Serving    | FastAPI serves Next.js static files + REST API on port 8000   |

### 2.2 File Structure
```
Manuscript_alert/
├── server.py                      # FastAPI backend + static file serving
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Ruff configuration
│
├── frontend/                      # Next.js + TypeScript application
│   ├── package.json               # Next.js 15, React 19, TS 5.7, Tailwind 3.4
│   ├── tsconfig.json              # Strict TS config, @/* path aliases
│   ├── next.config.ts             # Static export (output: "export")
│   ├── tailwind.config.ts         # Tailwind configuration
│   ├── postcss.config.mjs         # PostCSS + Autoprefixer
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout (Inter font, metadata)
│   │   │   ├── page.tsx           # Main page — tab nav, lifted state
│   │   │   └── globals.css        # Tailwind directives, custom scrollbar
│   │   ├── components/
│   │   │   ├── PapersTab.tsx      # Papers view with sidebar + auto-fetch
│   │   │   ├── PaperCard.tsx      # Individual paper display
│   │   │   ├── Statistics.tsx     # Source/keyword/score statistics
│   │   │   ├── ModelsTab.tsx      # Save/load/preview/delete model presets
│   │   │   └── SettingsTab.tsx    # Keywords, journals, scoring, search, backup
│   │   ├── lib/
│   │   │   └── api.ts             # Typed API client (all FastAPI endpoints)
│   │   └── types/
│   │       └── index.ts           # Shared interfaces (Paper, Settings, etc.)
│   └── out/                       # Built static files (auto-generated)
│
├── config/
│   ├── settings.py                # Application settings (keywords, journals, scoring)
│   ├── models/                    # Saved model presets (JSON files)
│   └── backups/                   # Settings backups
│
├── core/
│   ├── paper_manager.py           # Core paper management logic
│   └── filters.py                 # Paper filtering and search
│
├── fetchers/
│   ├── arxiv_fetcher.py           # arXiv API integration
│   ├── biorxiv_fetcher.py         # bioRxiv/medRxiv API integration
│   └── pubmed_fetcher.py          # PubMed API integration
│
├── processors/
│   └── keyword_matcher.py         # Keyword matching & relevance scoring
│
├── services/
│   ├── settings_service.py        # Settings load/save/backup
│   └── export_service.py          # CSV export
│
├── storage/
│   └── data_storage.py            # Local data persistence
│
├── utils/
│   ├── constants.py               # Shared constants
│   ├── journal_utils.py           # Journal name utilities
│   └── logger.py                  # Logging
│
├── KB_alz/                        # Knowledge base PDFs (Alzheimer's)
├── logs/                          # Application logs
├── docs/                          # Documentation
└── scripts/                       # Utility scripts
    └── legacy/                    # Legacy scripts
```

### 2.3 API Endpoints

| Method   | Endpoint                         | Description                |
|----------|----------------------------------|----------------------------|
| `GET`    | `/api/settings`                  | Get current settings       |
| `PUT`    | `/api/settings`                  | Save settings              |
| `POST`   | `/api/papers/fetch`              | Fetch and rank papers      |
| `POST`   | `/api/papers/export`             | Export papers as CSV       |
| `GET`    | `/api/models`                    | List saved model presets   |
| `POST`   | `/api/models`                    | Save a new model preset    |
| `POST`   | `/api/models/{filename}/load`    | Load a model preset        |
| `GET`    | `/api/models/{filename}/preview` | Preview a model preset     |
| `DELETE` | `/api/models/{filename}`         | Delete a model preset      |
| `GET`    | `/api/backups`                   | List settings backups      |
| `POST`   | `/api/backups/create`            | Create a settings backup   |
| `POST`   | `/api/backups/restore`           | Restore a settings backup  |
| `DELETE` | `/api/backups`                   | Delete a settings backup   |

---

## 3. Frontend Architecture

### 3.1 Overview

The Next.js frontend uses the **App Router** with a single `"use client"` page component that manages all global state.

### 3.2 State Management
- Global state (settings, papers, loading/error) is lifted to `page.tsx` and passed as props.
- All three tabs (Papers, Models, Settings) remain mounted in the DOM at all times — visibility is toggled via CSS `display: block | none`. This ensures fetched paper results persist across tab switches without re-fetching.
- When settings are saved or a model is loaded, the papers state is cleared to force a fresh fetch with the new configuration.

### 3.3 Type Safety
- All components use strict TypeScript interfaces defined in `src/types/index.ts`.
- The API client in `src/lib/api.ts` returns typed promises for every endpoint.
- Key interfaces: `Paper`, `FetchResult`, `Settings`, `DataSources`, `ModelInfo`, `BackupInfo`.

### 3.4 UI Design
- **Styling**: Tailwind CSS utility classes with a consistent indigo/gray design system.
- **Layout**: Sticky header with tab navigation; sidebar + main content layout on the Papers tab.
- **Auto-fetch**: `PapersTab` automatically fetches papers from all sources on first mount if keywords are configured.

### 3.5 Components

| Component          | Purpose                                                          |
|--------------------|------------------------------------------------------------------|
| `page.tsx`         | Root page — tab navigation, global state management              |
| `PapersTab.tsx`    | Sidebar controls (sources, search mode, filters) + paper list    |
| `PaperCard.tsx`    | Individual paper display with score, keywords, abstract          |
| `Statistics.tsx`   | Collapsible stats: source counts, top keywords, score overview   |
| `ModelsTab.tsx`    | Save/load/preview/delete model presets                           |
| `SettingsTab.tsx`  | Sub-tabs: Keywords, Journals, Scoring, Search, Backup            |

---

## 4. Backend Architecture

### 4.1 Overview

The FastAPI backend (`server.py`) serves as both the REST API and the static file server for the Next.js frontend.

### 4.2 Key Design Decisions

- **Pydantic Models**: `FetchRequest`, `SaveSettingsRequest`, `SaveModelRequest`, `RestoreBackupRequest`, `StatusResponse` for request/response validation.
- **Type Hints**: All functions use `from __future__ import annotations` and modern syntax (`list[str]`, `dict[str, Any]`, `str | None`).
- **Concurrent Fetching**: `ThreadPoolExecutor` (3 workers) for parallel arXiv, bioRxiv/medRxiv, and PubMed API calls.
- **Static Serving**: Next.js `out/` directory served as static files; `/_next` assets mounted separately; catch-all route falls back to `index.html`.
- **Auto-build**: On startup (`python server.py`), the server installs npm dependencies and builds the frontend if `out/` is missing or stale. Skipped with `--dev` flag.

### 4.3 Relevance Scoring

Papers are scored by a multi-factor algorithm in `_fetch_and_rank()`:

1. **Keyword Matching** (`processors/keyword_matcher.py`): Base relevance score from keyword presence in title and abstract, weighted by priority tier (high/medium).
2. **Journal Scoring** (PubMed only): Papers from target journals get a base boost (exact: +8, family: +6, specific: +5) plus a tiered boost based on the number of matched keywords.
3. **Journal Exclusions**: Papers from excluded journal patterns (e.g., "pediatric", "veterinary") are filtered out.
4. **Must-Have Filter**: If configured, papers must match at least one must-have keyword.
5. **Minimum Match Filter**: Papers must match ≥ 2 keywords to be included.

### 4.4 Data Flow

```
User opens app
  → page.tsx loads settings from GET /api/settings
  → PapersTab auto-fetches via POST /api/papers/fetch
      → server.py spawns 3 threads (arXiv, bioRxiv/medRxiv, PubMed)
      → Each fetcher calls its respective API
      → Results merged → keyword scoring → journal scoring → filtering → sorting
      → Top 50 papers returned as JSON
  → React renders PaperCard components with scores and keywords
```

---

## 5. Data Storage

### 5.1 Storage Approach

| Data Type               | Storage                          | Format           |
|-------------------------|----------------------------------|------------------|
| Application settings    | `config/settings.py`             | Python variables |
| Model presets           | `config/models/*.json`           | JSON files       |
| Settings backups        | `config/backups/*.py`            | Python files     |
| Paper results           | In-memory (React state)          | Per-session      |
| Application logs        | `logs/app.log`                   | Text log file    |
| Knowledge base PDFs     | `KB_alz/`                        | PDF files        |

### 5.2 Settings Structure

The `config/settings.py` file contains all configurable parameters:

- `DEFAULT_KEYWORDS` — list of research keywords
- `JOURNAL_SCORING` — enabled flag + boost values per keyword-match tier
- `TARGET_JOURNALS` — exact, family, and specific journal match patterns
- `JOURNAL_EXCLUSIONS` — patterns to exclude from results
- `KEYWORD_SCORING` — high/medium priority keyword tiers with boost multipliers
- `MUST_HAVE_KEYWORDS` — required keyword filter (optional)
- `DEFAULT_SEARCH_SETTINGS` — days back, search mode, min matches, max results, default sources
- `UI_SETTINGS` — theme, display toggles, papers per page

---

## 6. Functional Requirements

### 6.1 Paper Fetching
- Fetch papers from PubMed, arXiv, bioRxiv, and medRxiv concurrently
- Configurable date range (default: 8 days back)
- Three search modes: Brief (fast), Standard (balanced), Extended (comprehensive)
- Toggleable data sources per fetch

### 6.2 Relevance Scoring
- Keyword-based scoring with high/medium priority tiers
- Journal quality scoring for PubMed papers (exact/family/specific match types)
- Must-have keyword filter (papers must match ≥ 1 if configured)
- Minimum keyword match threshold (≥ 2)

### 6.3 User Interface
- Tab-based navigation: Papers, Models, Settings
- Papers tab: sidebar controls + paper list + statistics sidebar
- Real-time search within fetched results
- Expandable abstracts, keyword badges, source badges, relevance scores
- High-impact journal highlighting
- CSV export of results

### 6.4 Model Presets
- Save current settings as a named model preset (JSON)
- Load, preview, and delete model presets
- Loading a model overwrites current settings and clears cached papers

### 6.5 Settings Management
- Edit keywords, journal targets/exclusions, scoring parameters, search settings
- Create/restore/delete settings backups
- All settings changes take effect after clicking "Save All Settings"

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Concurrent API fetching (3 threads) for faster paper retrieval
- Frontend auto-fetch on startup — no manual click needed
- Frontend builds in < 30 seconds; server starts in < 5 seconds
- Fetched papers persist in memory across tab switches (no re-fetching)

### 7.2 Developer Experience
- Single-command launch: `python server.py`
- Dev mode: `python server.py --dev` + `cd frontend && npm run dev` (hot reload)
- Strict TypeScript in frontend, type hints throughout Python backend
- Ruff linting for Python code

### 7.3 Portability
- Runs on macOS and Linux
- Conda environment recommended (`conda create -n basic python=3.11 nodejs -y`)
- No external databases or cloud services required
- All data stored locally in the project directory

### 7.4 Reliability
- Graceful handling of individual API failures (other sources still return results)
- Error messages displayed in the UI for failed fetches
- Settings backup/restore to prevent accidental data loss

---

## 8. Architecture Design Principles

### 8.1 SOLID Principles
- **Single Responsibility**: Each module has one clear purpose (fetcher, matcher, service)
- **Open/Closed**: New data sources can be added as new fetcher modules
- **Interface Segregation**: Clean REST API boundary between frontend and backend
- **Dependency Inversion**: Frontend depends on API contract, not Python implementation

### 8.2 Type Safety
- **Python**: `from __future__ import annotations`, Pydantic models for API boundaries, modern union syntax
- **TypeScript**: `strict: true`, explicit interfaces for all props, API responses, and state

### 8.3 Simplicity
- **Minimal Dependencies**: Only essential libraries (no ORM, no database server)
- **File-based Storage**: JSON and Python files — no setup, human-readable, version-control friendly
- **Single Entry Point**: One command to run the entire application

---

## 9. Known Limitations

1. **Journal Quality Filter**: Only applies to PubMed papers — preprints (arXiv, bioRxiv, medRxiv) don't have journal metadata
2. **Keyword Matching Only**: No semantic understanding — relies on exact keyword presence in title/abstract
3. **No Persistence Across Sessions**: Paper results are in-memory only; closing the browser loses them
4. **Single User**: No authentication or multi-user support; designed as a personal research tool
5. **No Caching**: Papers are re-fetched every time; no local cache of previous results

---

## 10. Future Enhancement Candidates

These are potential improvements not currently implemented:

- **RAG Integration**: Semantic similarity scoring using knowledge bases and embeddings
- **Paper Caching**: Local cache of fetched papers to avoid redundant API calls
- **Reference Manager Integration**: Export to Zotero, Mendeley, etc.
- **Paper Summarization**: AI-generated summaries of abstracts
- **Research Trend Analysis**: Identify emerging topics over time
- **Email/Slack Alerts**: Scheduled notifications for new relevant papers
- **Multi-User Support**: Authentication and per-user settings

---

## 11. How to Run

### Quick Start
```bash
conda activate basic
python server.py
# → Opens at http://localhost:8000
```

### Development Mode
```bash
# Terminal 1 — Backend
python server.py --dev

# Terminal 2 — Frontend (hot reload)
cd frontend && npm run dev
```

### Prerequisites
```bash
conda create -n basic python=3.11 nodejs -y
conda activate basic
pip install -r requirements.txt
```
