# Cloud Migration Plan

## Roadmap Overview

| Step | What | Size | API Keys Needed | Key Outcome |
|------|------|------|-----------------|-------------|
| **1** | Tests & CI | S | None | pytest + GitHub Actions, blocks regressions |
| **2** | Frontend Redesign | XL | None | 3-column layout, new components, fresh aesthetics |
| **3** | Backend Restructuring | L | None | API versioning, pydantic-settings, SSE shell, KB stubs |
| **4** | Neon Database | M | `DATABASE_URL` (free signup) | Replace local JSON/Python files with Postgres |
| **5** | Deploy | M | None (free accounts) | Vercel (frontend) + Render (backend) |
| **6** | Agent Pipeline | XL | `ANTHROPIC_API_KEY` | LangGraph ReAct agents for intelligent paper review |
| **7** | Pinecone + KB | L | `PINECONE_API_KEY` (free signup) | Semantic search over PDFs and saved papers |

Steps 1-5 require **zero LLM API keys**. Steps 6-7 add AI features incrementally.

For detailed architecture, ReAct loop diagrams, and full dependency reference, see [architecture_reference.md](architecture_reference.md).

---

## Current State (Feb 2026)

- **Backend**: `server.py` → `backend/src/` (modular FastAPI routers, services, Pydantic schemas)
- **Frontend**: Next.js 16 + React 19 + TypeScript 5.9 + Tailwind CSS 4, static export served by FastAPI
- **Storage**: All local files — `config/settings.py`, `config/models/*.json`, `data/archive/archive.json`
- **No auth, no external services** — runs entirely offline on a single machine

## Reference: `nextjs` Branch

The `nextjs` branch is our target reference implementation. It has:
- 3-column AppShell layout (SearchPanel / PaperFeed / DashboardPanel)
- Component split: `features/` + `ui/` + custom hooks
- API versioning (`/api/v1/`)
- LangGraph ReAct agent pipeline (7 subagents)
- Neon Postgres (asyncpg) for persistent storage
- Pinecone vector store + SPECTER2 embeddings for KB
- SSE streaming for real-time agent progress
- Knowledge Base page (`/kb`) — PDF upload, semantic search

### What `main` has that's better/newer
- Next.js 16 (vs 15 on nextjs)
- Models tab (preset management) — dropped in nextjs
- Backup management UI
- Cleaner backend module layout (`backend/src/api/` flat vs `v1/` nested)

## Target Architecture

```
Vercel ─── Frontend (Next.js 16)        FREE
              ↓
Render ─── Python Backend (FastAPI)     FREE (750 hrs/month)
              ↓
Neon ─── PostgreSQL                     FREE (512 MB)
              ↓
Pinecone ─── Vector Store               FREE (2 GB)
```

### External Service Requirements

| Service | Free Tier | API Key Needed | Required For |
|---------|-----------|----------------|--------------|
| Vercel | Yes (hobby) | No (GitHub auth) | Frontend hosting |
| Render | Yes (750 hrs/mo) | No (GitHub auth) | Backend hosting |
| Neon | Yes (512 MB) | Connection string | Database (Step 4) |
| Anthropic | Pay-per-use | `ANTHROPIC_API_KEY` | Agent pipeline (Step 6) |
| Pinecone | Yes (2 GB) | `PINECONE_API_KEY` | KB vector search (Step 7) |

---

## Step 1: Tests & CI

**Goal**: Establish test coverage before any major changes. Tests first = safe refactoring.

**No API keys needed.**

### Backend Tests (`tests/`)
- **API endpoint tests** (pytest + FastAPI TestClient): health, settings CRUD, models CRUD, backups CRUD, archive CRUD
- **Service unit tests**: journal matching, scoring logic, archive I/O
- **No network calls** — mock fetchers so tests are fast and deterministic

### GitHub Actions CI (`.github/workflows/ci.yml`)
- Trigger: push to main, all PRs
- Runner: `ubuntu-latest`
- Steps: install Python deps → ruff lint → pytest
- Blocks merge on failure

### What This Catches
- Regressions during frontend redesign (Step 2)
- Broken API contracts when restructuring backend (Step 3)
- Storage migration issues when swapping to Neon (Step 4)
- Frontend/backend mismatches when deploying (Step 5)

---

## Step 2: Frontend Redesign

**Goal**: Port the `nextjs` branch UI structure into `main`, redesign with fresh aesthetics.

**No API keys needed. Fully local.**

### Sub-steps

#### 2a: Project Setup
- Install new deps: `lucide-react`, `clsx`, `tailwind-merge`, `@microsoft/fetch-event-source`
- Create `cn()` utility (`lib/utils.ts`) — clsx + tailwind-merge wrapper
- Set up directory structure: `components/features/`, `components/ui/`, `components/layout/`, `hooks/`

