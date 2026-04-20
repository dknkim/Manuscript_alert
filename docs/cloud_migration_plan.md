# Cloud Migration Plan

## Roadmap Overview

| Step | What | Size | Status | API Keys Needed | Key Outcome |
|------|------|------|--------|-----------------|-------------|
| **1** | Tests & CI | S | ✅ Done | None | pytest + GitHub Actions, blocks regressions |
| **2** | Frontend Redesign | XL | ✅ Done | None | 3-column layout, new components, fresh aesthetics |
| **3** | Backend Restructuring | L | ✅ Done | None (Clerk added) | API versioning, pydantic-settings, SSE, KB stubs, Clerk auth |
| **4** | Neon Database | M | ✅ Done | `DATABASE_URL` | Replace local JSON/Python files with Postgres |
| **5** | Deploy | M | ✅ Done | None (free accounts) | Vercel (frontend) + Render (backend) |
| **6** | Mobile Responsive Support | M | Not started | None | Usable layout on phones/tablets before adding AI features |
| **7** | Agent Pipeline | XL | Not started | `ANTHROPIC_API_KEY` | LangGraph ReAct agents for intelligent paper review |
| **8** | Pinecone + KB | L | Not started | `PINECONE_API_KEY` (free signup) | Semantic search over PDFs and saved papers |

Steps 1-6 require **zero LLM API keys**. Steps 7-8 add AI features incrementally.

For detailed architecture, ReAct loop diagrams, and full dependency reference, see [architecture_reference.md](architecture_reference.md).

---

## Current State (Apr 2026)

- **Backend**: `server.py` → `backend/src/` (modular FastAPI routers under `/api/v1/`, services, Pydantic schemas, SSE progress streaming)
- **Frontend**: Next.js 16 + React 19 + TypeScript 5.9 + Tailwind CSS 4, deployed to Vercel (SSR, not static export)
- **Storage**: Neon Postgres (cloud). Local file fallback when `DATABASE_URL` is unset
- **Auth**: Clerk (Google/GitHub OAuth). JWT verified on every backend request; per-user data isolation via `users` table
- **Hosting**: Vercel (frontend) + Render free tier (backend, ~30 s cold start) + Neon (database)
- **Known gap**: essentially no responsive styles (~3 `sm:`/`md:` usages across the frontend, no viewport meta) — addressed in Step 6

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

## Step 1: Tests & CI ✅

**What shipped**: 60 pytest tests across health/settings/papers/models/backups/journal_utils/keyword_matcher plus `/api/v1/` variants. `.github/workflows/regression-tests.yml` runs ruff check + ruff format check + pytest + frontend vitest + `npm run build` + Playwright E2E (chromium) against a live backend/frontend pair. Exceeds the original plan which only required lint + pytest.

**Goal**: Establish test coverage before any major changes. Tests first = safe refactoring.

**No API keys needed.**

### Backend Tests (`tests/`)
- **API endpoint tests** (pytest + FastAPI TestClient): health, settings CRUD, models CRUD, backups CRUD, archive CRUD
- **Service unit tests**: journal matching, scoring logic, archive I/O
- **No network calls** — mock fetchers so tests are fast and deterministic

### GitHub Actions CI (`.github/workflows/regression-tests.yml`)
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

## Step 2: Frontend Redesign ✅

**What shipped**: All deps installed (`lucide-react`, `clsx`, `tailwind-merge`, `@microsoft/fetch-event-source`). `cn()` utility in `lib/utils.ts`. Routes: `/`, `/settings`, `/models`, `/kb`, `/sign-in`. UI primitives: `Card`, `Toggle`, `ModeSwitch`, `SourceBadge`, `ScoreIndicator`, `Spinner`, `Flash`. Feature components: `SearchPanel`, `PaperFeed`, `PaperCard`, `DashboardPanel`, `AgentActivityStream`. Hooks: `useSettings`, `usePaperSearch`, `useAgentStream`, `useKnowledgeBase`. Dark mode via `AppShell` toggle with `localStorage` persistence.

**Deviations**:
- `PaperDetailDrawer` from the plan was merged into `DashboardPanel`'s right column rather than built as a separate drawer component.
- Mobile/tablet responsive collapse from sub-step 2b was **not** implemented — promoted to its own Step 6.

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

## Step 3: Backend Restructuring ✅

**What shipped**: All `/api/v1/` routes (`health`, `settings`, `papers`, `models`, `backups`, `kb`) live alongside legacy `/api/` routes. `pydantic-settings` reads `.env` with `.env.example` committed. DI via `backend/src/api/deps.py` (`get_db_pool`, `get_settings_service`). Full SSE implementation in `backend/src/api/v1/papers.py` via `sse-starlette`, with every event type from the plan (`source_start`, `source_complete`, `source_error`, `batch_progress`, `scoring`, `complete`) defined in `backend/src/models/events.py`. Frontend `useAgentStream` + `AgentActivityStream` consume the stream. KB stubs return 503.

