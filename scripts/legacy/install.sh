#!/bin/bash

# Manuscript Alert System Installer (legacy venv path)
# Installs the app using Python venv and adds a desktop entry

set -e

echo "=== Manuscript Alert System Installer (legacy) ==="
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3 first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    echo "Please install pip3 first"
    exit 1
fi

echo "✓ Python 3 and pip3 are available"

# Make the legacy launcher script executable
chmod +x "$SCRIPT_DIR/scripts/legacy/run_alert_app.sh"
echo "✓ Made legacy launcher script executable"

# Create virtual environment
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Dependencies installed"

# Create desktop entry
echo "Creating desktop entry..."
DESKTOP_ENTRY="$HOME/.local/share/applications/manuscript-alert.desktop"

# Update the desktop file with the correct path
cat > "$DESKTOP_ENTRY" << EOF
[Desktop Entry]
Name=Manuscript Alert System
Comment=Stay updated with the latest papers in Alzheimer's disease and neuroimaging
Exec=$SCRIPT_DIR/scripts/legacy/run_alert_app.sh
Type=Application
Terminal=true
Icon=applications-science
Categories=Science;Education;Network;
Keywords=research;papers;alzheimer;neuroimaging;pubmed;arxiv;
EOF

echo "✓ Desktop entry created at $DESKTOP_ENTRY"

# Create a simple icon (optional)
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
echo "You can now launch the app in several ways:"
echo "1. Search for 'Manuscript Alert System' in your application menu"
echo "2. Run: $SCRIPT_DIR/scripts/legacy/run_alert_app.sh"
echo "3. Double-click the desktop entry in your applications menu"
echo ""
echo "The app will open in your default web browser at http://localhost:8501"
echo ""
echo "To uninstall, simply delete the project folder and the desktop entry:"
echo "  rm $DESKTOP_ENTRY"
echo ""

