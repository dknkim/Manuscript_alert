#!/bin/bash

# Manuscript Alert System - New Computer Installer
# This script installs the app on a new computer with an existing conda environment

set -e

echo "=== Manuscript Alert System - New Computer Installer ==="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Make the launcher scripts executable
chmod +x "$SCRIPT_DIR/run_alert_app_conda.sh"
echo "✓ Made launcher script executable"

# Install dependencies in conda environment
echo "Installing dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Dependencies installed"

# Create desktop entry
echo "Creating desktop entry..."
DESKTOP_ENTRY="$HOME/.local/share/applications/manuscript-alert.desktop"

# Create the desktop file with the correct path
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

# Create a simple icon
ICON_DIR="$HOME/.local/share/icons"
mkdir -p "$ICON_DIR"

# Create a simple text-based icon
cat > "$ICON_DIR/manuscript-alert.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#4CAF50" rx="8"/>
  <text x="24" y="30" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">📚</text>
</svg>
EOF

# Update desktop entry to use the custom icon
sed -i "s|Icon=applications-science|Icon=$ICON_DIR/manuscript-alert.svg|" "$DESKTOP_ENTRY"

echo "✓ Custom icon created"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "The Manuscript Alert System has been installed successfully!"
echo ""
echo "You can now launch the app in several ways:"
echo "1. Search for 'Manuscript Alert System' in your application menu"
echo "2. Run: $SCRIPT_DIR/run_alert_app_conda.sh"
echo "3. Double-click the desktop entry in your applications menu"
echo ""
echo "The app will open in your default web browser at http://localhost:8501"
echo ""
echo "To uninstall, simply delete the project folder and the desktop entry:"
echo "  rm $DESKTOP_ENTRY"
echo "" 