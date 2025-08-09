#!/bin/bash

# Manuscript Alert System Launcher for macOS (legacy)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    echo "Please install conda or activate your conda environment manually"
    echo "You can install Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Warning: Not currently in a conda environment"
    echo "Please activate your conda environment first:"
    echo "  conda activate your_environment_name"
    echo ""
    echo "Or run this script from within your conda environment"
    exit 1
fi

echo "✓ Using conda environment: $CONDA_DEFAULT_ENV"

# Install/update dependencies in conda environment
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Launch the Streamlit app
echo "Launching Manuscript Alert System..."
echo "The app will open in your default browser"
echo "Press Ctrl+C to stop the app"
echo ""

streamlit run app.py --server.headless true --server.port 8501 