#### 2b: Layout & Routing
- Build `AppShell` — 3-column grid layout with navigation
- Add file-based routing: `/settings`, `/kb` (shell), `/models`
- Responsive breakpoints (collapse to 1-2 columns on mobile/tablet)

#### 2c: UI Primitives
- Port reusable components from `nextjs`: `Card`, `Toggle`, `ModeSwitch`, `SourceBadge`, `ScoreIndicator`, `Spinner`, `Flash`
- These are building blocks used by feature components

#### 2d: Core Components
- `SearchPanel` — source toggles, search mode, days back, mode switch (classic/agent)
- `PaperFeed` — paper list with loading/error/empty states
- `PaperCard` — redesigned with score badge, source color, expand/collapse
- `DashboardPanel` — stats, selected paper detail
- `PaperDetailDrawer` — expanded paper view
- `AgentActivityStream` — real-time agent steps (shell until Step 6)

#### 2e: Feature Migration
- Port Models tab from `main` → `/models` route
- Port Archive UI → integrate into DashboardPanel or sub-view
- Port Statistics into DashboardPanel
- Extract state into custom hooks: `usePaperSearch`, `useSettings`, `useAgentStream`, `useKnowledgeBase`

#### 2f: Visual Polish
- Fresh aesthetic direction (not the generic slate/indigo from `nextjs`)
- Distinctive typography, color palette, micro-interactions
- Dark mode support

### Decisions
- **Keep Models tab** from `main` → Yes, port as `/models` route
- **Keep Archive UI** from `main` → Yes, integrate into DashboardPanel or sub-view

---

## Step 3: Backend Restructuring

**Goal**: Align backend with `nextjs` branch patterns, prepare for cloud services.

**No API keys needed. No external services yet.**

### Changes
1. **API versioning**: Move routes under `/api/v1/` prefix
2. **Config migration**: Replace hardcoded `config.py` with `pydantic-settings` reading from `.env`
   - Add `.env.example` with all variables (empty values for optional ones)
   - `DATABASE_URL`, `PINECONE_API_KEY`, `ANTHROPIC_API_KEY` all optional at this stage
3. **Dependency injection**: Port `deps.py` pattern — services injected via FastAPI `Depends()`
4. **Pydantic models**: Port `Paper`, `ReviewRequest`, `SearchResponse`, `KBProject`, `KBDocument`, `AgentStep`
5. **SSE endpoint shell**: Add `POST /api/v1/papers/review` — initially wraps classic search
6. **KB API stubs**: Add `/api/v1/kb/` routes — return 503 until Step 7

### New Backend Dependencies
- `pydantic-settings` — env-based config
- `sse-starlette` — Server-Sent Events
- `httpx` — async HTTP client
- `python-dotenv` — `.env` file loading
- `python-multipart` — file upload support

### Backward Compatibility
- Keep existing `/api/papers/fetch` working during transition
- Frontend API client updated to use `/api/v1/` endpoints
- Old routes deprecated, removed after frontend is updated

---

## Step 4: Neon Database

**Goal**: Replace local file storage with Neon Postgres.

**Needs: Neon account (free, no credit card). Provides `DATABASE_URL`.**

