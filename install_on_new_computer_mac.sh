#!/bin/bash

# Manuscript Alert System - New Computer Installer for macOS
# This script installs the app on a new Mac with an existing conda environment

set -e

echo "=== Manuscript Alert System - macOS Installer ==="
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

# Create macOS application bundle
echo "Creating macOS application bundle..."
APP_NAME="Manuscript Alert System"
APP_DIR="$HOME/Applications/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# Create directory structure
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

# Create the launcher script for macOS
cat > "$MACOS_DIR/launcher" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_DEFAULT_ENV
streamlit run app.py --server.headless true --server.port 8501
EOF

chmod +x "$MACOS_DIR/launcher"

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.manuscript.alert.system</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✓ macOS application bundle created at $APP_DIR"

# Create a simple icon (optional)
cat > "$RESOURCES_DIR/icon.icns" << 'EOF'
# This would be a proper .icns file in a real implementation
# For now, we'll use the default app icon
EOF

echo ""
echo "=== Installation Complete ==="
echo ""
echo "The Manuscript Alert System has been installed successfully on macOS!"
echo ""
echo "You can now launch the app in several ways:"
echo "1. Double-click '$APP_NAME' in your Applications folder"
echo "2. Run: $SCRIPT_DIR/run_alert_app_conda.sh"
echo "3. Run directly: streamlit run app.py"
echo ""
echo "The app will open in your default web browser at http://localhost:8501"
echo ""
echo "To uninstall, simply delete the project folder and the app bundle:"
echo "  rm -rf $APP_DIR"
echo "" 