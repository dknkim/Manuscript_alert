# Architecture Reference

Detailed technical reference for the cloud migration. See [cloud_migration_plan.md](cloud_migration_plan.md) for the step-by-step roadmap.

---

## Current Architecture (main branch)

```
Browser ── http://localhost:8000 ──▶ FastAPI (Uvicorn)
                                          │
                  ┌───────────────────────┼──────────────────┐
                  │                       │                  │
            Static Files            API Routes          SPA Fallback
         (frontend/out/_next)       (/api/*)            (index.html)
                                          │
              ┌──────────┬────────────┬───┴──────┬──────────┐
              │          │            │          │          │
           /health  /settings     /papers    /models   /backups
                        │            │          │          │
                        ▼            ▼          ▼          ▼
                   settings     paper_service  JSON I/O  settings
                   _service     archive_service           _service
                                     │
                          ┌──────────┼──────────┐
                          │          │          │
                       PubMed     arXiv    bioRxiv/
                       Fetcher    Fetcher   medRxiv
                          │          │      Fetcher
                          ▼          ▼          ▼
                      PubMed API  arXiv API  bioRxiv API

Storage (local files):
  backend/config/settings.py        ← current settings
  backend/config/backups/           ← auto-snapshots
  backend/config/models/*.json      ← model presets
  backend/data/archive/             ← archived papers
```

**Key characteristics:**
- Single process — FastAPI serves both the API and the Next.js static export
- All Python code consolidated under `backend/src/` (fetchers, processors, services, utils)
- Singletons instantiated at startup in `config.py` (fetchers, keyword_matcher, settings_service)
- Paper fetch uses `concurrent.futures` for parallel source queries
- Results cached in memory (`_fetch_cache`) for CSV export reuse
- No auth, no external services — runs entirely offline on a single machine
- Step 3 will move routes under `/api/v1/` prefix — current flat `/api/` routes are pre-versioning