### Tables
Full schema in [architecture_reference.md](architecture_reference.md#database-schema-neon).

| Current Local File | New Table | Notes |
|---|---|---|
| `data/archive/archive.json` | `papers` | With `archived` boolean flag |
| `config/settings.py` | `settings` | Single row, JSONB column |
| `config/backups/*.py` | `settings_versions` | Timestamped snapshots |
| `config/models/*.json` | `model_presets` | name + JSONB data |
| _(new in Step 7)_ | `kb_projects` | Knowledge base projects |
| _(new in Step 7)_ | `kb_documents` | KB document metadata |

### New Backend Dependencies
- `asyncpg` — async Postgres driver

### Migration Steps
1. Create Neon project via MCP tool or dashboard
2. Run schema bootstrap (`CREATE TABLE IF NOT EXISTS`)
3. Port `db/neon.py` (connection pool) and `db/models.py` (SQL queries) from `nextjs`
4. Replace file I/O in services with DB calls
5. Migrate existing local data into Neon
6. Keep local file fallback for offline development (`DATABASE_URL` optional)

---

## Step 5: Deploy

**Goal**: Frontend on Vercel, backend on Render, database on Neon.

**Needs: Vercel + Render accounts (free, GitHub auth).**

### Vercel (Frontend)
1. Connect GitHub repo, set root directory to `frontend/`
2. Set `NEXT_PUBLIC_API_URL` to Render backend URL
3. Remove `output: "export"` from `next.config.ts` (Vercel handles SSR)
4. Auto-deploys on push to main

### Render (Backend)
1. Add `Dockerfile` or `render.yaml` blueprint
2. Set environment variables: `DATABASE_URL` (Neon)
3. Deploy from GitHub main branch
4. Configure health check: `GET /api/v1/health`

### Considerations
- Render free tier spins down after 15 min idle (~30s cold start)
- Keep `server.py` local dev mode (serves frontend static build + API on port 8000)
- CORS: allow both `localhost:3000` (dev) and Vercel domain (prod)

### CI/CD
- GitHub Actions: lint + test on PR (from Step 1)
- Vercel: auto-deploy frontend on merge to main
- Render: auto-deploy backend on merge to main

---

## Step 6: Agent Pipeline

**Goal**: Port LangGraph ReAct agent system from `nextjs` branch.

**Needs: `ANTHROPIC_API_KEY` (pay-per-use).**

### Architecture
```
User Request → Resolver Agent → SearchPlan
    → Parallel Fetcher Agents (PubMed, arXiv, bioRxiv) → Raw papers
    → KB Analyst Agent → Score papers against KB (needs Step 7)
    → Dedup Agent → Remove duplicates
    → Summarizer Agent → Trends & themes
    → SSE Stream → Frontend
```

Full ReAct loop diagram in [architecture_reference.md](architecture_reference.md#how-the-react-agent-loop-works).

### 7 Subagents
| Agent | Purpose | Tools |
|-------|---------|-------|
| Resolver | Parse request → SearchPlan | config_tools |
| PubMed Fetcher | Fetch from PubMed API | fetcher_tools |
| arXiv Fetcher | Fetch from arXiv API | fetcher_tools |
| bioRxiv Fetcher | Fetch from bioRxiv/medRxiv | fetcher_tools |
| KB Analyst | Score papers vs KB docs ("Reverse RAG") | kb_tools, analysis_tools |
| Dedup | Remove duplicate papers | analysis_tools |
| Summarizer | Generate trends summary | summary_tools |

### New Backend Dependencies
- `langchain` — LLM abstraction layer
- `langchain-anthropic` — Claude integration
- `langgraph` — cyclic ReAct agent orchestration

### Frontend Integration
- Wire `AgentActivityStream` component (shell from Step 2) to real SSE endpoint
- `useAgentStream` hook consumes SSE events
- Mode switch (classic/agent) toggles between `/papers/search` and `/papers/review`

### Notes
- OpenAI support optional — `model_factory.py` defaults to Anthropic
- `agent_max_cycles: 15` prevents infinite loops
- ToolErrorMiddleware makes agents resilient to tool failures
- LangSmith tracing optional (`LANGCHAIN_TRACING_V2=false` by default)

---

## Step 7: Pinecone + Knowledge Base

**Goal**: Enable semantic search over uploaded PDFs and saved papers.

**Needs: `PINECONE_API_KEY` (free tier, 2 GB).**

### How It Works
```
PDFs/Papers → SPECTER2 (local, no API key) → 768-dim vectors → Pinecone (stores + searches)
```

See [architecture_reference.md](architecture_reference.md#how-pinecone--specter2-work-together) for detailed explanation.

### New Backend Dependencies
- `pinecone` — vector store client
- `sentence-transformers` — local embedding model loader
- `transformers` — HuggingFace tokenization/model loading
- `torch` — ML runtime (**install via conda on macOS**)
- `pymupdf` (fitz) — PDF text extraction
- `numpy` — embedding math (cosine similarity, normalization)

### Frontend Integration
- Wire `/kb` page to real API endpoints (stubs from Step 3)
- `useKnowledgeBase` hook for project CRUD, PDF upload, search
- KB project selector in SearchPanel (for agent mode)

### Considerations
- SPECTER2 model download is ~500 MB on first load (cached after)
- `torch` via conda: `conda install pytorch cpuonly -c pytorch`
- Pinecone free tier: 2 GB, 100K vectors — sufficient for single-user KB
- Pin `transformers>=4.40.0,<4.49.0` to avoid torch version conflicts

---

## Open Questions

| Question | Affects | Recommendation |
|----------|---------|----------------|
| Auth: multi-user vs single shared instance? | Steps 4-5 | **Single-user for MVP** (Steps 1-5). Add optional auth post-deploy if needed. Avoids scope creep. |
| KB_alz/ PDFs (78 MB): keep local or move to cloud storage (S3/R2)? | Step 7 | **Keep local for now.** Revisit when KB is implemented in Step 7. Cloud storage only needed if multi-user. |
| Keep `server.py` auto-build for local dev, or separate build steps in CI? | Step 5 | **Both.** Keep auto-build for local dev convenience. CI uses separate `npm run build` step. |
| Models tab: DB-backed feature, or superseded by agent pipeline? | Steps 2, 4 | **Keep and port to DB.** Useful for saving keyword/settings presets regardless of agent mode. |
| Render cold start (~30s): acceptable, or upgrade to paid? | Step 5 | **Start free.** 30s cold start is fine for a personal research tool. Upgrade only if it becomes a real pain point. |
