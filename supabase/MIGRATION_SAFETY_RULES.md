# MIGRATION SAFETY RULES

## ⚠️ CRITICAL: These rules MUST be followed for ALL database migrations

### Rule #1: NEVER DROP TABLES IN MIGRATIONS
```sql
❌ NEVER DO THIS:
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS papers CASCADE;

✅ ALWAYS DO THIS:
CREATE TABLE IF NOT EXISTS user_profiles (...);
CREATE TABLE IF NOT EXISTS papers (...);
```

### Rule #2: NEVER DROP DATA
- Never use `DROP TABLE`
- Never use `TRUNCATE`
- Never use `DELETE FROM table` without WHERE clause
- Never use `DROP DATABASE`

### Rule #3: Use Safe Operations Only
```sql
✅ SAFE operations:
- CREATE TABLE IF NOT EXISTS
- CREATE INDEX IF NOT EXISTS
- ALTER TABLE ADD COLUMN IF NOT EXISTS
- INSERT ... ON CONFLICT DO NOTHING
- UPDATE ... WHERE (specific condition)
- CREATE OR REPLACE FUNCTION
- DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN null END $$;

❌ DANGEROUS operations:
- DROP TABLE
- DROP COLUMN
- TRUNCATE
- DELETE without WHERE
- ALTER TABLE DROP CONSTRAINT
```

### Rule #4: Always Review Before Pushing
**BEFORE running `supabase db push`:**
1. Review EVERY migration file that will be applied
2. Look for DROP, TRUNCATE, DELETE keywords
3. Check migration diff with `supabase db diff`
4. Test migrations on local database first
5. Have someone else review if touching production

### Rule #5: Backup Before Major Changes
```bash
# ALWAYS backup before migrations
supabase db dump -f backup_$(date +%Y%m%d_%H%M%S).sql

# Test migration locally first
supabase db reset  # This is OK for LOCAL dev only
supabase db push

# If successful, then push to remote
supabase db push
```

### Rule #6: Migration File Naming
- Use timestamps: `YYYYMMDDHHMMSS_description.sql`
- Be descriptive: `20251027120000_add_user_preferences_table.sql`
- Never reuse timestamps
- Keep migrations in order

### Rule #7: Make Migrations Idempotent
Every migration should be runnable multiple times without errors:
```sql
-- Bad: Fails on second run
CREATE TYPE user_role AS ENUM ('admin', 'user');

-- Good: Idempotent
DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('admin', 'user');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;
```

### Rule #8: Use Transactions (When Possible)
```sql
BEGIN;
  -- Your changes here
  ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT;
COMMIT;
```

### Rule #9: Document WHY, Not Just WHAT
```sql
-- Bad comment:
-- Create user_preferences table

-- Good comment:
-- Refactor preferences from JSONB blob to structured table
-- Benefits: Better querying, type safety, GIN indexes for arrays
-- Migration path: JSONB → structured columns
-- Date: 2025-10-27
-- Author: Claude
```

### Rule #10: Pre-Migration Checklist
- [ ] Does this migration use DROP anywhere? ❌ STOP
- [ ] Does this migration use TRUNCATE? ❌ STOP
- [ ] Does this migration use DELETE without WHERE? ❌ STOP
- [ ] Are all CREATE statements using IF NOT EXISTS? ✅
- [ ] Are all policies wrapped in DO blocks with exception handling? ✅
- [ ] Have I tested this on local database? ✅
- [ ] Have I reviewed the git diff? ✅
- [ ] Do I have a backup? ✅
- [ ] Is this idempotent (can run multiple times)? ✅

## Emergency Recovery

### If Data is Lost:
1. **DON'T PANIC** - Check for backups first
2. Check Supabase dashboard for automatic backups (Pro tier only)
3. Check local dumps: `ls -la *.sql`
4. Check git history for data dumps
5. Restore from backup: `psql DATABASE_URL < backup.sql`

### If No Backup Exists:
1. Accept the loss (this is why we backup)
2. Document what was lost
3. Create new test data
4. Learn from the mistake
5. Implement backup system going forward

## Backup Strategy

### Daily Automatic Backups (Required for Production)
```bash
# Add to crontab
0 2 * * * cd /path/to/project && supabase db dump -f backups/daily_$(date +%Y%m%d).sql

# Keep last 7 days
0 3 * * * find /path/to/project/backups -name "daily_*.sql" -mtime +7 -delete
```

### Before Every Migration
```bash
#!/bin/bash
# scripts/safe_migrate.sh

echo "Creating backup before migration..."
supabase db dump -f "backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql"

echo "Reviewing migrations to be applied..."
supabase migration list

echo "Show me the diff..."
supabase db diff

read -p "Continue with migration? (yes/no) " answer
if [ "$answer" = "yes" ]; then
  supabase db push
  echo "Migration complete!"
else
  echo "Migration cancelled."
fi
```

## Code Review Requirements

### Migrations Must Be Reviewed By:
1. Original author (you)
2. Another developer (if available)
3. Someone who reads this safety guide

### Review Checklist:
- [ ] No DROP statements
- [ ] No TRUNCATE statements
- [ ] No DELETE without WHERE
- [ ] All CREATEs use IF NOT EXISTS
- [ ] Migration is idempotent
- [ ] Backup taken before applying
- [ ] Tested on local first

## What Went Wrong (October 27, 2025)

### The Incident:
- Destructive migration `20251027000000_email_based_auth.sql` contained DROP TABLE statements
- Migration was applied without review
- All user data was deleted
- No backup existed

### Root Cause:
- Migration file created for initial setup (clean slate)
- File never updated to be safe for existing data
- No pre-push review process
- No automated backup system

### Lessons Learned:
1. Never commit destructive migrations
2. Always review before push
3. Implement automated backups
4. Test migrations on local first
5. Use CREATE IF NOT EXISTS everywhere
6. Make migrations idempotent
7. Document migration purposes clearly

### Prevention:
- This safety guide created
- Migration file fixed to use CREATE IF NOT EXISTS
- TODO: Implement automated backup script
- TODO: Add pre-commit hook to check for DROP statements
- TODO: Create safe_migrate.sh wrapper script

## Future Improvements

### Pre-commit Hook (TODO)
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Check for dangerous SQL in migrations

if git diff --cached --name-only | grep -q "supabase/migrations/"; then
  echo "Checking migrations for dangerous operations..."

  if git diff --cached | grep -iE "(DROP TABLE|DROP DATABASE|TRUNCATE|DELETE FROM.*WHERE)"; then
    echo "❌ DANGER: Migration contains destructive operations!"
    echo "Review the changes carefully."
    echo "If intentional, use git commit --no-verify"
    exit 1
  fi
fi
```

### Safe Migration Wrapper (TODO)
Create `scripts/safe_migrate.sh` with:
- Automatic backup before migration
- Migration review prompt
- Dry-run option
- Rollback capability

---

**REMEMBER:** Data loss is permanent. Always err on the side of caution.
