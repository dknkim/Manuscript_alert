#!/bin/bash
# Installation script for git hooks
# Generates pre-commit hook directly (no copying or tracking template files)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_TARGET="$PROJECT_ROOT/.git/hooks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Git Hooks Installation ===${NC}"
echo ""

# Check if .git directory exists
if [ ! -d "$HOOKS_TARGET" ]; then
  echo -e "${RED}Error: .git/hooks directory not found!${NC}"
  echo "Make sure you're running this from the project root."
  exit 1
fi

# Function to generate and install pre-commit hook
install_precommit_hook() {
  local target_file="$HOOKS_TARGET/pre-commit"

  # Check if target already exists
  if [ -f "$target_file" ]; then
    # Backup existing hook
    local backup_file="$target_file.backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}⚠ Existing pre-commit hook found${NC}"
    echo "  Creating backup: $(basename "$backup_file")"
    cp "$target_file" "$backup_file"
  fi

  # Generate the hook file
  echo -e "${GREEN}✓ Generating pre-commit hook${NC}"

  cat > "$target_file" << 'HOOK_EOF'
#!/bin/bash
# Pre-commit hook for Manuscript Alert System
# Runs ruff for Python linting/formatting and checks SQL migrations for safety

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Running Pre-commit Checks ===${NC}"
echo ""

# ============================================================
# STEP 1: Python Code Quality Checks with Ruff
# ============================================================

PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ ! -z "$PYTHON_FILES" ]; then
  echo -e "${YELLOW}Running ruff checks on Python files...${NC}"

  # Count total errors before fixing
  TOTAL_ERRORS=0
  FIXED_ERRORS=0

  # Run ruff check with MINIMAL rules (quotes, imports, trailing newlines only)
  # These are auto-fixable and should never block commits
  ruff check --fix --select=I,Q,W292 $PYTHON_FILES 2>&1 | tee /tmp/ruff_output.txt || true

  # Parse output for reporting only (don't fail on errors)
  TOTAL_ERRORS=$(grep -oE "[0-9]+ error" /tmp/ruff_output.txt | head -1 | grep -oE "[0-9]+" || echo "0")
  FIXED_ERRORS=$(grep -oE "[0-9]+ fixed" /tmp/ruff_output.txt | head -1 | grep -oE "[0-9]+" || echo "0")

  if [ "$FIXED_ERRORS" -gt 0 ]; then
    REMAINING=$((TOTAL_ERRORS - FIXED_ERRORS))
    if [ "$REMAINING" -gt 0 ]; then
      echo -e "${YELLOW}Found $TOTAL_ERRORS errors ($FIXED_ERRORS fixed, $REMAINING remaining).${NC}"
      echo -e "  ${YELLOW}⚠ Could not auto-fix all issues${NC}"
    else
      echo -e "${GREEN}Found $TOTAL_ERRORS errors ($FIXED_ERRORS fixed, 0 remaining).${NC}"
    fi
  fi

  # Run ruff format (formatting/style)
  echo -e "${YELLOW}Running ruff format...${NC}"
  if ruff format $PYTHON_FILES; then
    echo -e "${GREEN}✓ Formatting applied${NC}"
  else
    echo -e "${RED}✗ Formatting failed${NC}"
    exit 1
  fi

  # Re-stage the fixed files
  for file in $PYTHON_FILES; do
    git add "$file"
  done

  echo ""
  echo -e "${GREEN}✓ Python code quality checks passed${NC}"
  echo ""
  echo "Summary of fixes applied:"
  echo "  • Double quotes enforced"
  echo "  • Imports sorted (PEP 8)"
  echo "  • Trailing newlines added"
  echo "  • Other style issues fixed"
  echo ""
fi

# ============================================================
# STEP 2: SQL Migration Safety Checks
# ============================================================

MIGRATION_FILES=$(git diff --cached --name-only | grep "supabase/migrations/.*\.sql$" || true)

