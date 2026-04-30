# DevOps Reference — Manuscript Alert

> Last updated: 2026-04-29

---

## Table of Contents

1. [Infrastructure Overview](#1-infrastructure-overview)
2. [Service Inventory](#2-service-inventory)
3. [Environment Variables](#3-environment-variables)
4. [Local Development](#4-local-development)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Deployment](#6-deployment)
7. [Database](#7-database)
8. [Keep-Alive Strategy](#8-keep-alive-strategy)
9. [Observability & Logging](#9-observability--logging)
10. [Secrets Management](#10-secrets-management)
11. [Runbook: Common Operations](#11-runbook-common-operations)

---

## 1. Infrastructure Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        GitHub (source of truth)                   │
│   main branch ──→ push/PR ──→ GitHub Actions (CI)                │
└─────────────────────────────┬────────────────────────────────────┘
                              │ deploy (auto, on green CI)
            ┌─────────────────┴──────────────────┐
            │                                    │
            ▼                                    ▼
   ┌─────────────────┐                ┌─────────────────────┐
   │     Vercel      │                │       Render        │
   │  (Frontend)     │                │     (Backend)       │
   │  Next.js SSR    │◄──── HTTPS ───►│  FastAPI / uvicorn  │
   │  Port: 443      │   /api/v1/*    │  Port: $PORT (10000)│
   └─────────────────┘                └────────┬────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌──────────────┐         ┌──────────────────┐       ┌──────────────────┐
           │     Neon     │         │      Clerk       │       │   External APIs  │
           │ (PostgreSQL) │         │  (Auth / JWKS)   │       │ PubMed · arXiv   │
           │  serverless  │         │                  │       │ bioRxiv · medRxiv│
           └──────────────┘         └──────────────────┘       └──────────────────┘
```

**Request flow (authenticated user):**

1. Browser hits Vercel-hosted Next.js frontend.
2. Clerk middleware (`proxy.ts`) verifies the session; unauthenticated requests redirect to `/sign-in`.
3. Frontend attaches a short-lived Clerk JWT to every API call.
4. FastAPI backend validates the JWT against Clerk's JWKS endpoint (cached locally).
5. Per-user data is read/written from Neon PostgreSQL.
6. Paper fetches call PubMed, arXiv, bioRxiv, and medRxiv directly from the backend.

---

## 2. Service Inventory

| Service | Role | Tier | Region | URL |
|---------|------|------|--------|-----|
| **Vercel** | Frontend hosting (Next.js SSR) | Hobby (free) | Auto (closest to user) | `https://manuscript-alert.vercel.app` |
| **Render** | Backend hosting (FastAPI) | Free web service | Oregon (us-west) | `https://manuscript-alert-api.onrender.com` |
| **Neon** | Serverless PostgreSQL | Free tier | AWS us-east-2 | Via `DATABASE_URL` |
| **Clerk** | Auth & JWT issuance | Free tier | Global CDN | Via JWKS URL |
| **cron-job.org** | Keep-alive scheduler | Free | — | Pings health endpoint every 10 min |
| **GitHub Actions** | CI/CD | Free (public repo) | ubuntu-latest | `.github/workflows/` |

### Render service spec (`render.yaml`)

```yaml
services:
  - type: web
    name: manuscript-alert-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.src.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/v1/health
```

Render auto-deploys on every push to `main` that passes CI (if Render's GitHub integration is connected).

---

## 3. Environment Variables

### Backend (set in Render dashboard → Environment)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (cloud) | Neon PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `ALLOWED_ORIGINS` | Yes | Comma-separated CORS origins (e.g. `https://manuscript-alert.vercel.app,http://localhost:3000`) |
| `CLERK_JWKS_URL` | Yes (cloud) | From Clerk dashboard → API Keys → Advanced → JWKS URL |
| `CLERK_SECRET_KEY` | Yes (cloud) | Clerk backend secret key (`sk_...`) |
| `ANTHROPIC_API_KEY` | Planned (Step 7) | Claude API key for paper review agent |
| `PINECONE_API_KEY` | Planned (Step 8) | Pinecone vector DB key for Knowledge Base |

**Fallback behavior when variables are absent:**

- `DATABASE_URL` absent → backend falls back to local JSON files under `backend/config/` and `backend/data/`.
- `CLERK_JWKS_URL` absent → auth middleware is disabled; all requests are treated as authenticated (local dev mode).

### Frontend (set in Vercel dashboard → Settings → Environment Variables)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key (`pk_...`) |
| `NEXT_PUBLIC_API_URL` | Yes | Backend base URL (e.g. `https://manuscript-alert-api.onrender.com/api/v1`) |

> `NEXT_PUBLIC_*` values are baked into the client bundle at build time. They are safe for public exposure but must not contain secrets.

### Local development (`.env` at repo root)

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

The frontend reads from `frontend/.env.local`:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 4. Local Development

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 22+ |
| npm | 10+ |
| Conda (optional) | Any |

### Setup

```bash
# 1. Clone repo
git clone <repo-url> && cd Manuscript_alert

# 2a. With Conda (recommended — auto-tracks dep changes)
source scripts/bootstrap_conda_env.sh

# 2b. Without Conda
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Copy and fill env vars
cp .env.example .env
# Edit .env — DATABASE_URL and CLERK_JWKS_URL are optional for basic local dev

# 4. Start both servers (hot-reload)
python server.py --dev
# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
```

### Dev server flags

| Command | Effect |
|---------|--------|
| `python server.py --dev` | FastAPI :8000 + Next.js dev server :3000 (hot-reload) |
| `python server.py` | FastAPI :8000 serving the pre-built Next.js static output |

---

## 5. CI/CD Pipeline

**File:** `.github/workflows/regression-tests.yml`

Triggers on every push and pull request to `main`.

### Pipeline stages

```
Checkout
   │
   ├── Set up Python 3.11 (pip cache)
   ├── Set up Node.js 22 (npm cache)
   └── Install dependencies
          │
          ├── [Backend] Ruff check        ← lint
          ├── [Backend] Ruff format check ← style
          ├── [Backend] pytest -v         ← 60+ unit & integration tests
          │
          ├── [Frontend] vitest           ← component tests
          ├── [Frontend] next build       ← production build (NEXT_PUBLIC_API_URL=localhost:8000)
          │
          ├── Start uvicorn :8000 (background)
          ├── Start next start :3000 (background)
          ├── Wait for both servers (curl poll, 30 retries × 2s)
          └── [E2E] Playwright (chromium)
```

### Key CI constraints

- All steps run on a single `ubuntu-latest` job (no parallelism at stage level).
- Ruff failures block the pipeline before any tests run.
- E2E tests depend on a successful `next build`; the build step bakes `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` into the bundle.
- No secrets are injected into CI; backend runs in local/no-auth mode.

### Adding a new CI step

Add to `.github/workflows/regression-tests.yml` under `steps:`. Order matters — backend tests run before E2E.

---

## 6. Deployment

### Backend → Render

Render auto-deploys when:
1. A push to `main` is detected (via GitHub integration), **and**
2. The build command (`pip install -r requirements.txt`) succeeds.

**Manual deploy:**
- Render dashboard → manuscript-alert-api → Manual Deploy → Deploy latest commit.

**Build & start sequence on Render:**

```
pip install -r requirements.txt
↓
uvicorn backend.src.main:app --host 0.0.0.0 --port $PORT
↓
FastAPI lifespan startup:
  - Initialize asyncpg connection pool (DATABASE_URL)
  - Run schema migrations (CREATE TABLE IF NOT EXISTS)
  - Migrate local JSON data to DB (first run only)
↓
Health check: GET /api/v1/health → 200 OK
```

**Cold start time:** ~30 seconds on Render free tier. The frontend shows a "server waking up" message and retries automatically.

### Frontend → Vercel

Vercel auto-deploys on every push to `main`. No config file required — Vercel auto-detects Next.js.

- Preview deployments are created for every branch/PR.
- Production deployment is promoted from `main` after CI passes.

**Vercel build command (auto-detected):**

```bash
cd frontend && npm run build
```

**Environment variables** must be set in the Vercel dashboard (not committed to git).

### Deployment checklist (first-time setup)

- [ ] Create Neon project, copy `DATABASE_URL` → Render env vars
- [ ] Create Clerk application, copy `CLERK_JWKS_URL` + `CLERK_SECRET_KEY` → Render env vars
- [ ] Copy `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` → Vercel env vars
- [ ] Set `NEXT_PUBLIC_API_URL` to Render URL → Vercel env vars
- [ ] Set `ALLOWED_ORIGINS` to Vercel URL in Render env vars
- [ ] Connect GitHub repo to Render (auto-deploy on push)
- [ ] Verify health endpoint: `curl https://manuscript-alert-api.onrender.com/api/v1/health`
- [ ] Set up cron-job.org keep-alive (see §8)

---

## 7. Database

**Provider:** Neon (serverless PostgreSQL)  
**Driver:** asyncpg (async connection pool)  
**Schema management:** Inline SQL in `backend/src/db/neon.py` (idempotent `CREATE TABLE IF NOT EXISTS`)

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Clerk user ID registry (created on first login) |
| `settings` | Per-user search configuration (keywords, date range, sources, etc.) |
| `settings_versions` | Versioned settings backups |
| `model_presets` | Named keyword/settings presets per user |
| `papers` | Cached fetched papers (keyed by user + fetch run) |

### Connection management

- Pool is initialized once at application startup (`lifespan` event).
- Pool is closed gracefully on shutdown.
- Schema is bootstrapped automatically on first connection.
- Local JSON data is migrated to DB on first run (one-time operation).

### Fallback (no DATABASE_URL)

When `DATABASE_URL` is unset, all persistence falls back to local JSON:

| Data | Location |
|------|----------|
| Settings | `backend/config/settings.json` |
| Model presets | `backend/config/models/*.json` |
| Archived papers | `backend/data/archive/archive.json` |
| Backups | `backend/config/backups/*.json` |

### Neon-specific notes

- Neon suspends compute after ~5 minutes of inactivity (free tier). First query after suspension has ~500ms cold start.
- Connection strings use the pooler endpoint (`-pooler` suffix) for lower latency.
- Backups: Neon provides point-in-time restore on paid plans; free tier has limited history.

---

## 8. Keep-Alive Strategy

Render free tier suspends services after 15 minutes of inactivity. Two mechanisms keep the backend warm:

### Primary: cron-job.org (recommended)

- External cron service at [cron-job.org](https://cron-job.org)
- Schedule: every 10 minutes, 24/7
- Target: `GET https://manuscript-alert-api.onrender.com/api/v1/health`
- No GitHub Actions minutes consumed.

### Secondary: GitHub Actions (manual trigger)

**File:** `.github/workflows/keep-alive.yml`

The scheduled cron is disabled (commented out). Can be triggered manually from the Actions tab.

```bash
# To re-enable scheduled pinging via GitHub Actions, uncomment in keep-alive.yml:
# schedule:
#   - cron: "*/10 0-6,13-23 * * *"
```

> The frontend `usePaperSearch` hook also handles cold starts gracefully — it shows a "server waking up" status and retries the fetch after a delay.

---

## 9. Observability & Logging

### Backend logs

- Structured logs written to `logs/app.log` and stdout.
- Logger configured in `backend/src/utils/logger.py`.
- On Render: logs are visible in the Render dashboard → manuscript-alert-api → Logs.
- Log rotation is not configured; the file grows unbounded in local dev.

### Health endpoint

```
GET /api/v1/health
→ 200 OK  {"status": "ok"}
```

Used by:
- Render health check (determines when deployment is live)
- Keep-alive pings (cron-job.org + GitHub Actions)
- CI server-ready poll

### What is not yet monitored

- No error tracking service (Sentry, Rollbar) is integrated.
- No uptime alerting beyond Render's native checks.
- No frontend performance monitoring (Vercel Analytics is available on paid plans).
- No structured query logging for Neon.

---

## 10. Secrets Management

### Rules

1. **Never commit secrets.** `.env` and `frontend/.env.local` are in `.gitignore`.
2. Backend secrets live in Render's environment variable dashboard.
3. Frontend secrets live in Vercel's environment variable dashboard.
4. `NEXT_PUBLIC_*` values are public by design — do not store secrets in them.
5. The `.env.example` file is committed and contains only placeholder values.

### Rotation procedure

| Secret | Where to rotate | What to update after |
|--------|----------------|----------------------|
| `CLERK_SECRET_KEY` | Clerk dashboard → API Keys | Render env var |
| `CLERK_JWKS_URL` | Auto-rotated by Clerk | Usually stable; re-copy if Clerk changes it |
| `DATABASE_URL` | Neon dashboard → Connection string | Render env var |
| `ANTHROPIC_API_KEY` | Anthropic console | Render env var |
| `PINECONE_API_KEY` | Pinecone dashboard | Render env var |

After updating a Render env var, trigger a manual deploy for the new value to take effect.

---

## 11. Runbook: Common Operations

### Check backend health

```bash
curl https://manuscript-alert-api.onrender.com/api/v1/health
# Expected: {"status":"ok"}
```

### Run the full test suite locally

```bash
# Backend
ruff check backend/ tests/
ruff format --check backend/ tests/
pytest -v

# Frontend
cd frontend
npm test          # vitest
npm run build     # production build
npm run test:e2e  # Playwright (requires servers running)
```

### Force a Render redeploy

Render dashboard → manuscript-alert-api → Manual Deploy → Deploy latest commit.

Or push an empty commit:

```bash
git commit --allow-empty -m "chore: trigger redeploy"
git push
```

### Add a new environment variable

1. Add the key to `.env.example` with an empty value and a comment.
2. Add it to `render.yaml` under `envVars:` with `sync: false`.
3. Set the actual value in the Render dashboard.
4. If it's a frontend variable (`NEXT_PUBLIC_*`), add it in the Vercel dashboard too.
5. Redeploy both services.

### Roll back to a previous deployment

**Render:** Dashboard → manuscript-alert-api → Deploys → select previous deploy → Rollback.  
**Vercel:** Dashboard → manuscript-alert → Deployments → select commit → Promote to Production.

### Reset the database schema (destructive)

```bash
# Only do this in development — drops all tables and recreates them
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# Restart the backend — lifespan startup will recreate tables
```

### Manually trigger keep-alive ping

GitHub → Actions → "Keep Render Backend Warm" → Run workflow.

### Inspect Neon database

```bash
psql $DATABASE_URL
\dt              # list tables
\d users         # describe a table
SELECT * FROM settings WHERE user_id = '<clerk-user-id>';
```

---

*For initial cloud setup, see `docs/deployment_guide.md`.  
For API reference and architecture diagrams, see `docs/architecture_reference.md`.*
