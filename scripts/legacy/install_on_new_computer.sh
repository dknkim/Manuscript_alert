#!/bin/bash

# Manuscript Alert System - New Computer Installer (legacy)

set -e

echo "=== Manuscript Alert System - New Computer Installer (legacy) ==="
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

# Create desktop entry
echo "Creating desktop entry..."
DESKTOP_ENTRY="$HOME/.local/share/applications/manuscript-alert.desktop"

cat > "$DESKTOP_ENTRY" << EOF
[Desktop Entry]
Name=Manuscript Alert System
Comment=Stay updated with the latest papers in Alzheimer's disease and neuroimaging
Exec=$SCRIPT_DIR/run_alert_app_conda.sh
Type=Application
Terminal=true
Icon=applications-science
Categories=Science;Education;Network;
Keywords=research;papers;alzheimer;neuroimaging;pubmed;arxiv;
EOF

echo "✓ Desktop entry created at $DESKTOP_ENTRY"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "You can now launch the app by running:"
echo "$SCRIPT_DIR/run_alert_app_conda.sh"
echo ""