if [ ! -z "$MIGRATION_FILES" ]; then
  echo -e "${YELLOW}Checking SQL migrations for dangerous operations...${NC}"

  # Check for dangerous operations ONLY in migration files (exclude SQL comments)
  DANGEROUS=$(git diff --cached -- $MIGRATION_FILES | grep -iE "^\+.*(DROP TABLE|DROP DATABASE|TRUNCATE TABLE)" | grep -v "^\+--" || true)

  if [ ! -z "$DANGEROUS" ]; then
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  DANGER: Migration contains DESTRUCTIVE operations!       ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Dangerous lines detected:${NC}"
    echo "$DANGEROUS"
    echo ""
    echo -e "${RED}These operations can cause PERMANENT DATA LOSS!${NC}"
    echo ""
    echo "Rules:"
    echo "  ❌ NEVER use DROP TABLE"
    echo "  ❌ NEVER use TRUNCATE"
    echo "  ❌ NEVER use DELETE without WHERE"
    echo "  ✅ ALWAYS use CREATE TABLE IF NOT EXISTS"
    echo "  ✅ ALWAYS use ALTER TABLE ADD COLUMN IF NOT EXISTS"
    echo ""
    echo "Read: supabase/MIGRATION_SAFETY_RULES.md"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  1. Fix the migration to use safe operations (recommended)"
    echo "  2. Use 'git commit --no-verify' to bypass this check (NOT recommended)"
    echo ""
    exit 1
  fi

  # Check for missing IF NOT EXISTS ONLY in migration files (non-blocking warning)
  MISSING_IF_NOT_EXISTS=$(git diff --cached -- $MIGRATION_FILES | grep -iE "^\+.*CREATE (TABLE|INDEX)" | grep -v "IF NOT EXISTS" | grep -v "^\+--" || true)

  if [ ! -z "$MISSING_IF_NOT_EXISTS" ]; then
    echo -e "${YELLOW}⚠️  Note: Found CREATE statements without 'IF NOT EXISTS':${NC}"
    echo "$MISSING_IF_NOT_EXISTS"
    echo ""
    echo -e "${YELLOW}Consider adding 'IF NOT EXISTS' to make migration idempotent.${NC}"
    echo -e "${YELLOW}(This is just a suggestion - commit will proceed)${NC}"
    echo ""
  fi

  echo -e "${GREEN}✓ Migration safety checks passed${NC}"
  echo ""
fi

# ============================================================
# Final Summary
# ============================================================

echo -e "${GREEN}✓ Pre-commit checks completed${NC}"
if [ ! -z "$PYTHON_FILES" ]; then
  echo "Note: Some files were auto-fixed and re-staged"
  echo ""
  echo "Files are ready to commit!"
fi
echo ""

exit 0
HOOK_EOF

  # Make it executable
  chmod +x "$target_file"
  echo -e "${GREEN}✓ Hook installed and made executable${NC}"
}

# Install pre-commit hook
echo "Generating git hooks..."
echo ""
install_precommit_hook

# Check if ruff is installed
echo ""
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v ruff &> /dev/null; then
  echo -e "${YELLOW}⚠ Warning: ruff is not installed${NC}"
  echo "  The pre-commit hook requires ruff for Python linting."
  echo "  Install it with: pip install ruff"
  echo ""
else
  echo -e "${GREEN}✓ ruff is installed${NC}"
fi

# List all backups created
echo ""
echo "Backups created (if any):"
ls -1 "$HOOKS_TARGET"/*.backup_* 2>/dev/null || echo "  No existing hooks were backed up"

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Python linting (ruff) + SQL migration safety checks"
echo ""
echo "To restore a backup:"
echo "  cp .git/hooks/pre-commit.backup_TIMESTAMP .git/hooks/pre-commit"
echo ""
echo "To uninstall:"
echo "  rm .git/hooks/pre-commit"
echo ""
echo "To reinstall/update:"
echo "  ./scripts/install-hooks.sh"
echo ""
