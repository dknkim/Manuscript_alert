#!/usr/bin/env bash
set -euo pipefail

# Bootstraps the Conda environment for Manuscript Alert System.
# - Ensures conda is available
# - Creates env if missing
# - Activates env
# - Installs requirements only when they changed

ENV_NAME="manuscript_alert"
PY_VER="3.11"
REQ_FILE="requirements.txt"
REQ_HASH_FILE=".requirements.sha256"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$SCRIPT_DIR"

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda not found. Please install/initialize Conda:"
  echo "https://docs.conda.io/en/latest/miniconda.html"
  exit 1
fi

# Ensure 'conda activate' works in non-interactive shell
eval "$(conda shell.bash hook)"

# Create env if missing
if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Creating conda environment '$ENV_NAME' (python=$PY_VER)..."
  conda create -y -n "$ENV_NAME" "python=$PY_VER"
fi

# Activate env
conda activate "$ENV_NAME"
echo "✓ Using conda environment: $CONDA_DEFAULT_ENV"

# Install/update dependencies only if needed
NEED_INSTALL=0
if [ ! -f "$REQ_FILE" ]; then
  echo "Error: $REQ_FILE not found in $SCRIPT_DIR"
  exit 1
fi

CURRENT_HASH="$(hash_file "$REQ_FILE")"
if ! python -c "import fastapi" >/dev/null 2>&1; then
  NEED_INSTALL=1
elif [ ! -f "$REQ_HASH_FILE" ]; then
  NEED_INSTALL=1
elif [ "$(cat "$REQ_HASH_FILE")" != "$CURRENT_HASH" ]; then
  NEED_INSTALL=1
fi

if [ "${FAST:-0}" -ne 1 ] && [ "$NEED_INSTALL" -eq 1 ]; then
  echo "Installing/updating dependencies..."
  pip install -r "$REQ_FILE"
  echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
fi

echo "✓ Environment ready"

