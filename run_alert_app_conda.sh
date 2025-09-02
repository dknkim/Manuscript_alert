#!/usr/bin/env bash
set -euo pipefail

# Manuscript Alert System Launcher (Conda, single entry point)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory (project root)
cd "$SCRIPT_DIR"

# Bootstrap environment and dependencies (creates/activates env if needed,
# installs deps only when requirements.txt changes)
bash scripts/bootstrap_conda_env.sh

# Setup git pre-commit hook (silent if already installed)
bash scripts/setup-git-hook.sh

echo "Launching Manuscript Alert System..."
echo "The app will open in your default browser"
echo "Press Ctrl+C to stop the app"
echo ""

exec streamlit run app.py \
  --server.headless true \
  --server.port 8501 \
  --server.runOnSave true