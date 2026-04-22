# Manuscript Alert System for AD and Neuroimaging

A web application that helps researchers stay updated with the latest papers in Alzheimer's disease and neuroimaging from PubMed, arXiv, bioRxiv, and medRxiv.

**Deployed stack**: Vercel (frontend) + Render (backend) + Neon (Postgres) + Clerk (auth)

---

## Quick Start (Local Development)

> **First time?** Complete [Installation](#installation) and [Environment Setup](#environment-setup) below.

```bash
# Terminal 1 — Backend (FastAPI on http://localhost:8000)
conda activate manuscript_alert
python server.py --dev

# Terminal 2 — Frontend (Next.js on http://localhost:3000)
cd frontend && npm run dev
```

Visit **[http://localhost:3000](http://localhost:3000)**. Papers are fetched automatically on load.

To stop: `Ctrl+C` in both terminals.

---

## Environment Setup

Copy `.env.example` to `.env` in the repo root and fill in the values:

```bash
cp .env.example .env
```

| Variable | Where to find it | Required |
|---|---|---|
| `CLERK_JWKS_URL` | Clerk dashboard → API Keys → Advanced → JWKS URL | Yes |
| `CLERK_SECRET_KEY` | Clerk dashboard → API Keys (starts with `sk_`) | Yes |
| `DATABASE_URL` | Neon dashboard → Connection string | No (falls back to local JSON) |
| `ANTHROPIC_API_KEY` | Anthropic console | No (Step 7 agent pipeline) |
| `PINECONE_API_KEY` | Pinecone console | No (Step 8 KB) |

Create `frontend/.env.local` for the frontend:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ with npm
- Git

### Option A: Conda (recommended)

```bash
source scripts/bootstrap_conda_env.sh
```

Or manually:

```bash
conda create -n manuscript_alert python=3.11 nodejs -y
conda activate manuscript_alert
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Option B: venv

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Verify

```bash
python -c "import fastapi; print('Backend OK')"
node -v   # should print v18+
```

---

## Features

- **Multi-source paper fetching**: PubMed, arXiv, bioRxiv, and medRxiv
- **Auto-fetch on startup**: Papers are fetched automatically when the app loads
- **SSE progress streaming**: Real-time fetch progress via Server-Sent Events
- **Smart keyword matching**: Papers must match at least 2 keywords to be displayed
- **Relevance scoring**: Papers are ranked by relevance to your research interests
- **Journal quality filtering**: Option to show only papers from high-impact journals
- **Paper archiving**: Save interesting papers for later reference
- **Configurable search parameters**: Date range, search limits, and data sources
- **Model presets**: Save and load different keyword/settings configurations
- **Settings backup & restore**: Automatic and manual backup of settings
- **Export functionality**: Download results as CSV
- **Knowledge Base**: Upload and search PDFs (Pinecone-backed, Step 8)
- **Auth**: Clerk-based login with per-user data isolation

## System Requirements

Tested on macOS and Linux with Conda or venv.

- Python 3.11+
- Node.js 18+ (with npm)
- Conda (recommended) or venv
- Internet connection for fetching papers

---

## Usage

### Tabs

1. **Papers**: Papers are fetched automatically on load. Use the sidebar to toggle sources, select search mode (Brief / Standard / Extended), filter by journal quality, search within results, archive papers, and export to CSV.
2. **Models**: Save/load keyword & settings presets for different research topics. Two presets ship by default: `AD_neuroimaging` and `Stroke_imaging`.
3. **Settings**: Configure keywords, journal preferences, scoring parameters, and manage backups.
4. **Knowledge Base**: Upload PDFs and run semantic search over them (requires Pinecone key).

### Search Modes

| Mode | PubMed | Others |
|---|---|---|
| Brief | 1,000 | 500 |
| Standard | 2,500 | 1,000 |
| Extended | 5,000 | 5,000 |

---

## Technical Details

### Architecture

- **Frontend**: Next.js 16 + React 19 + TypeScript 5.9 + Tailwind CSS 4 — SSR, deployed to Vercel
- **Backend**: FastAPI (Python 3.11) with modular `/api/v1/` routers — deployed to Render free tier (~30 s cold start)
- **Database**: Neon (serverless Postgres via asyncpg) — falls back to local JSON files when `DATABASE_URL` is unset
- **Auth**: Clerk (JWT verification on protected endpoints)
- **Data Sources**: PubMed, arXiv, bioRxiv/medRxiv APIs (parallel fetch with SSE progress)
- **Keep-alive**: GitHub Actions pings `/api/v1/health` every 10 min (Pacific 6 am–11 pm) to reduce cold starts

### File Structure

```
Manuscript_alert/
├── server.py                          # Local dev entry point
├── requirements.txt
├── pyproject.toml                     # Ruff config
├── .env.example                       # Env var template
├── backend/
│   └── src/
│       ├── main.py                    # FastAPI app factory, CORS, routers
│       ├── config.py                  # pydantic-settings env config
│       ├── api/
│       │   ├── auth.py                # Clerk JWT verification
│       │   ├── deps.py                # Dependency injection
│       │   └── v1/                    # Route modules
│       │       ├── health.py          # GET /api/v1/health
│       │       ├── settings.py        # Settings GET/PUT
│       │       ├── papers.py          # Fetch, export, archive, review (SSE)
│       │       ├── models.py          # Model preset CRUD
│       │       ├── backups.py         # Backup CRUD
│       │       └── kb.py              # Knowledge Base CRUD
│       ├── db/
│       │   ├── neon.py                # asyncpg pool, schema, local→DB migration
│       │   └── models.py              # SQL queries
│       ├── models/
│       │   ├── schemas.py             # Pydantic request/response models
│       │   └── events.py              # SSE event shapes
│       ├── services/
│       │   ├── paper_service.py       # Fetch, rank, SSE progress streaming
│       │   ├── archive_service.py     # Archive JSON I/O
│       │   ├── settings_service.py    # Settings load/save/backup
│       │   └── export_service.py      # CSV export
│       ├── fetchers/
│       │   ├── arxiv_fetcher.py
│       │   ├── biorxiv_fetcher.py
│       │   └── pubmed_fetcher.py
│       ├── processors/
│       │   └── keyword_matcher.py
│       └── utils/
│           ├── constants.py
│           ├── journal_utils.py
│           └── logger.py
├── frontend/
│   └── src/
│       ├── app/                       # Next.js App Router pages
│       │   ├── layout.tsx
│       │   ├── page.tsx               # Papers page
│       │   ├── models/page.tsx
│       │   ├── settings/page.tsx
│       │   ├── kb/page.tsx
│       │   └── sign-in/               # Clerk sign-in
│       ├── components/
│       │   ├── features/              # SearchPanel, PaperFeed, DashboardPanel, AgentActivityStream
│       │   ├── layout/                # AppShell
│       │   └── ui/                    # Card, Flash, Spinner, Toggle, etc.
│       ├── hooks/                     # useSettings, usePaperSearch, useAgentStream, useKnowledgeBase
│       ├── lib/
│       │   ├── api.ts                 # Typed API client
│       │   └── utils.ts
│       ├── proxy.ts                   # Clerk auth proxy
│       └── types/index.ts
├── tests/                             # pytest — 60+ tests
├── docs/                              # Architecture reference, cloud migration plan, deployment guide
├── scripts/                           # bootstrap_conda_env.sh, setup-git-hook.sh
└── logs/                              # app.log
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/settings` | Get current settings |
| `PUT` | `/api/v1/settings` | Save settings |
| `POST` | `/api/v1/papers/fetch` | Fetch and rank papers (SSE stream) |
| `POST` | `/api/v1/papers/review` | AI review of a paper |
| `POST` | `/api/v1/papers/export` | Export papers as CSV |
| `POST` | `/api/v1/papers/archive` | Archive a paper |
| `GET` | `/api/v1/papers/archive` | List archived papers |
| `DELETE` | `/api/v1/papers/archive` | Remove a paper from archive |
| `GET` | `/api/v1/models` | List saved model presets |
| `POST` | `/api/v1/models` | Save a new model preset |
| `POST` | `/api/v1/models/{filename}/load` | Load a model preset |
| `GET` | `/api/v1/models/{filename}/preview` | Preview a model preset |
| `DELETE` | `/api/v1/models/{filename}` | Delete a model preset |
| `GET` | `/api/v1/backups` | List settings backups |
| `POST` | `/api/v1/backups/create` | Create a settings backup |
| `POST` | `/api/v1/backups/restore` | Restore a settings backup |
| `DELETE` | `/api/v1/backups` | Delete a settings backup |
| `GET` | `/api/v1/kb/projects` | List KB projects |
| `POST` | `/api/v1/kb/projects` | Create a KB project |
| `GET` | `/api/v1/kb/projects/{id}` | Get a KB project |
| `DELETE` | `/api/v1/kb/projects/{id}` | Delete a KB project |
| `POST` | `/api/v1/kb/projects/{id}/documents` | Upload a document |
| `GET` | `/api/v1/kb/projects/{id}/search` | Semantic search |

Swagger UI: `http://localhost:8000/docs`

### Dependencies

**Python** (`requirements.txt`): `fastapi`, `uvicorn`, `pandas`, `requests`, `beautifulsoup4`, `lxml`, `feedparser`, `asyncpg`, `pydantic-settings`, `sse-starlette`, `python-dotenv`, `python-multipart`, `PyJWT`, `cryptography`, `ruff`, `pytest`, `httpx`, `pytest-asyncio`

**Frontend** (`frontend/package.json`): `next`, `react`, `typescript`, `tailwindcss`, `@clerk/nextjs`

---

## Running Tests

```bash
# Backend
conda activate manuscript_alert
pytest

# Frontend
cd frontend && npm test
```

CI runs ruff, pytest, frontend vitest, build check, and Playwright E2E on every push.

---

## Troubleshooting

**"npm: command not found"**
```bash
conda install nodejs -y
```

**"Module not found" (Python)**
```bash
pip install -r requirements.txt
```

**"Module not found" (Frontend)**
```bash
cd frontend && npm install
```

**Port 8000 already in use**
```bash
lsof -i :8000 && kill -9 <PID>
```

**Render cold start (~30 s)** — the frontend shows a "server waking up" message automatically and retries.

**Logs**: `logs/app.log` and terminal output. API docs at `http://localhost:8000/docs`.

---

## Roadmap

See [docs/cloud_migration_plan.md](docs/cloud_migration_plan.md) for the full plan.

| Step | Status | Description |
|---|---|---|
| 1 | ✅ | Tests & CI |
| 2 | ✅ | Frontend Redesign |
| 3 | ✅ | Backend Restructure + Clerk Auth |
| 4 | ✅ | Neon Database |
| 5 | ✅ | Deploy (Vercel + Render) |
| 6 | 🔜 | Mobile Responsive Support |
| 7 | — | Agent Pipeline (LangGraph ReAct) |
| 8 | — | Pinecone + Knowledge Base |

---

## License

Open source, not for commercial use.
