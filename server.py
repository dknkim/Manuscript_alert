"""
Thin entry point for the Manuscript Alert System.

Usage:
    conda activate basic
    python server.py          # builds frontend if needed, then starts on http://localhost:8000
    python server.py --dev    # starts API on :8000 + Next.js dev server on :3000 (hot-reload)
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys

from backend.src.main import app, build_frontend


if __name__ == "__main__":
    import uvicorn

    dev_mode: bool = "--dev" in sys.argv

    if dev_mode:
        # Start Next.js dev server with API proxy pointed at this backend
        env = {**os.environ, "NEXT_PUBLIC_API_URL": "http://localhost:8000/api/v1"}
        next_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=os.path.join(os.path.dirname(__file__), "frontend"),
            env=env,
        )

        # Ensure Next.js dev server is killed when this process exits
        def _cleanup(signum: int, _frame: object) -> None:
            next_proc.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, _cleanup)
        signal.signal(signal.SIGTERM, _cleanup)

        port: int = 8000
        print(f"\n🚀 API server on http://localhost:{port}")
        print(f"🔥 Frontend dev server on http://localhost:3000  (hot-reload)\n")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        build_frontend()
        port = 8000
        print(f"\n🚀 Manuscript Alert System running at  http://localhost:{port}\n")
        uvicorn.run(app, host="0.0.0.0", port=port)
