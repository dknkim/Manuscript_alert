"""
Thin entry point for the Manuscript Alert System.

Usage:
    conda activate basic
    python server.py          # builds frontend if needed, then starts on http://localhost:8000
    python server.py --dev    # skip frontend build (Next.js dev server)
"""

from __future__ import annotations

import sys

from backend.src.main import app, build_frontend


if __name__ == "__main__":
    import uvicorn

    dev_mode: bool = "--dev" in sys.argv

    if not dev_mode:
        build_frontend()

    port: int = 8000
    print(f"\n🚀 Manuscript Alert System running at  http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