**Target state** (after Steps 1-7):
```
Vercel (frontend) → Render (FastAPI + LangGraph agents) → Neon (Postgres) + Pinecone (vectors)
```
SSE streaming replaces polling; `/api/v1/` prefix; pydantic-settings config; agent mode optional (classic mode still works without API keys). Full target diagram in [cloud_migration_plan.md](cloud_migration_plan.md#target-architecture).

---

## Architectural Audit (vs `nextjs` branch)

Everything from the `nextjs` branch is accounted for in the migration plan.

| Component | Step | Source | Notes |
|-----------|------|--------|-------|
| 7 LangGraph ReAct agents | 6 | `nextjs` | resolver, 3 fetchers, kb_analyst, dedup, summarizer |
| Agent tools (6 modules) | 6 | `nextjs` | fetcher_tools, config_tools, kb_tools, analysis_tools, summary_tools, pdf_tools |
| Agent prompts (5 files) | 6 | `nextjs` | Each agent has a system prompt defining its role |
| 3-layer pipeline (pipeline.py) | 6 | `nextjs` | Deterministic → Agents → Deterministic |
| ToolErrorMiddleware | 6 | `nextjs` | Wraps tools so failures return error strings instead of crashing the agent loop |
| PDF ingestion pipeline | 7 | `nextjs` | Download → extract text (PyMuPDF) → chunk with overlap → embed → store in Pinecone |
| SSE streaming | 3 (shell), 6 (wired) | `nextjs` | pipeline_helpers.py formats LangGraph events into SSE dicts |
| Neon DB (neon.py + models.py) | 4 | `nextjs` | asyncpg connection pool + raw SQL data access |
| Pinecone vectorstore | 7 | `nextjs` | Abstract base class + factory pattern + PineconeStore implementation |
| SPECTER2 embeddings | 7 | `nextjs` | Local model, no API key needed |
| pydantic-settings config | 3 | `nextjs` | `.env`-based configuration replacing hardcoded paths |
| Frontend 3-column layout | 2 | `nextjs` | AppShell with SearchPanel / PaperFeed / DashboardPanel |
| KB page | 2 (shell), 7 (wired) | `nextjs` | `/kb` route for knowledge base management |
| pytest + CI | 1 | new | Backend API tests, service unit tests, GitHub Actions |

---

## How the ReAct Agent Loop Works

ReAct = **Re**asoning + **Act**ion. Each agent is a cyclic loop where the LLM reasons about what to do, calls a tool, observes the result, then decides whether to call more tools or produce a final answer.

```
User: "Find recent Alzheimer's papers"
        │
        ▼
┌─ Resolver Agent (ReAct) ─────────────────────┐
│  Thought: Need to check user's config...      │
│  Action:  get_user_config()                   │
│  Observe: {keywords: ["alzheimer's", ...]}    │
│  Thought: Check KB for context...             │
│  Action:  get_kb_summary("project-123")       │
│  Observe: {total_documents: 15, ...}          │
│  Thought: I have enough info for a plan.      │
│  Output:  SearchPlan JSON                     │
└───────────────────────────────────────────────┘
        │
        ▼ (parallel)
┌─ PubMed Agent ─┐ ┌─ arXiv Agent ─┐ ┌─ bioRxiv Agent ─┐
│ Action: fetch() │ │ Action: fetch()│ │ Action: fetch()  │
│ Observe: papers │ │ Observe: papers│ │ Observe: papers  │
└─────────────────┘ └────────────────┘ └──────────────────┘
        │                   │                    │
        └───────────┬───────┘────────────────────┘
                    ▼
┌─ KB Analyst Agent (ReAct — "Reverse RAG") ────┐
│  For each paper:                               │
│  Action:  search_kb(paper.abstract)            │
│  Observe: similar KB docs with scores          │
│  Action:  compute_similarity(paper, kb_doc)    │
│  Observe: 0.87                                 │
│  Thought: Highly relevant to existing research │
│  Output:  {kb_score: 0.87, classification: ...}│
└────────────────────────────────────────────────┘
        │
        ▼
┌─ Dedup Agent (ReAct) ─────────────────────────┐
│  Action:  find_duplicates(all_papers)          │
│  Observe: 3 duplicate groups found             │
│  Action:  merge_paper_records(papers, groups)  │
│  Output:  deduplicated list                    │
└────────────────────────────────────────────────┘
        │
        ▼
┌─ Summarizer Agent (ReAct) ────────────────────┐
│  Action:  generate_summary(papers)             │
│  Action:  identify_trends(papers)              │
│  Action:  write_scratchpad("Key themes...")    │
│  Output:  themes, trends, overview             │
└────────────────────────────────────────────────┘
```

### Key Design Decisions

- **`agent_max_cycles: 15`** — safety limit prevents infinite tool-calling loops
- **ToolErrorMiddleware** — if a tool crashes, the LLM gets an error string back and can reason about it (retry, skip, try a different approach). This is what makes the loop resilient.
- **Classic mode bypass** — without an `ANTHROPIC_API_KEY`, the entire agent layer is skipped. Classic mode calls fetchers directly, identical to current `main` behavior. The UI mode switch lets users choose.
- **3-layer pipeline** — Layer 1 (parse/validate) and Layer 3 (sort/format) are deterministic Python. Only Layer 2 uses LLM agents. This keeps the pipeline predictable at the boundaries.

---

## How Pinecone + SPECTER2 Work Together

Pinecone is a hosted vector database — it stores numerical representations of text and finds semantically similar documents. SPECTER2 is the model that creates those representations.

```
Your PDFs / Papers
      ↓
SPECTER2 (local model, runs on CPU, no API key)
      ↓
768-dimensional vectors (numbers representing meaning)
      ↓
Pinecone stores these vectors (hosted, free tier: 2 GB)
      ↓
When searching: "Find papers similar to X"
      ↓
SPECTER2 converts query X to a vector
      ↓
Pinecone finds nearest vectors (cosine similarity)
      ↓
Returns ranked results with similarity scores
```

### Why not just use Postgres for this?

Regular databases do exact matching (WHERE title = 'X'). Vector databases do **approximate nearest neighbor** search — "find me the 10 documents whose meaning is closest to this query." Postgres can do this with pgvector, but Pinecone is purpose-built and faster at scale.

### KB Project Isolation

Each KB project gets its own Pinecone **namespace** within a single index. This means projects don't interfere with each other's search results, but share the same billing/storage quota.

---

## New Dependencies Reference

### Step 1: Tests & CI

No new production dependencies. Dev/test only:

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `pytest` | Python test framework | Run backend unit and integration tests |
| `httpx` | Async HTTP client (promoted to prod dep in Step 3) | FastAPI `TestClient` requires it for async tests |
| `pytest-asyncio` | Async test support for pytest | Test async FastAPI endpoints |

### Step 2: Frontend

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `lucide-react` | Icon library (tree-shakeable SVG icons) | Replace inline SVGs, consistent icon system |
| `clsx` | Conditional className strings (`clsx('foo', condition && 'bar')`) | Cleaner conditional styling in JSX |
| `tailwind-merge` | Intelligently merges Tailwind classes (avoids conflicts) | Used with clsx via `cn()` utility |
| `@microsoft/fetch-event-source` | SSE client that works with POST requests | Needed for agent mode streaming (Step 6) |

### Step 3: Backend Restructuring

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `pydantic-settings` | Read config from `.env` files + environment variables into typed Python objects | Replace hardcoded paths in `config.py` |
| `sse-starlette` | Server-Sent Events support for FastAPI/Starlette | Stream agent progress to frontend in real-time |
| `httpx` | Async HTTP client (like requests, but async-native) | Used by agent tools for async PDF downloads |
| `python-dotenv` | Load `.env` file into `os.environ` | Development convenience, pydantic-settings reads from it |
| `python-multipart` | Parse multipart form data (file uploads) | Required by FastAPI for `UploadFile` endpoints |

### Step 4: Neon Database

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `asyncpg` | Async PostgreSQL driver (pure Python, fast) | Non-blocking DB queries from FastAPI async handlers |

### Step 6: Agent Pipeline

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `langchain` | LLM abstraction layer — unified interface for prompts, tools, chains | Foundation for agent tool definitions and message types |
| `langchain-anthropic` | Claude integration for LangChain (`ChatAnthropic` model class) | Connect LangGraph agents to Anthropic API |
| `langgraph` | Agent orchestration framework — builds cyclic ReAct graphs | Core of the agent pipeline: each subagent is a LangGraph react agent |

### Step 7: Pinecone + Knowledge Base

| Package | What it does | Why we need it |
|---------|-------------|----------------|
| `pinecone` | Pinecone Python SDK (vector database client) | Store and query document embeddings |
| `sentence-transformers` | Load and run transformer models for text embeddings | Wraps SPECTER2 model with a simple `.encode()` API |
| `transformers` | HuggingFace model loading and tokenization | Required by sentence-transformers under the hood |
| `torch` | PyTorch ML runtime | Required by transformers for model inference. **Install via conda on macOS** |
| `pymupdf` (fitz) | PDF text extraction (fast, no external deps) | Extract text from uploaded PDFs for chunking and embedding |
| `numpy` | Numerical array operations | Cosine similarity computation, embedding normalization |

### Dependency Notes
- `torch` must be installed via conda, not pip, on macOS: `conda install pytorch cpuonly -c pytorch`
- Pin `transformers>=4.40.0,<4.49.0` to avoid torch version conflicts (CVE-2025-32434)
- SPECTER2 model (`allenai/specter2_base`) is ~500 MB on first download, cached in `~/.cache/huggingface/`

---

## Database Schema (Neon)

Full SQL from `nextjs` branch `db/neon.py`, extended with tables for features kept from `main`.

```sql
-- ============================================================
-- STEP 4: Core tables (created during Neon setup)
-- ============================================================

-- Papers (replaces archive.json + in-memory results)
CREATE TABLE papers (
    id              serial PRIMARY KEY,
    external_id     text UNIQUE NOT NULL,
    source          text,
    title           text,
    abstract        text,
    authors         text[],
    journal         text,
    published_date  date,
    relevance_score double precision,
    matched_keywords text[],
    url             text,
    doi             text,
    is_high_impact  boolean DEFAULT false,
    created_at      timestamptz DEFAULT now(),
    archived        boolean DEFAULT false
);
CREATE INDEX idx_papers_source ON papers (source);
CREATE INDEX idx_papers_published_date ON papers (published_date);

-- Settings (replaces config/settings.py)
CREATE TABLE settings (
    id         serial PRIMARY KEY,
    data       jsonb NOT NULL,
    updated_at timestamptz DEFAULT now()
);

-- Settings versions (replaces config/backups/*.py)
CREATE TABLE settings_versions (
    id         serial PRIMARY KEY,
    data       jsonb NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Model presets (replaces config/models/*.json)
CREATE TABLE model_presets (
    id         serial PRIMARY KEY,
    name       text UNIQUE NOT NULL,
    data       jsonb NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- ============================================================
-- STEP 7: Knowledge Base tables (created when KB is enabled)
-- ============================================================

-- KB projects
CREATE TABLE kb_projects (
    id          text PRIMARY KEY,
    name        text NOT NULL,
    description text,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

-- KB documents
CREATE TABLE kb_documents (
    id                 text PRIMARY KEY,
    project_id         text REFERENCES kb_projects(id),
    title              text,
    source_type        text,
    filename           text,
    abstract           text,
    included_in_search boolean DEFAULT false,
    chunk_count        integer DEFAULT 0,
    metadata           jsonb DEFAULT '{}'::jsonb,
    created_at         timestamptz DEFAULT now()
);
CREATE INDEX idx_kb_documents_project_id ON kb_documents (project_id);
```

> **Schema sync:** This SQL is the reference copy. When Step 4 is implemented, the bootstrap script in `backend/src/db/neon.py` must match this schema. Update both places together.

---

## Files to Create or Port (by step)

### Step 1: Tests & CI (new files)
- `tests/conftest.py` → shared fixtures (TestClient, mock settings, mock fetchers)
- `tests/test_health.py` → health endpoint
- `tests/test_settings.py` → settings GET/PUT
- `tests/test_papers.py` → fetch, archive, export (mocked fetchers)
- `tests/test_models.py` → model preset CRUD
- `tests/test_backups.py` → backup CRUD
- `tests/test_keyword_matcher.py` → keyword matching & scoring unit tests
- `tests/test_journal_utils.py` → journal name matching unit tests
- `.github/workflows/regression-tests.yml` → ruff lint + pytest + frontend tests + E2E on push/PR

### Step 2: Frontend Redesign (port from `nextjs`)
- `frontend/src/lib/utils.ts` → `cn()` utility (clsx + tailwind-merge)
- `frontend/src/components/ui/` → Card, Toggle, ModeSwitch, SourceBadge, ScoreIndicator, Spinner, Flash
- `frontend/src/components/layout/AppShell.tsx` → 3-column grid layout with nav
- `frontend/src/components/features/SearchPanel.tsx` → source toggles, search mode, days back
- `frontend/src/components/features/PaperFeed.tsx` → paper list with loading/error states
- `frontend/src/components/features/PaperCard.tsx` → redesigned card with score badge
- `frontend/src/components/features/DashboardPanel.tsx` → stats, selected paper detail
- `frontend/src/components/features/PaperDetailDrawer.tsx` → expanded paper view
- `frontend/src/components/features/AgentActivityStream.tsx` → shell (wired in Step 6)
- `frontend/src/hooks/usePaperSearch.ts` → paper fetch state management
- `frontend/src/hooks/useSettings.ts` → settings state management
- `frontend/src/hooks/useAgentStream.ts` → SSE stream consumer (shell until Step 6)
- `frontend/src/hooks/useKnowledgeBase.ts` → KB state management (shell until Step 7)
- `frontend/src/app/settings/page.tsx` → settings route
- `frontend/src/app/kb/page.tsx` → knowledge base route (shell)
- `frontend/src/app/models/page.tsx` → model presets route

### Step 3: Backend Restructuring (port from `nextjs`)
- `backend/src/config.py` → rewrite with pydantic-settings
- `backend/src/api/deps.py` → dependency injection
- `backend/src/api/v1/` → versioned route modules (health, papers, settings, export, kb)
- `backend/src/models/` → `paper.py`, `settings.py`, `events.py`, `kb.py`

### Step 4: Neon Database (port from `nextjs`)
- `backend/src/db/neon.py` → connection pool + schema bootstrap
- `backend/src/db/models.py` → raw SQL data access layer

### Step 6: Agent Pipeline (port from `nextjs`)
- `backend/src/agents/graph.py` → agent registry
- `backend/src/agents/middleware.py` → ToolErrorMiddleware
- `backend/src/agents/model_factory.py` → LLM provider factory (Anthropic/OpenAI)
- `backend/src/agents/prompts/` → resolver, fetcher, kb_analyst, dedup, summarizer
- `backend/src/agents/subagents/` → 7 agent constructors
- `backend/src/agents/tools/` → 6 tool modules
- `backend/src/services/pipeline.py` → 3-layer orchestrator
- `backend/src/services/pipeline_helpers.py` → SSE event formatting

### Step 7: Pinecone + Knowledge Base (port from `nextjs`)
- `backend/src/vectorstore/base.py` → abstract VectorStore interface
- `backend/src/vectorstore/factory.py` → backend selection
- `backend/src/vectorstore/pinecone_store.py` → Pinecone implementation
- `backend/src/services/embedding_service.py` → async SPECTER2 wrapper
- `backend/src/services/kb_service.py` → KB business logic