**Deviations** (additions beyond plan):
- **Clerk auth added.** JWT middleware in `backend/src/api/auth.py` verifies tokens via `CLERK_JWKS_URL`; `CurrentUser` dependency injected into every data route. Frontend wires `ClerkProvider` + `proxy.ts` (renamed per Next.js 16 convention) + `/sign-in` route. The plan deferred auth to "post-deploy if needed" — pulling it forward was a conscious choice to enable multi-user cloud deployment.
- New deps beyond plan: `PyJWT`, `cryptography` (for Clerk JWT verification).

**Loose end** (resolved Apr 2026): legacy `/api/*` routes fully removed. 5 route files deleted (`health.py`, `settings.py`, `papers.py`, `models.py`, `backups.py`), 5 legacy test files deleted, 5 ported to `/api/v1/` counterparts, plus new SSE test coverage for `/api/v1/papers/review` (5 tests). Test count: 60 → 62 after net delete/port. `backend/src/main.py` now registers `/api/v1/` routers only.

**Goal**: Align backend with `nextjs` branch patterns, prepare for cloud services.

**No API keys needed. No external services yet.**

### Changes
1. **API versioning**: Move routes under `/api/v1/` prefix
2. **Config migration**: Replace hardcoded `config.py` with `pydantic-settings` reading from `.env`
   - Add `.env.example` with all variables (empty values for optional ones)
   - `DATABASE_URL`, `PINECONE_API_KEY`, `ANTHROPIC_API_KEY` all optional at this stage
3. **Dependency injection**: Port `deps.py` pattern — services injected via FastAPI `Depends()`
4. **Pydantic models**: Port `Paper`, `ReviewRequest`, `SearchResponse`, `KBProject`, `KBDocument`, `AgentStep`
5. **SSE streaming with progress**: Add `POST /api/v1/papers/review` as an SSE endpoint that wraps the classic fetch but streams real-time progress events:
   - `source_start` / `source_complete` — when each fetcher (PubMed, arXiv, bioRxiv) starts/finishes, with paper counts
   - `batch_progress` — PubMed batch progress (e.g., "batch 3/10, 300 papers so far")
   - `source_error` — when a source fails (e.g., bioRxiv timeout)
   - `scoring` — when keyword matching / ranking begins
   - `complete` — final results payload
   - Frontend `AgentActivityStream` component wired to display these events
   - Frontend `useAgentStream` hook consumes the SSE stream
   - `SearchPanel` mode switch toggles between `/papers/fetch` (classic JSON) and `/papers/review` (SSE stream)
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

## Step 4: Neon Database ✅

**What shipped**: `backend/src/db/neon.py` (asyncpg pool, schema bootstrap, one-time data migration from local files) and `backend/src/db/models.py` (all SQL queries). Local file fallback preserved: when `DATABASE_URL` is unset, services read/write the original local paths. Auto-creates `users` row on first authenticated request.

**Deviation** (beyond plan): added a `users` table (not listed in the original schema) to support Clerk-based per-user data isolation. All data tables (`settings`, `settings_versions`, `model_presets`, `papers`) key off `user_id`.

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

## Step 5: Deploy ✅

**What shipped**: `render.yaml` blueprint (uvicorn on `$PORT`, health check at `/api/v1/health`, env vars for `DATABASE_URL`, `ALLOWED_ORIGINS`, `CLERK_JWKS_URL`, `CLERK_SECRET_KEY`, and placeholders for `ANTHROPIC_API_KEY` / `PINECONE_API_KEY`). `frontend/next.config.ts` no longer uses `output: "export"` (Vercel handles SSR). CORS reads `ALLOWED_ORIGINS` from env. Full walkthrough in `docs/deployment_guide.md`.

**Observed pain**: Render free tier's ~30 s cold start bleeds into first-load UX. Recent commits (`ccc61fb`, `e8f1d30`, `2e8d7f9`) added retry/auto-retry and graceful degradation in the frontend. A keep-alive pinger hitting `/api/v1/health` every 10 minutes remains an open option.

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

## Step 6: Mobile Responsive Support

**Goal**: Make the deployed site usable on phones and tablets. The app is live on Vercel — anyone sharing a paper link on Slack, email, or their phone currently lands on a broken desktop layout.

**No API keys needed. No external services.**

### Why here, before agents
Agents (Step 7) introduce long-running SSE streams and richer activity UI — both amplify mobile friction if the underlying layout is broken. Fixing the foundation now means Step 7 frontend work targets a layout that already works at every size.

### Current gaps
- `AppShell` header nav renders all items as inline pills — overflows on narrow screens
- Main page's 3-column layout (SearchPanel / PaperFeed / DashboardPanel) has no collapse behavior
- Settings/Models tables and forms are desktop-shaped
- Touch targets on icon buttons and toggles are below 44×44
- No `viewport` meta in `app/layout.tsx`
- No mobile viewport coverage in Playwright E2E
- Whole codebase has ~3 `sm:`/`md:` Tailwind usages — effectively zero responsive design

