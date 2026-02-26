"""App factory — FastAPI init, CORS, routers, static file serving."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.src.api import backups, health, models, papers, settings
from backend.src.config import DIST_DIR, FRONTEND_DIR


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app: FastAPI = FastAPI(title="Manuscript Alert System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(papers.router)
app.include_router(models.router)
app.include_router(backups.router)

# ---------------------------------------------------------------------------
# Static file serving (Next.js export)
# ---------------------------------------------------------------------------
if DIST_DIR.exists():
    next_static: Path = DIST_DIR / "_next"
    if next_static.exists():
        app.mount("/_next", StaticFiles(directory=str(next_static)), name="next_static")


@app.get("/{full_path:path}", response_model=None)
async def serve_frontend(
    request: Request, full_path: str
) -> FileResponse | dict[str, str]:
    """Serve the Next.js SPA — any non-API route returns index.html."""
    file_path: Path = DIST_DIR / full_path
    if file_path.is_file():
        return FileResponse(str(file_path))
    index: Path = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"detail": "Frontend not built. Run: cd frontend && npm run build"}


# ---------------------------------------------------------------------------
# Frontend build helper
# ---------------------------------------------------------------------------


def build_frontend() -> None:
    """Build the Next.js frontend if out/ is missing or outdated."""
    node_modules: Path = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies …")
        subprocess.check_call(["npm", "install"], cwd=str(FRONTEND_DIR))

    needs_build: bool = not DIST_DIR.exists()
    if not needs_build:
        index_file: Path = DIST_DIR / "index.html"
        dist_mtime: float = index_file.stat().st_mtime if index_file.exists() else 0
        src_dir: Path = FRONTEND_DIR / "src"
        for f in src_dir.rglob("*"):
            if f.stat().st_mtime > dist_mtime:
                needs_build = True
                break

    if needs_build:
        print("🔨 Building Next.js frontend …")
        subprocess.check_call(["npm", "run", "build"], cwd=str(FRONTEND_DIR))
        print("✅ Frontend built successfully.")
    else:
        print("✅ Frontend already up to date.")
