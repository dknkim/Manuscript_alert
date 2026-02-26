# Cloud Migration Plan

## Current State (Feb 2026)
- **Backend**: `server.py` → `backend/src/` (refactored from 688-line monolith into modular FastAPI routers)
- **Frontend**: Next.js 15 + React 19, built as static export served by FastAPI
- **Storage**: All local files — `config/settings.py`, `config/models/*.json`, `data/archive/archive.json`
- **No auth, no shared state** — each machine has its own data

## Step 0: Tests & CI (pre-migration)

Establish test coverage before changing storage or deployment — so we can verify nothing breaks during migration.

### Backend Tests (`tests/`)
- **API endpoint tests** (pytest + FastAPI TestClient): health, settings CRUD, models CRUD, backups CRUD, archive CRUD
- **Service unit tests**: journal matching, scoring logic, archive I/O
- **No network calls** — mock fetchers (PubMed, arXiv, bioRxiv) so tests are fast and deterministic

### GitHub Actions CI (`.github/workflows/ci.yml`)
- Trigger: push to main, all PRs
- Runner: `ubuntu-latest` (free for public repos, unlimited minutes)
- Steps: install Python deps → ruff lint → pytest
- Blocks merge on failure

### What This Catches
- Regressions when swapping file I/O for database calls (Step 1-2)
- Broken API contracts when deploying to Render (Step 3)
- Frontend/backend mismatches when splitting to Vercel + Render (Step 4)

## Target Architecture

```
Vercel ─── Frontend (Next.js)         FREE
              ↓
Render ─── Python Backend (FastAPI)   FREE (750 hrs/month)
              ↓
Neon ─── PostgreSQL                   FREE (512 MB)
```

### Why This Stack
- **Vercel**: Native Next.js hosting, auto-deploy from GitHub
- **Render**: Proper Python server (not serverless), no timeout limits — needed for LangGraph ReAct agents
- **Neon**: Hosted PostgreSQL, shared state across machines and team members
- Vercel serverless has 10s timeout on hobby plan — too short for LLM agent calls

### MCP Tools Available
- Neon: installed (`npx neonctl@latest init`)
- Render: installed (`claude mcp add render-mcp`)
- Both accessible from Claude Code for DB management and deployments

## Database Migration

### Tables Needed (Neon PostgreSQL)

| Current Local File | New Table | Notes |
|---|---|---|
| `config/settings.py` | `settings` | Single row, JSONB column for all settings |
| `config/backups/*.py` | `settings_versions` | Timestamped snapshots |
| `config/models/*.json` | `model_presets` | name, settings JSONB, created_at |
| `data/archive/archive.json` | `archived_papers` | title, authors, abstract, url, source, archived_date |

### Migration Steps
1. Create Neon project (`manuscript-alert`)
2. Create tables with schema above
3. Add `psycopg2` or `asyncpg` to `requirements.txt`
4. Add DB connection layer to `backend/src/services/` (replace file I/O with SQL)
5. Migrate existing local data into Neon
6. Remove local file storage code

## Backend Deployment (Render)

### Steps
1. Create `Dockerfile` or use Render's Python buildpack
2. Add `render.yaml` (blueprint) or configure via dashboard
3. Set environment variables: `DATABASE_URL` (Neon connection string)
4. Deploy from GitHub main branch
5. Update frontend API client to point to Render URL

### Considerations
- Free tier spins down after 15min idle (~30s cold start on wake)
- No timeout limit — suitable for LangGraph agents
- 750 hrs/month free (enough for always-on single instance)

## Frontend Deployment (Vercel)

### Steps
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend/`
3. Set `NEXT_PUBLIC_API_URL` env var to Render backend URL
4. Auto-deploys on push to main

### Changes Needed
- `frontend/src/lib/api.ts` — use `NEXT_PUBLIC_API_URL` instead of relative `/api/*` paths
- `next.config.ts` — remove `output: "export"` (Vercel handles SSR natively)

## Future: LangGraph Agent (from nextjs branch)

The `nextjs` branch has an experimental ReAct agent with:
- LangGraph cyclic agent graph
- Pinecone vector store (SPECTER2 embeddings)
- Dual LLM support (OpenAI + Anthropic)
- KB document management

This can be integrated after the cloud migration is complete. Render's no-timeout backend supports long-running agent cycles.

## Open Questions
- Do we need auth? (multi-user vs single shared instance)
- Keep `server.py` auto-build of frontend, or separate build steps in CI?
- KB_alz/ PDFs (78MB) — keep local or move to cloud storage?
