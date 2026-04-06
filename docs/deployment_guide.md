# Deployment Guide: Neon + Clerk + Render + Vercel

This document explains what was built and how everything fits together.
Written for reference after completing Steps 3–5 of the cloud migration plan.

---

## Big Picture

Before this session, the app ran only on your local machine. Data was stored in local files. No login. No cloud.

After this session:

```
Your browser
    ↓ HTTPS
Vercel  ──── Next.js frontend (free)
    ↓ HTTPS API calls
Render  ──── FastAPI backend (free)
    ↓ SQL
Neon    ──── PostgreSQL database (free)

All routes protected by Clerk (Google/GitHub login)
```

Your data (settings, model presets, archived papers) now lives in the cloud. Each person who logs in gets their own isolated data.

---

## Part 1: Neon (Database)

### What it is
Neon is a cloud PostgreSQL database. PostgreSQL is just a structured way to store data — think of it as a very powerful spreadsheet that lives in the cloud.

### Why we needed it
Before: data was stored in local Python files and `.json` files on your machine. If you reset your machine, or wanted a colleague to use the app, the data was gone or inaccessible.

After: all data lives in Neon and is accessible from anywhere.

### What tables were created

| Table | What it stores | Replaces |
|-------|---------------|---------|
| `users` | One row per logged-in user | (new) |
| `settings` | Your keyword/search settings | `config/settings.py` |
| `settings_versions` | History of saved settings | `config/backups/` |
| `model_presets` | Saved model presets | `config/models/*.json` |
| `papers` | Archived papers | `data/archive/archive.json` |