### Sub-steps

#### 6a: Foundations
- Add `viewport` export in `app/layout.tsx` (`width=device-width, initial-scale=1`, `themeColor` light/dark)
- Audit touch targets: icon buttons to ≥40×40, primary controls to ≥44 height
- Document breakpoint usage (`sm` 640, `md` 768, `lg` 1024, `xl` 1280) — default Tailwind is fine, just commit to using it consistently

#### 6b: Navigation
- Collapse `AppShell` nav to a hamburger drawer on `<md` (use `lucide-react` `Menu` icon)
- Compact title block on narrow screens; keep theme toggle + `UserButton` accessible
- Ensure active route state still reads clearly in drawer form

#### 6c: Layout collapse
- `/` page: stack SearchPanel → PaperFeed → DashboardPanel vertically on `<lg`, 2-column on `md`, 3-column on `lg+`
- DashboardPanel's selected-paper detail: full-screen sheet on mobile rather than a sidebar column
- `PaperCard`: reduce horizontal padding on small screens, wrap metadata rows, keep score badge prominent

#### 6d: Forms and tables
- Settings / Models pages: stack form fields, make tables horizontally scrollable with a visible scroll hint
- Keyword chips and source toggles: widen tap area, preserve spacing so fingers don't cross-tap

#### 6e: Streaming UX on mobile
- `AgentActivityStream`: collapsed-by-default on mobile with a compact "3 sources active" header; expand on tap
- Verify `@microsoft/fetch-event-source` reconnect behavior when the browser backgrounds the tab on iOS Safari

#### 6f: Testing
- Add Playwright projects for `iPhone 14` and `iPad Mini` viewports in `playwright.config.ts`
- Visual regression snapshots at each breakpoint (keep the existing `VR=1` opt-in pattern, don't block CI)
- One round of manual QA on real iOS Safari + Android Chrome before marking this step done

### Decisions
- **PWA manifest + install prompt?** Defer. No clear demand, adds icons/service-worker surface for little gain at v1.
- **Bottom tab bar vs hamburger?** Hamburger — only 4 nav items, bottom bar eats scarce vertical space on already-cramped mobile screens.
- **Tablet portrait: 2-column or 3-column?** 2-column on `md` (tablets in portrait), 3-column only at `lg+` (1024 px +).

---

## Step 7: Agent Pipeline

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
- `AgentActivityStream` + `useAgentStream` already consume Step 3's progress-event stream — the Step 7 work is adding richer agent-step events on top of the existing SSE channel, not building the stream from scratch
- Mode switch (classic/agent) toggles between `/papers/search` and `/papers/review`

### Notes
- OpenAI support optional — `model_factory.py` defaults to Anthropic
- `agent_max_cycles: 15` prevents infinite loops
- ToolErrorMiddleware makes agents resilient to tool failures
- LangSmith tracing optional (`LANGCHAIN_TRACING_V2=false` by default)

---

## Step 8: Pinecone + Knowledge Base

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
- `/kb` route already exists (disabled in nav); `useKnowledgeBase` hook is scaffolded. Step 8 work is wiring them to the real API once the 503 stubs are replaced
- KB project selector in SearchPanel (for agent mode)

### Considerations
- SPECTER2 model download is ~500 MB on first load (cached after)
- `torch` via conda: `conda install pytorch cpuonly -c pytorch`
- Pinecone free tier: 2 GB, 100K vectors — sufficient for single-user KB
- Pin `transformers>=4.40.0,<4.49.0` to avoid torch version conflicts

---

## Open Questions

### Resolved during Steps 3–5
- **Auth**: went with Clerk + multi-user isolation in Neon (pulled forward from "post-deploy if needed"). Each logged-in user gets their own `users` row and data scope.
- **`server.py` auto-build**: kept for local dev; CI uses separate `npm run build`.
- **Models tab**: kept, DB-backed via `model_presets` table.

### Still open
| Question | Affects | Recommendation |
|----------|---------|----------------|
| KB_alz/ PDFs (78 MB): keep local or move to cloud storage (S3/R2)? | Step 8 | **Keep local for now.** Revisit when KB is implemented. Cloud storage only worth it if usage grows beyond a single researcher. |
| Render cold start (~30 s): live with it, or add keep-alive pinger, or upgrade to paid? | Step 5 follow-up | Cheapest fix is a cron pinger hitting `/api/v1/health` every 10 min — closes the papercut without paid tier. Worth doing before Step 7 so agent runs don't start with a cold backend. |
| ~~Remove legacy `/api/*` routes?~~ | ~~Step 3 cleanup~~ | ✅ Resolved Apr 2026 — legacy routes + tests removed, ports + SSE coverage added. |
| `PaperDetailDrawer` as its own component vs embedded in `DashboardPanel`? | Step 2 / Step 6 | Revisit during Step 6 — a mobile bottom sheet is a natural place to split this out. |
