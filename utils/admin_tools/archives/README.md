# Migration Scripts Archive

This folder contains historical migration scripts that were used during the Supabase integration phases. These scripts are preserved for reference and potential rollback scenarios but are not actively used.

## Scripts

### `migrate_preferences_to_supabase.py`
**Phase:** 2.0 (October 2025)
**Purpose:** Migrated user preferences from `config/settings.py` file to Supabase `user_profiles.preferences` JSONB field
**Status:** ✅ Completed - No longer needed
**When to use:** Only if you need to restore the Phase 2.0 migration behavior

**Migration path:**
```
config/settings.py → user_profiles.preferences (JSONB blob)
```

### `migrate_preferences_to_table.py`
**Phase:** 2.1 (October 27, 2025)
**Purpose:** Migrated user preferences from JSONB blob to structured `user_preferences` table
**Status:** ✅ Completed - May be needed if production users have unmigrated JSONB data
**When to use:** If you discover users with preferences still in `user_profiles.preferences` JSONB format

**Migration path:**
```
user_profiles.preferences (JSONB blob) → user_preferences table (structured columns)
```

**Features:**
- Transforms JSONB to structured columns
- Handles data type conversions (arrays, booleans, JSONB)
- Provides verification and detailed migration reports
- Idempotent (skips already-migrated users)

## Current Architecture (Post Phase 2.1)

User preferences are now stored in the `user_preferences` table with:
- Structured columns for simple values (theme, keywords, search settings)
- JSONB only for complex nested structures (journal_scoring, keyword_scoring)
- Foreign key relationship to `auth.users(id)`
- Automatic creation via database trigger on user signup
- GIN indexes for array-based searches

## When to Delete These Scripts

**Safe to delete when:**
- All production users have migrated to `user_preferences` table
- No `user_profiles.preferences` JSONB data exists in production
- You're confident you won't need to reference the migration logic

**Verify with:**
```sql
-- Check if any users still have JSONB preferences
SELECT COUNT(*) FROM user_profiles WHERE preferences IS NOT NULL;

-- Should return 0 if all migrated
```

## Notes

- These scripts are preserved for documentation and potential edge cases
- New users automatically get preferences via the database trigger
- No manual migration should be needed for new installations