### How the migration works
On first startup after `DATABASE_URL` is set, the app automatically:
1. Creates all the tables (if they don't exist)
2. Copies your existing local data into the database (runs once)

You never lose your old data.

### Fallback mode
If `DATABASE_URL` is not set (e.g., running locally without `.env`), the app falls back to reading local files. This means the app always works, even without a database connection.

### Key files
- `backend/src/db/neon.py` — connection pool, schema creation, data migration
- `backend/src/db/models.py` — all SQL queries (get settings, save preset, archive paper, etc.)

---

## Part 2: Clerk (Authentication)

### What it is
Clerk is an auth-as-a-service tool. Instead of building login/signup yourself (which is complex and error-prone), you hand that off to Clerk. It handles Google OAuth, GitHub OAuth, sessions, and JWT tokens.

### What a JWT token is
When you log in with Google via Clerk, Clerk gives the browser a short-lived token (JWT). Every API request from the frontend to the backend includes this token in the header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...
```

The backend verifies this token using Clerk's public key (JWKS URL). If valid, it extracts your user ID. That user ID is used to look up your personal data in Neon.

### How it's wired up

**Frontend (`proxy.ts`)**
Runs on every request before the page loads. If you're not logged in and try to visit any page, it redirects you to `/sign-in`. The sign-in page is the only public route.

**Frontend (`ClerkTokenProvider.tsx`)**
After login, registers a function that fetches your JWT. Every API call made by `api.ts` automatically attaches the token.

**Frontend (`layout.tsx`)**
Wraps the whole app in `ClerkProvider`. This gives all components access to auth state (who is logged in, etc.).

**Backend (`backend/src/api/auth.py`)**
FastAPI dependency that verifies the JWT on every protected route. Returns the user's Clerk ID (a string like `user_abc123`). Returns `None` if auth is not configured (local dev mode).

**Backend (all v1 routes)**
Each route receives `user_id` as a parameter. DB queries are filtered by `user_id`, so users only see their own data.

### Local dev without Clerk
If `CLERK_JWKS_URL` is not set in `.env`, the backend skips JWT verification and treats all requests as a single anonymous user. The app works normally, just without login.

### Key files
- `frontend/src/proxy.ts` — route protection (redirect to sign-in if not authenticated)
- `frontend/src/app/sign-in/[[...sign-in]]/page.tsx` — Clerk's hosted sign-in UI
- `frontend/src/components/ClerkTokenProvider.tsx` — attaches JWT to all API calls
- `frontend/src/app/layout.tsx` — ClerkProvider wrapper
- `backend/src/api/auth.py` — JWT verification on the backend

---

## Part 3: Render (Backend Hosting)

### What it is
Render is a cloud platform that runs your Python/FastAPI backend. It pulls your code from GitHub and runs it on a server.

### How deployment works
1. You push code to GitHub (`main` branch)
2. Render detects the push and automatically rebuilds + redeploys
3. Your API is live at `https://manuscript-alert-api.onrender.com`

### The blueprint file (`render.yaml`)
Tells Render exactly how to build and run your app:

```yaml
buildCommand: pip install -r requirements.txt
startCommand: uvicorn backend.src.main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /api/v1/health
```

### Free tier limits
- 750 hours/month (enough for 24/7 if you only have one service)
- **Spins down after 15 minutes of inactivity** — first request after idle takes ~30 seconds to wake up. This is normal on the free tier.
- 512 MB RAM

### Environment variables set on Render

| Variable | What it is |
|----------|-----------|
| `DATABASE_URL` | Neon connection string |
| `CLERK_JWKS_URL` | Clerk's public key URL for JWT verification |
| `CLERK_SECRET_KEY` | Clerk secret key (server-side auth) |
| `ALLOWED_ORIGINS` | Your Vercel frontend URL (for CORS) |

### What CORS is
CORS is a browser security rule: a webpage at `vercel.app` is not allowed to make requests to `render.com` unless the backend explicitly says "I trust requests from `vercel.app`." The `ALLOWED_ORIGINS` variable tells the backend which domains to trust.

### Key files
- `render.yaml` — deployment blueprint
- `.python-version` — tells Render to use Python 3.11

---

## Part 4: Vercel (Frontend Hosting)

### What it is
Vercel is a cloud platform specialized for Next.js apps. It builds and serves your frontend.

### How deployment works
1. You push code to GitHub (`main` branch)
2. Vercel detects the push and automatically rebuilds + redeploys
3. Your app is live at `https://your-app.vercel.app`

### Why `output: "export"` was removed
The old `next.config.ts` had `output: "export"` which generates a static HTML site. Static sites can't run server-side code — but Clerk's sign-in page needs server-side rendering. Removing this line enables full SSR on Vercel.

### Environment variables set on Vercel

| Variable | What it is |
|----------|-----------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key (used in the browser) |
| `CLERK_SECRET_KEY` | Clerk secret key (used server-side) |
| `NEXT_PUBLIC_API_URL` | Your Render backend URL + `/api/v1` |

Note: variables starting with `NEXT_PUBLIC_` are visible in the browser. Never put secrets in `NEXT_PUBLIC_` variables.

---

## Deployment Order (Important)

Because Vercel needs the Render URL, and Render needs the Vercel URL, deploy in this order:

```
1. Deploy Render first
      ↓ note the URL: https://manuscript-alert-api.onrender.com
2. Deploy Vercel (set NEXT_PUBLIC_API_URL to the Render URL)
      ↓ note the URL: https://your-app.vercel.app
3. Update Render's ALLOWED_ORIGINS to the Vercel URL
      ↓ Render auto-redeploys
4. Done
```

---

## Environment Variables Summary

### Local `.env` file
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
CLERK_JWKS_URL=https://...clerk.accounts.dev/.well-known/jwks.json
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
DATABASE_URL=postgresql://...@...neon.tech/neondb?sslmode=require
```

### Render environment variables
```
DATABASE_URL=...
CLERK_JWKS_URL=...
CLERK_SECRET_KEY=...
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Vercel environment variables
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=https://manuscript-alert-api.onrender.com/api/v1
```

---

## How Data Flows (End to End)

```
1. User visits https://your-app.vercel.app
2. proxy.ts checks: are you logged in?
   → No: redirect to /sign-in
   → Yes: show the app
3. User clicks "Fetch Papers"
4. Frontend calls POST /api/v1/papers/fetch
   with header: Authorization: Bearer <JWT>
5. Render receives the request
6. auth.py verifies the JWT with Clerk's JWKS endpoint
7. Returns user_id = "user_abc123"
8. Papers route fetches from PubMed/arXiv/bioRxiv
9. Results are returned and displayed
10. User archives a paper
11. Backend saves it to Neon under user_id = "user_abc123"
12. Next time user logs in (on any device), their archived papers are there
```

---

## What Still Uses Local Files

When running locally **without** `DATABASE_URL` in `.env`:
- Settings → read from `backend/src/services/settings_service.py`
- Model presets → read from `backend/config/models/*.json`
- Archive → read from `backend/data/archive/archive.json`

This fallback is intentional — the app works fully offline for local development.

---

## Next Steps (Steps 6 & 7)

| Step | What | Needs |
|------|------|-------|
| Step 6 | LangGraph agent pipeline (intelligent paper review) | `ANTHROPIC_API_KEY` |
| Step 7 | Pinecone vector search + Knowledge Base | `PINECONE_API_KEY` |

Both are additive — the app continues to work without them.
