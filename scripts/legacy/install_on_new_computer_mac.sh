#!/bin/bash

# Manuscript Alert System - New Computer Installer for macOS (legacy)

set -e

echo "=== Manuscript Alert System - macOS Installer (legacy) ==="
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed"
    echo "Please install conda first:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Error: Not currently in a conda environment"
    echo "Please activate your conda environment first:"
    echo "  conda activate your_environment_name"
    echo ""
    echo "Or create a new environment:"
    echo "  conda create -n manuscript_alert python=3.11"
    echo "  conda activate manuscript_alert"
    exit 1
fi

echo "✓ Using conda environment: $CONDA_DEFAULT_ENV"

# Make the launcher script executable
chmod +x "$SCRIPT_DIR/run_alert_app_conda.sh"
echo "✓ Made launcher script executable"

# Install dependencies in conda environment
echo "Installing dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Dependencies installed"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "You can now launch the app by running:"
echo "$SCRIPT_DIR/run_alert_app_conda.sh"
echo ""

