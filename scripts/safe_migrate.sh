#!/bin/bash
# Safe Migration Script for Supabase
# This script ensures backups are taken before any database migration

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/migrations"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Safe Migration Script ===${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Step 1: Check for dangerous operations in pending migrations
echo -e "${YELLOW}Step 1: Checking for dangerous operations...${NC}"

if [ -d "$PROJECT_ROOT/supabase/migrations" ]; then
  DANGEROUS=$(grep -r -i -E "(DROP TABLE|DROP DATABASE|TRUNCATE|DELETE FROM.*(?!WHERE))" "$PROJECT_ROOT/supabase/migrations/" || true)

  if [ ! -z "$DANGEROUS" ]; then
    echo -e "${RED}⚠️  WARNING: Dangerous operations detected in migrations:${NC}"
    echo "$DANGEROUS"
    echo ""
    read -p "These operations can cause DATA LOSS. Continue anyway? (type 'yes' to continue): " answer
    if [ "$answer" != "yes" ]; then
      echo -e "${RED}Migration cancelled for safety.${NC}"
      exit 1
    fi
  else
    echo -e "${GREEN}✓ No dangerous operations detected${NC}"
  fi
fi

# Step 2: Show what migrations will be applied
echo ""
echo -e "${YELLOW}Step 2: Migrations to be applied:${NC}"
supabase migration list

echo ""
read -p "Do you want to see the migration diff? (y/n): " show_diff
if [ "$show_diff" = "y" ]; then
  supabase db diff || echo "No diff available"
fi

# Step 3: Create backup
echo ""
echo -e "${YELLOW}Step 3: Creating backup...${NC}"
BACKUP_FILE="$BACKUP_DIR/pre_migration_$TIMESTAMP.sql"

supabase db dump -f "$BACKUP_FILE" || {
  echo -e "${RED}✗ Backup failed! Cannot proceed without backup.${NC}"
  exit 1
}

echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "  Size: $BACKUP_SIZE"

# Step 4: Confirm before proceeding
echo ""
echo -e "${YELLOW}Step 4: Ready to migrate${NC}"
echo "Backup location: $BACKUP_FILE"
echo ""
read -p "Apply migrations now? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo -e "${YELLOW}Migration cancelled by user.${NC}"
  echo "Backup preserved at: $BACKUP_FILE"
  exit 0
fi

# Step 5: Apply migrations
echo ""
echo -e "${YELLOW}Step 5: Applying migrations...${NC}"

if supabase db push; then
  echo -e "${GREEN}✓ Migration successful!${NC}"
  echo ""
  echo "Backup preserved at: $BACKUP_FILE"
  echo "You can delete this backup once you've verified everything works."
else
  echo -e "${RED}✗ Migration failed!${NC}"
  echo ""
  echo "To rollback, restore from backup:"
  echo "  psql \$DATABASE_URL < $BACKUP_FILE"
  exit 1
fi

# Step 6: Clean up old backups (keep last 10)
echo ""
echo -e "${YELLOW}Step 6: Cleaning up old backups (keeping last 10)...${NC}"
ls -t "$BACKUP_DIR"/pre_migration_*.sql | tail -n +11 | xargs -r rm
echo -e "${GREEN}✓ Cleanup complete${NC}"

echo ""
echo -e "${GREEN}=== Migration Complete ===${NC}"
