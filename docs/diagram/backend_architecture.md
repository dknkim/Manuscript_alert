# Backend Architecture

## Request Flow

```
Client (Browser / Next.js)
    │
    ▼
server.py                          ← entry point (python server.py)
    │
    ▼
backend/src/main.py                ← FastAPI app, CORS, static serving
    │
    ├── /_next/*  → StaticFiles    (JS/CSS from frontend/out/)
    ├── /*        → index.html     (SPA catch-all)
    │
    └── /api/*    → Routers
            │
            ├── api/health.py ·················· GET /api/health
            │
            ├── api/settings.py ················ GET /api/settings
            │   └── settings_service ──────────► config/settings.py (read)
            │                                    config/backups/    (snapshot)
            │                        ·········· PUT /api/settings
            │   └── settings_service ──────────► config/settings.py (write)
            │
            ├── api/papers.py ·················· POST /api/papers/fetch
            │   ├── paper_service.fetch_and_rank()
            │   │       │
            │   │       ├── fetchers/arxiv_fetcher ────► arXiv API
            │   │       ├── fetchers/biorxiv_fetcher ──► bioRxiv/medRxiv API
            │   │       ├── fetchers/pubmed_fetcher ───► PubMed API
            │   │       │        (parallel via ThreadPoolExecutor)
            │   │       │
            │   │       ├── processors/keyword_matcher  (score & rank)
            │   │       └── paper_service               (journal boost)
            │   │
            │   └── _fetch_cache (in-memory) ──► reused by export
            │                   ················ POST /api/papers/export
            │   └── pandas → CSV StreamingResponse
            │                   ················ POST /api/papers/archive
            │                   ················ GET  /api/papers/archive
            │                   ················ DEL  /api/papers/archive
            │   └── archive_service ───────────► data/archive/archive.json
            │
            ├── api/models.py ·················· GET    /api/models
            │                  ················· POST   /api/models
            │                  ················· POST   /api/models/{f}/load
            │                  ················· GET    /api/models/{f}/preview
            │                  ················· DELETE /api/models/{f}
            │   └── file I/O ──────────────────► config/models/*.json
            │
            └── api/backups.py ················· GET    /api/backups
                               ················ POST   /api/backups/create
                               ················ POST   /api/backups/restore
                               ················ DELETE /api/backups
                └── settings_service ──────────► config/backups/*.py
```

## File Map

```
server.py                          27 lines   Thin entry point
│
└── backend/
    ├── src/                                   ── App Layer ──
    │   ├── main.py                93 lines   App factory, CORS, routers, static
    │   ├── config.py              35 lines   Paths, singletons, shared state
    │   │
    │   ├── api/                               ── Route Layer ──
    │   │   ├── health.py          15 lines   1 endpoint
    │   │   ├── settings.py        28 lines   2 endpoints
    │   │   ├── papers.py         151 lines   5 endpoints
    │   │   ├── models.py          88 lines   5 endpoints
    │   │   └── backups.py         60 lines   4 endpoints
    │   │
    │   ├── models/                            ── Schema Layer ──
    │   │   └── schemas.py         37 lines   7 Pydantic models
    │   │
    │   └── services/                          ── Service Layer ──
    │       ├── paper_service.py  226 lines   Fetch, score, rank
    │       └── archive_service.py 25 lines   Archive JSON I/O
    │
    ├── fetchers/                              ── External APIs ──
    │   ├── arxiv_fetcher.py                   arXiv API
    │   ├── biorxiv_fetcher.py                 bioRxiv + medRxiv API
    │   └── pubmed_fetcher.py                  PubMed API
    │
    ├── processors/                            ── Processing ──
    │   └── keyword_matcher.py                 Keyword matching & scoring
    │
    ├── services/                              ── Persistence ──
    │   ├── settings_service.py                Settings file I/O
    │   └── export_service.py                  CSV export helper
    │
    ├── utils/                                 ── Utilities ──
    │   ├── logger.py                          Color console + rotating file log
    │   ├── constants.py                       Shared constants
    │   └── journal_utils.py                   Journal name helpers
    │
    ├── config/                                ── Runtime Data ──
    │   ├── settings.py                        Current settings (Python module)
    │   ├── backups/                            Auto-snapshots (gitignored)
    │   └── models/                            Saved presets (*.json)
    │
    └── data/
        └── archive/archive.json               Archived papers
```

## Dependency Flow

```
                    ┌─────────────────────────┐
                    │       server.py          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     src/main.py          │
                    │  (app factory + routers) │
                    └────────────┬────────────┘
                                 │
              ┌──────────┬───────┴───────┬──────────┐
              ▼          ▼               ▼          ▼
         api/papers  api/settings  api/models  api/backups
              │          │               │          │
              ▼          └───────┬───────┘──────────┘
      paper_service              ▼
         │    │          settings_service
         │    │               │
    ┌────┘    └────┐          ▼
    ▼              ▼     config/settings.py
  fetchers    processors  config/backups/
    │              │      config/models/
    ▼              │
 External APIs     │
 (PubMed,arXiv,    │
  bioRxiv)         │
                   ▼
            keyword_matcher

    ───────────────────────
    All use: utils/logger.py
```
