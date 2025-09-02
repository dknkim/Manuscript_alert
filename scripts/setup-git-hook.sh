#!/usr/bin/env bash
set -euo pipefail

# Setup Git pre-commit hook for the Manuscript Alert System
# This script creates a pre-commit hook that runs ruff on Python files

# Get the git root directory
GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"

if [ -z "$GIT_ROOT" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

HOOK_FILE="$GIT_ROOT/.git/hooks/pre-commit"

# Function to create the pre-commit hook content
create_hook_content() {
    cat << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Git pre-commit hook for Manuscript Alert System
# Runs ruff to check and fix Python code style
# Also removes __pycache__ and .pyc files from git

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the git root directory
GIT_ROOT="$(git rev-parse --show-toplevel)"
cd "$GIT_ROOT"

# Activate conda environment if available
ENV_NAME="manuscript_alert"
if command -v conda >/dev/null 2>&1; then
    # Initialize conda for bash (required for non-interactive shells)
    eval "$(conda shell.bash hook)" 2>/dev/null || true
    # Activate environment if it exists
    if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME" 2>/dev/null; then
        conda activate "$ENV_NAME" 2>/dev/null || true
    fi
fi

# Auto-remove __pycache__ and .pyc files from git index
find . -type d -name '__pycache__' -print0 | xargs -0 git rm -r --cached --ignore-unmatch 2>/dev/null || true
git rm -f --cached $(git ls-files '*.pyc' 2>/dev/null || echo) 2>/dev/null || true

# Check if ruff is installed
if ! command -v ruff >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Warning: ruff is not installed${NC}"
    echo "Please install it with: pip install ruff"
    echo "Skipping pre-commit checks..."
    exit 0
fi

# Get list of staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    # No Python files staged, nothing to check
    exit 0
fi

echo -e "${GREEN}Running pre-commit checks...${NC}"

# Count files for progress display
TOTAL_FILES=$(echo "$STAGED_PY_FILES" | wc -l | tr -d ' ')
CURRENT_FILE=0

# Track if any files were modified
FILES_MODIFIED=false

# Process each staged Python file
for FILE in $STAGED_PY_FILES; do
    CURRENT_FILE=$((CURRENT_FILE + 1))
    
    # Show progress
    echo -e "[$CURRENT_FILE/$TOTAL_FILES] Checking $FILE..."
    
    # Run ruff check with auto-fix
    if ruff check --fix "$FILE" 2>/dev/null && ruff format "$FILE" 2>/dev/null; then
        # Check if file was modified
        if ! git diff --quiet "$FILE"; then
            FILES_MODIFIED=true
            echo -e "  ${GREEN}✓${NC} Fixed and formatted"
            # Re-add the file to include the fixes
            git add "$FILE"
        else
            echo -e "  ${GREEN}✓${NC} Already clean"
        fi
    else
        # If ruff fails, show the error but continue
        echo -e "  ${YELLOW}⚠${NC} Could not auto-fix all issues"
        # Still try to add any partial fixes
        git add "$FILE"
        FILES_MODIFIED=true
    fi
done

echo ""

if [ "$FILES_MODIFIED" = true ]; then
    echo -e "${GREEN}✓ Pre-commit checks completed${NC}"
    echo -e "${YELLOW}Note: Some files were auto-fixed and re-staged${NC}"
    echo ""
    echo "Summary of fixes applied:"
    echo "  • Double quotes enforced"
    echo "  • Imports sorted (PEP 8)"
    echo "  • Trailing newlines added"
    echo "  • Other style issues fixed"
    echo ""
    echo -e "${GREEN}Files are ready to commit!${NC}"
else
    echo -e "${GREEN}✓ All files passed checks - no changes needed${NC}"
fi

exit 0
EOF
}

# Check if hook already exists
if [ -f "$HOOK_FILE" ]; then
    # Hook exists, check if it's our hook by looking for a marker
    if grep -q "Manuscript Alert System" "$HOOK_FILE" 2>/dev/null; then
        # It's our hook, silently exit
        exit 0
    else
        # Different hook exists, prompt user
        echo "⚠ A pre-commit hook already exists but it's not the Manuscript Alert hook"
        echo "Location: $HOOK_FILE"
        echo ""
        read -p "Do you want to replace it? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping existing hook. Setup cancelled."
            exit 0
        fi
        echo "Backing up existing hook to $HOOK_FILE.backup"
        cp "$HOOK_FILE" "$HOOK_FILE.backup"
    fi
fi

# Install the hook
echo "Installing pre-commit git hook..."
echo ""
echo "Setting up Git hook with the following features:"
echo "  ✓ Automatic double quote enforcement"
echo "  ✓ Import sorting (PEP 8 standard)"
echo "  ✓ Trailing newline fixes"
echo "  ✓ Code formatting with ruff"
echo ""

# Create the hook file
create_hook_content > "$HOOK_FILE"

# Make it executable
chmod +x "$HOOK_FILE"

# Test the hook
echo "Testing hook installation..."
if [ -x "$HOOK_FILE" ]; then
    echo "✓ Hook installed successfully at $HOOK_FILE"
    echo ""
    echo "The pre-commit hook is now active and will:"
    echo "  • Run automatically before each commit"
    echo "  • Fix style issues in staged Python files"
    echo "  • Re-stage fixed files automatically"
    echo ""
    echo "Setup complete!"
else
    echo "❌ Error: Failed to make hook executable"
    exit 1
fi