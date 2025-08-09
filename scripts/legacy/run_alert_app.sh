#!/bin/bash

# Manuscript Alert System Launcher (legacy venv path)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Launch the Streamlit app
echo "Launching Manuscript Alert System..."
echo "The app will open in your default browser"
echo "Press Ctrl+C to stop the app"
echo ""

streamlit run app.py --server.headless true --server.port 8501 

